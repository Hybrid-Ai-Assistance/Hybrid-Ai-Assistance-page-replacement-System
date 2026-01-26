# config.py — central knobs
MODEL_PATH = "./models/gru_slices_v3_best.keras"
DEV_PATH = "/dev/swap_ai"
NETLINK_PROTOCOL = 2          # NETLINK_USERSOCK
MAX_PROCS = 15                # shared region slots

# Model + sequence
SEQ_LEN = 30
FUTURE = 5
TRIGGER_EVERY = 3             # run model every N faults / PID
MIN_GAP_NS = 300_000          # 0.3 ms to suppress micro-batch triggers
HALF_READY_RATIO = 0.5        # 50% inputs must be filled before predicting

# Feature columns (match your V3)
INPUT_COLS_T = [
    "Va_L2","Va_L1",
    "PFN_Top_region","PFN_slice_4","PFN_slice_3","PFN_slice_2","PFN_slice_1","PFN_slice_0"
]
EXTRA_COLS = ["PID","folio_index","mapping","lat_cluster","start_ns"]
QUEUE_SIZE = SEQ_LEN + FUTURE

# Shared region (structs must match kernel)
# struct swap_feat { u64 va,pfn,mapping,start_ns,latency_ns; u32 folio_index; u32 reserved; }
FEAT_FMT = "<QQQQQI I"      # little endian
# struct swap_window { u32 pid,u32 count,char comm[16], feats[SEQ_LEN] }
WIN_HDR_FMT = "<II16s"
# region header { u32 nslots,u32 seq_len }
REG_HDR_FMT = "<II"
REG_SIZE = 24576  # 1 page region

# Logging
LOG_EVERY_FAULTS = 50        # print status every N faults (per PID)
