#!/usr/bin/env python3
import time
import numpy as np
from collections import defaultdict, deque
from hashlib import blake2b

# ----------------------------------------------------
# Load trained AI model
# ----------------------------------------------------
try:
    from swap_predictor import SwapFaultPredictor
    predictor = SwapFaultPredictor("swap_lstm_model_fixed.keras", "swap_log.csv")
    PRED_AVAILABLE = True
    print("✅ AI model loaded for live predictions.")
except Exception as e:
    print("⚠️ Predictor unavailable, using dummy mode:", e)
    predictor = None
    PRED_AVAILABLE = False

PROC_FILE = "/proc/swap_entry"
SEQ_LEN = 10
FEATURE_DIM = 5     # [VA, PFN, folio_index, mapping, latency_ns]
PRED_STEPS = 20     # how many future faults to predict
GLOBAL_QUEUE_LEN = 50

# ----------------------------------------------------
# Process-wise sequence store (LIFO-style)
# ----------------------------------------------------
class ProcessSeqStore:
    def __init__(self, seq_len=10, feature_dim=5):
        self.seq_len = seq_len
        self.feature_dim = feature_dim
        self.store = defaultdict(lambda: np.zeros((seq_len, feature_dim), dtype=np.float64))

    def update(self, pid, new_entry):
        seq = self.store[pid]
        seq = np.vstack([seq, new_entry[np.newaxis, :]])
        if seq.shape[0] > self.seq_len:
            seq = seq[-self.seq_len:, :]
        elif seq.shape[0] < self.seq_len:
            pad = np.zeros((self.seq_len - seq.shape[0], self.feature_dim))
            seq = np.vstack([pad, seq])
        self.store[pid] = seq

    def get(self, pid):
        return self.store[pid]

# ----------------------------------------------------
# Helper functions
# ----------------------------------------------------
def hex_to_int(x):
    try:
        if isinstance(x, str) and x.startswith(("0x", "0X")):
            return int(x, 16)
        return int(x)
    except:
        return 0

def parse_line(line):
    """Parse line: PID,COMM,VA,PFN,mapping,folio_index,start_ns,latency_ns"""
    parts = line.strip().split(",")
    if len(parts) < 8:
        return None
    try:
        pid = int(parts[0])
        va = hex_to_int(parts[2])
        pfn = hex_to_int(parts[3])
        mapping = hex_to_int(parts[4])
        folio_idx = int(parts[5])
        latency = int(parts[7])
        vec = np.array([va, pfn, folio_idx, mapping, latency], dtype=np.float64)
        return pid, vec
    except:
        return None

# ----------------------------------------------------
# Main loop
# ----------------------------------------------------
def main():
    seq_store = ProcessSeqStore(seq_len=SEQ_LEN, feature_dim=FEATURE_DIM)
    prediction_queue = deque(maxlen=GLOBAL_QUEUE_LEN)
    seen_hashes = deque(maxlen=8000)

    print(f"📡 Real-time monitoring started on {PROC_FILE}")

    while True:
        try:
            with open(PROC_FILE, "r") as f:
                lines = f.readlines()
        except Exception as e:
            print("⚠️ Error reading /proc:", e)
            time.sleep(1)
            continue

        for line in lines:
            if not line or line.startswith("#") or "PID" in line:
                continue

            parsed = parse_line(line)
            if not parsed:
                continue
            pid, vec = parsed

            # hash-based deduplication
            h = blake2b(f"{pid}-{vec[0]}-{vec[1]}-{vec[4]}".encode(), digest_size=8).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.append(h)

            # update per-process sequence
            seq_store.update(pid, vec)
            seq = seq_store.get(pid)
            print(f"[PID={pid}] New Fault → PFN={int(vec[1])}, Lat={vec[4]/1e6:.3f} ms")

            # ---- Trigger AI prediction ----
            if PRED_AVAILABLE and np.count_nonzero(seq) > 0:
                future = predictor.predict_future_sequence(seq, steps=PRED_STEPS, denormalize=True)
                prediction_queue.append((pid, future))

                print(f"🔮 Predicted next {PRED_STEPS} PFNs for PID {pid}:")
                print("   ", future[:, 1].astype(np.int64))
                print(f"   Latency trend (ms): {np.round(future[:, 4] / 1e6, 3)}")

        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully...")

