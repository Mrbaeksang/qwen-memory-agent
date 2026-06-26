#!/usr/bin/env bash
# qmem 제거 — 데몬 중지 + plist 삭제 + ~/.claude/settings.json 백업 복원.
# 메모리(~/.qmem)는 보존. 완전 삭제하려면: rm -rf ~/.qmem
set -uo pipefail

LABEL="com.qmem.daemon"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
BAK="$HOME/.claude/settings.json.qmem-bak"

launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "데몬 중지 + plist 삭제"

if [ -f "$BAK" ]; then
  cp "$BAK" "$HOME/.claude/settings.json"
  echo "settings.json 백업 복원: $BAK"
else
  echo "백업 없음 — ~/.claude/settings.json 의 qmem 훅을 수동 제거하세요"
fi

echo "✅ 제거 완료 (메모리 ~/.qmem 는 보존됨)"
