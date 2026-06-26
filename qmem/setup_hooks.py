"""설치/제거 로직 — Claude Code 훅 와이어링 + launchd 데몬 (qmem install/uninstall/status).

PyPI 설치(`uv tool install qwen-memory-agent`)든 레포(`uv run qmem install`)든,
PATH의 `qmem` 실행파일 절대경로를 찾아 훅·데몬이 그걸 가리키게 한다.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from qmem.config import QMEM_HOME, port

LABEL = "com.qmem.daemon"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_EVENTS = ["SessionStart", "UserPromptSubmit", "PreCompact", "SessionEnd"]


def _qmem_cmd() -> str:
    return str(Path(shutil.which("qmem") or sys.argv[0]).resolve())


def _ensure_env() -> None:
    QMEM_HOME.mkdir(parents=True, exist_ok=True)
    target = QMEM_HOME / ".env"
    if target.exists():
        return
    repo_env = Path(__file__).resolve().parent.parent / ".env"
    if repo_env.exists():
        target.write_text(repo_env.read_text())
    else:
        target.write_text(
            "QWEN_API_KEY=\n"
            "QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1\n"
            "QWEN_MODEL_INLINE=qwen-plus\n"
            "QWEN_MODEL_REVIEW=qwen-turbo\n"
        )
        print(f"  ! {target} 에 QWEN_API_KEY 를 채워주세요")


def _wire_hooks(cmd: str) -> None:
    settings: dict = {}
    if SETTINGS.exists():
        shutil.copy(SETTINGS, SETTINGS.with_name("settings.json.qmem-bak"))
        settings = json.loads(SETTINGS.read_text() or "{}")
    hooks = settings.setdefault("hooks", {})
    hook_cmd = f'"{cmd}" hook'
    for event in HOOK_EVENTS:
        # 기존 qmem 엔트리 제거 후 재추가(경로 변경/구버전 정리), 타 훅은 보존
        groups = [g for g in hooks.get(event, []) if "qmem" not in json.dumps(g)]
        groups.append({"hooks": [{"type": "command", "command": hook_cmd}]})
        hooks[event] = groups
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2))
    print(f"  hooks -> {hook_cmd}")


def _write_plist(cmd: str) -> None:
    QMEM_HOME.mkdir(parents=True, exist_ok=True)
    log = QMEM_HOME / "daemon.log"
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    PLIST.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>{cmd}</string><string>daemon</string></array>
  <key>WorkingDirectory</key><string>{QMEM_HOME}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""
    )
    print(f"  plist -> {PLIST}")


def _is_loaded() -> bool:
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    return LABEL in r.stdout


def _load_daemon() -> None:
    if _is_loaded():
        subprocess.run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{LABEL}"])
    else:
        subprocess.run(["launchctl", "load", str(PLIST)])


def _health() -> int | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port()}/lessons", timeout=3) as r:
            return r.status
    except Exception:
        return None


def install() -> None:
    print("==> qmem install")
    _ensure_env()
    cmd = _qmem_cmd()
    _wire_hooks(cmd)
    _write_plist(cmd)
    _load_daemon()
    time.sleep(2)
    code = _health()
    if code == 200:
        print(f"✅ 설치 완료 — daemon http://127.0.0.1:{port()} (HTTP {code})")
        print(f"   메모리: {QMEM_HOME / 'mem.db'} | 로그: {QMEM_HOME / 'daemon.log'}")
    else:
        print(f"⚠️  데몬 응답 없음 — {QMEM_HOME / 'daemon.log'} 확인")
        sys.exit(1)


def uninstall() -> None:
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    PLIST.unlink(missing_ok=True)
    bak = SETTINGS.with_name("settings.json.qmem-bak")
    if bak.exists():
        shutil.copy(bak, SETTINGS)
        print(f"settings.json 백업 복원: {bak}")
    print("✅ 제거 완료 (메모리 ~/.qmem 보존; 완전삭제: rm -rf ~/.qmem)")


def status() -> None:
    code = _health()
    print(f"daemon : {'UP (HTTP %d)' % code if code else 'DOWN'}")
    if code == 200:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port()}/lessons", timeout=3) as r:
                print(f"lessons: {len(json.load(r))}")
        except Exception:
            pass
    wired = []
    if SETTINGS.exists():
        hooks = json.loads(SETTINGS.read_text() or "{}").get("hooks", {})
        wired = [e for e in HOOK_EVENTS if any("qmem" in json.dumps(g) for g in hooks.get(e, []))]
    print(f"hooks  : {', '.join(wired) if wired else '(없음)'}")
