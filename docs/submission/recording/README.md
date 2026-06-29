# Recording the demo video (Linux headless box)

Produces a clean ~60–90s terminal demo MP4 of the real qmem loop — no GUI, no live
screen capture. Based on the `headless-screencast` method (Xvfb + xterm + ffmpeg).
(This Mac lacks X11, so run this on a Linux box.)

## Prereqs (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y xvfb xterm ffmpeg fonts-dejavu
# qmem + deps
git clone https://github.com/Mrbaeksang/qwen-memory-agent ~/qwen-memory-agent
cd ~/qwen-memory-agent && uv sync          # .venv gets pydantic (read by Verify-A)
uv tool install qwen-memory-agent          # provides the `qmem` command
mkdir -p ~/.qmem && echo "QWEN_API_KEY=sk-..." > ~/.qmem/.env
qmem install                               # starts daemon on :8787 (systemd/manual on Linux)
# if launchd-style autostart isn't available on your box, just run the daemon:
#   nohup qmem daemon >~/.qmem/daemon.log 2>&1 &
```

> Note: `qmem install` wires launchd (macOS). On Linux, start the daemon with
> `nohup qmem daemon &` (or a systemd --user unit). The hooks/adapter still work via `qmem hook`.

## Record

```bash
cd ~/qwen-memory-agent/docs/submission/recording
REPO=~/qwen-memory-agent setsid bash orch.sh &
tail -f orch.log          # watch; final.mp4 appears when done
```

Output: `final.mp4` (1280x720). Re-run if a take is poor (Qwen latency/jitter) — keep the best.

## Upload

Upload `final.mp4` to YouTube (Unlisted or Public), paste the link into the Devpost
"Video demo link" field. Keep it under 3 minutes.

## Files
- `inner.sh` — the visible demo choreography (typed commands + real runs).
- `orch.sh` — Xvfb/xterm/ffmpeg orchestrator (detached); writes `final.mp4`.
