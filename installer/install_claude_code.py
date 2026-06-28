"""(backward-compat shim) — install logic now lives in `qmem install` (qmem.setup_hooks)."""

from qmem.setup_hooks import install

if __name__ == "__main__":
    install()
