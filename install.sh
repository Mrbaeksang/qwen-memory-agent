#!/usr/bin/env bash
# qmem 원스크립트 설치 — 의존성 + 훅 와이어링 + 데몬 기동/재기동까지 한 번에.
# 사용: ./install.sh   (레포 루트에서 실행)
set -euo pipefail
cd "$(dirname "$0")"

LABEL="com.qmem.daemon"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

echo "==> [1/3] 의존성 설치 (uv sync)"
uv sync

echo "==> [2/3] Claude Code 훅 와이어링 + launchd plist"
uv run python installer/install_claude_code.py

echo "==> [3/3] 데몬 기동/재기동"
if launchctl list | grep -q "$LABEL"; then
  launchctl kickstart -k "gui/$(id -u)/$LABEL"
  echo "    (이미 로드됨 → 재기동)"
else
  launchctl load "$PLIST"
  echo "    (신규 로드)"
fi

sleep 2
CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8787/lessons || echo 000)
echo ""
if [ "$CODE" = "200" ]; then
  echo "✅ 설치 완료 — 데몬 http://127.0.0.1:8787 (HTTP $CODE)"
  echo "   루트 메모리: ~/.qmem/mem.db | 로그: ~/.qmem/daemon.log"
  echo "   이제 모든 Claude Code 세션에서 메모리가 자동 동작합니다."
else
  echo "⚠️  데몬 응답 없음 (HTTP $CODE) — ~/.qmem/daemon.log 확인"
  exit 1
fi
