"""qmem console CLI — `qmem <command>`.

  qmem install     wire hooks + start the launchd daemon (install)
  qmem uninstall   stop the daemon + restore the settings backup
  qmem status      daemon / memory / hooks status
  qmem daemon      run the daemon process (invoked by launchd)
  qmem hook        Claude Code hook adapter (invoked by hooks, stdin->stdout)
"""

import sys

USAGE = "usage: qmem {install|uninstall|status|daemon|hook}"


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "daemon":
        from qmem.__main__ import main as run_daemon

        run_daemon()
    elif cmd == "hook":
        from qmem.adapters.claude_code import main as run_hook

        run_hook()
    elif cmd == "install":
        from qmem.setup_hooks import install

        install()
    elif cmd == "uninstall":
        from qmem.setup_hooks import uninstall

        uninstall()
    elif cmd == "status":
        from qmem.setup_hooks import status

        status()
    else:
        print(USAGE)
        sys.exit(0 if cmd in ("help", "-h", "--help") else 2)


if __name__ == "__main__":
    main()
