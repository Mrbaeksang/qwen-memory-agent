"""qmem 콘솔 CLI — `qmem <command>`.

  qmem install     훅 와이어링 + launchd 데몬 기동 (설치)
  qmem uninstall   데몬 중지 + 설정 백업 복원
  qmem status      데몬/메모리/훅 상태
  qmem daemon      데몬 프로세스 실행 (launchd가 호출)
  qmem hook        Claude Code 훅 어댑터 (훅이 호출, stdin→stdout)
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
