"""Read the installed package directly from disk for version + docs (Verify-A's source of truth).

Searches both project-local installs (cwd/node_modules, cwd site-packages) and global
installs (`npm root -g`, the Python site-packages), so globally-installed CLIs/tools
(e.g. a global npm package) are read version-exact instead of falling back to web search.
"""

import glob
import json
import os
import subprocess
import sysconfig
from pathlib import Path


def _read_node_pkg(pkg_dir: Path, tech: str) -> dict | None:
    pj = pkg_dir / "package.json"
    if not pj.exists():
        return None
    try:
        version = json.loads(pj.read_text()).get("version", "")
    except Exception:
        version = ""
    docs = ""
    for readme in ("README.md", "readme.md"):
        rp = pkg_dir / readme
        if rp.exists():
            docs = rp.read_text()
            break
    return {"name": tech, "version": version, "docs": docs}


def read_installed_package(tech: str, search_paths: list[str | Path]) -> dict | None:
    if not tech:
        return None
    for base in search_paths:
        base = Path(base)

        # Node — both cwd/node_modules/<tech> and <base>/<tech> (npm root -g layout)
        for pkg_dir in (base / "node_modules" / tech, base / tech):
            result = _read_node_pkg(pkg_dir, tech)
            if result is not None:
                return result

        # Python — site-packages/<tech>-<ver>.dist-info/METADATA
        for dist in base.glob(f"{tech}-*.dist-info"):
            meta = dist / "METADATA"
            if not meta.exists():
                continue
            text = meta.read_text()
            version = ""
            for line in text.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    break
            return {"name": tech, "version": version, "docs": text}

    return None


# Extra bin dirs to help *locate the npm binary* when a daemon launched by launchd/systemd
# runs with a stripped PATH. We don't hardcode package locations — we just make `npm` findable
# so it can report ITS OWN global root (correct for any machine: brew, nvm, custom prefix, Linux).
_EXTRA_BIN = (
    "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin",
    str(Path.home() / ".npm-global/bin"), str(Path.home() / ".local/bin"),
)

# Last-resort global node_modules roots, only if `npm` can't be run at all. Standard
# cross-distro locations (not specific to one machine).
_FALLBACK_NODE_ROOTS = (
    "/usr/local/lib/node_modules", "/usr/lib/node_modules", "/opt/homebrew/lib/node_modules",
    str(Path.home() / ".npm-global/lib/node_modules"),
)


def _env_with_path() -> dict:
    env = dict(os.environ)
    extra = os.pathsep.join(_EXTRA_BIN)
    env["PATH"] = (env.get("PATH", "") + os.pathsep + extra).strip(os.pathsep)
    return env


def _npm_global_root() -> str | None:
    try:
        r = subprocess.run(
            ["npm", "root", "-g"], capture_output=True, text=True, timeout=8, env=_env_with_path()
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def default_search_paths(cwd: str | Path) -> list[str]:
    """Resolve where packages actually live — machine-agnostic.

    Order: project cwd · project virtualenv site-packages · npm's own global root
    (asked dynamically) · fallback global node roots · the daemon's Python env.
    """
    cwd = Path(cwd)
    paths: list[str] = [str(cwd)]

    # project-local Python virtualenv (any interpreter version)
    for pattern in (".venv/lib/python*/site-packages", "venv/lib/python*/site-packages"):
        paths.extend(glob.glob(str(cwd / pattern)))

    # ask npm where ITS global root is — correct on any setup (brew/nvm/custom prefix/Linux)
    root = _npm_global_root()
    if root:
        paths.append(root)

    # only if npm couldn't be run at all
    if root is None:
        for fallback in _FALLBACK_NODE_ROOTS:
            if Path(fallback).is_dir():
                paths.append(fallback)

    # globally pip-installed into this interpreter
    try:
        paths.append(sysconfig.get_paths()["purelib"])
    except Exception:
        pass

    # dedupe, preserve order
    seen: set[str] = set()
    return [p for p in paths if not (p in seen or seen.add(p))]
