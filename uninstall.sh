#!/usr/bin/env bash
# qmem uninstall — stop the daemon, remove the plist, restore the settings.json backup.
# Memory (~/.qmem) is kept. To wipe it entirely: rm -rf ~/.qmem
set -uo pipefail

LABEL="com.qmem.daemon"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
BAK="$HOME/.claude/settings.json.qmem-bak"

launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "daemon stopped + plist removed"

if [ -f "$BAK" ]; then
  cp "$BAK" "$HOME/.claude/settings.json"
  echo "settings.json restored from backup: $BAK"
else
  echo "no backup found — remove the qmem hooks from ~/.claude/settings.json manually"
fi

echo "uninstalled (memory ~/.qmem kept)"
