#!/usr/bin/env bash
# Headless recorder (Linux/X11) — Xvfb + xterm + ffmpeg x11grab → final.mp4.
# Per the headless-screencast skill: never touches the real desktop.
# Run detached:  REPO=~/qwen-memory-agent setsid bash orch.sh & ; tail -f orch.log
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${REPO:-$HOME/qwen-memory-agent}"
SENTINEL=/tmp/qmem_demo.done
W=1280; H=720
: > "$DIR/orch.log"; exec >>"$DIR/orch.log" 2>&1
rm -f "$SENTINEL"

echo "[orch] starting Xvfb"
Xvfb :99 -screen 0 ${W}x${H}x24 -ac &
XVFB=$!; sleep 1.5

echo "[orch] launching xterm + inner.sh"
DISPLAY=:99 xterm -geometry 160x44+0+0 -fa 'DejaVu Sans Mono' -fs 12 -bg black -fg white \
  -e bash -lc "SENTINEL=$SENTINEL REPO='$REPO' PORT=8787 bash '$DIR/inner.sh'; sleep 3" &
sleep 1.5

echo "[orch] recording"
ffmpeg -y -f x11grab -framerate 15 -video_size ${W}x${H} -i :99 \
  -c:v libx264 -pix_fmt yuv420p "$DIR/out_raw.mp4" &
FF=$!

for _ in $(seq 1 180); do [ -f "$SENTINEL" ] && break; sleep 2; done   # max ~6 min
sleep 2
kill -INT $FF 2>/dev/null; wait $FF 2>/dev/null
kill $XVFB 2>/dev/null

echo "[orch] post-processing"
ffmpeg -y -i "$DIR/out_raw.mp4" -vf "fade=in:0:0.6" -crf 22 -movflags +faststart "$DIR/final.mp4"
echo "[orch] DONE -> $DIR/final.mp4"
