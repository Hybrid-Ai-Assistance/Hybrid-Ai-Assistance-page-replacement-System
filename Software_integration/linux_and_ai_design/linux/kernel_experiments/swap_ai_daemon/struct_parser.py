# struct_parser.py — mmap shared-region + netlink helpers + row conversion
import os, mmap, struct, socket
from typing import Dict, Any, List, Tuple, Optional
from config import (
    DEV_PATH, REG_SIZE, FEAT_FMT, WIN_HDR_FMT, REG_HDR_FMT,
    MAX_PROCS, SEQ_LEN, NETLINK_PROTOCOL
)
from utils import pfn_to_slices, va_to_L1L2, latency_to_cluster

FEAT_SIZE = struct.calcsize(FEAT_FMT)
WIN_HDR_SIZE = struct.calcsize(WIN_HDR_FMT)
REG_HDR_SIZE = struct.calcsize(REG_HDR_FMT)
WIN_SIZE = WIN_HDR_SIZE + SEQ_LEN * FEAT_SIZE

# --- mmap/open
def open_region():
    """
    Safely open & mmap /dev/swap_ai.
    - No spam print
    - Raises precise exceptions for caller
    - Caller decides fallback (model-only mode)
    """
    if not os.path.exists(DEV_PATH):
        raise FileNotFoundError(f"{DEV_PATH} does not exist (kernel module not loaded)")
   
    try:
        fd = os.open(DEV_PATH, os.O_RDONLY)
    except PermissionError:
        raise PermissionError(f"Permission denied while opening {DEV_PATH}")
    except Exception as e:
        raise RuntimeError(f"Failed to open {DEV_PATH}: {e}")

    try:
        mm = mmap.mmap(fd, REG_SIZE, access=mmap.ACCESS_READ)
    except Exception as e:
        os.close(fd)
        raise RuntimeError(f"mmap failed on {DEV_PATH}: {e}")
        
    
    return fd, mm

# --- netlink
def open_netlink():
    nl = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_PROTOCOL)
    nl.bind((os.getpid(), 0))
    nl.send(b"HELLO")
    return nl

NLMSG_HDR_FMT = "<IHHII"   # len,type,flags,seq,pid
NLMSG_HDR_SIZE = struct.calcsize(NLMSG_HDR_FMT)

def nl_get_payload_pid(dat: bytes) -> Optional[int]:
    if len(dat) < NLMSG_HDR_SIZE + 4:
        return None
    _,_,_,_,_ = struct.unpack_from(NLMSG_HDR_FMT, dat, 0)
    payload_off = NLMSG_HDR_SIZE
    if payload_off + 4 <= len(dat):
        (pid_payload,) = struct.unpack_from("<I", dat, payload_off)
        return pid_payload
    return None

# --- region reading
def read_region(mm):
    """Reads the entire mmap region using dynamic nslots + seqlen."""
    # --- 1) Read region header ---
    # REG_HDR_FMT = "<II" → (nslots, seqlen)
    nslots, seqlen = struct.unpack_from(REG_HDR_FMT, mm, 0)

    # Compute dynamic WIN_SIZE
    # WIN_HDR_SIZE = sizeof(pid,count,comm)
    # FEAT_SIZE    = sizeof(one sequence entry)
    win_size = WIN_HDR_SIZE + seqlen * FEAT_SIZE

    windows = []
    base = REG_HDR_SIZE

    # --- 2) Iterate only over actual kernel slots (dynamic) ---
    for slot_idx in range(nslots):
        off = base + slot_idx * win_size

        # --- 3) Per-window header ---
        pid, count, comm = struct.unpack_from(WIN_HDR_FMT, mm, off)

        # Decode comm safely
        comm = comm.split(b"\x00", 1)[0].decode(errors="ignore")

        feats = []
        feat_off = off + WIN_HDR_SIZE

        # --- 4) Read dynamic SEQ entries ---
        for j in range(seqlen):
            va, pfn, mapping, start_ns, latency_ns, folio_idx, _ = \
                struct.unpack_from(FEAT_FMT, mm, feat_off + j * FEAT_SIZE)

            feats.append({
                "va": va,
                "pfn": pfn,
                "mapping": mapping,
                "start_ns": start_ns,
                "lat_ns": latency_ns,
                "folio": folio_idx,
            })

        # --- 5) Append parsed window ---
        windows.append({
            "pid": pid,
            "count": count,
            "comm": comm,
            "feats": feats,
        })

    return windows

def find_pid_window(windows, pid) -> Optional[Dict[str,Any]]:
    for w in windows:
        if w["pid"] == pid:
            return w
    return None

# --- convert one feat tuple → V3 row
def feat_to_row(pid:int, feat_tuple) -> Dict[str,Any]:
    va, pfn, mapping, start_ns, latency_ns, folio_idx = feat_tuple
    try:
        top,s4,s3,s2,s1,s0 = pfn_to_slices(int(pfn))
    except Exception as e:
        raise RuntimeWarning(f"{e} pfn = {int(pfn)}")
    va_l2, va_l1 = va_to_L1L2(int(va))
    return {
        'Va_L2': va_l2,
        'Va_L1': va_l1,
        'PFN_Top_region': top,
        'PFN_slice_4': s4,
        'PFN_slice_3': s3,
        'PFN_slice_2': s2,
        'PFN_slice_1': s1,
        'PFN_slice_0': s0,
        'PID': int(pid),
        'folio_index': int(folio_idx),
        'mapping': int(mapping),
        'lat_cluster': latency_to_cluster(int(latency_ns)),
        'start_ns': int(start_ns),
        # PFN will be reconstructed by queue if needed (not strictly required here)
    }
