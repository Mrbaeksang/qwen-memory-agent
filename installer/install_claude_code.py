"""Claude Code(Tier 1) 설치기 — 훅 와이어링 + 데몬 launchd plist 생성.

- ~/.claude/settings.json 을 백업 후 가산 병합(기존 훅 보존).
- ~/Library/LaunchAgents/com.qmem.daemon.plist 생성(영속 데몬).
실행: `uv run python installer/install_claude_code.py`
"""

import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
ADAPTER_CMD = f'"{VENV_PYTHON}" -m qmem.adapters.claude_code'
HOOK_EVENTS = ["SessionStart", "UserPromptSubmit", "PreCompact", "SessionEnd"]

SETTINGS = Path.home() / ".claude" / "settings.json"
PLIST = Path.home() / "Library" / "LaunchAgents" / "com.qmem.daemon.plist"
LOG_DIR = Path.home() / ".qmem"


def wire_hooks() -> None:
    settings: dict = {}
    if SETTINGS.exists():
        shutil.copy(SETTINGS, SETTINGS.with_name("settings.json.qmem-bak"))
        settings = json.loads(SETTINGS.read_text() or "{}")

    hooks = settings.setdefault("hooks", {})
    for event in HOOK_EVENTS:
        groups = hooks.setdefault(event, [])
        if any("qmem.adapters" in json.dumps(g) for g in groups):
            continue  # 이미 설치됨
        groups.append({"hooks": [{"type": "command", "command": ADAPTER_CMD}]})

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2))
    print(f"[hooks] wired {HOOK_EVENTS} -> {ADAPTER_CMD}")
    print(f"[hooks] backup: {SETTINGS.with_name('settings.json.qmem-bak')}")


def write_plist() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.qmem.daemon</string>
  <key>ProgramArguments</key>
  <array>
    <string>{VENV_PYTHON}</string>
    <string>-m</string>
    <string>qmem</string>
  </array>
  <key>WorkingDirectory</key><string>{PROJECT_ROOT}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{LOG_DIR / 'daemon.log'}</string>
  <key>StandardErrorPath</key><string>{LOG_DIR / 'daemon.log'}</string>
</dict>
</plist>
"""
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    PLIST.write_text(plist)
    print(f"[daemon] plist: {PLIST}")
    print(f"[daemon] load: launchctl unload {PLIST} 2>/dev/null; launchctl load {PLIST}")


if __name__ == "__main__":
    wire_hooks()
    write_plist()
    print("\n설치 완료. 데몬을 launchctl로 로드하면 모든 Claude Code 세션에서 메모리가 동작합니다.")
