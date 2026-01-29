# AI Swap Predictor Daemon (V3)

## What it does
- Reads kernel shared region `/dev/swap_ai` via `mmap`
- Listens to netlink events (kprobe trace batching safe)
- Maintains per-PID **sliding queue**: past=30 + future=5
- Half-ready gate (>=15 inputs) before any prediction
- Threshold trigger (every 3rd fault)
- Micro-batch suppression using `start_ns` time gap
- Autoregressive multi-horizon V3 predictions
- p/q nearest-head merge + **reality repair** (future[0] vs actual)

## Install
```bash
sudo mkdir -p /opt/swap_ai_daemon
sudo cp -r * /opt/swap_ai_daemon/
sudo systemctl daemon-reload
sudo cp /opt/swap_ai_daemon/swap_ai.service /etc/systemd/system/
sudo systemctl enable --now swap_ai
