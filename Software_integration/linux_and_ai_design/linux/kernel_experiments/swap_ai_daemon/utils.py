# utils.py — helpers: PFN/VA slicing, zero rows, small utils
from typing import Dict, Any
from config import INPUT_COLS_T, EXTRA_COLS

def reconstruct_pfn(top, s4, s3, s2, s1, s0) -> int:
    # Your earlier convention (top=1 bit, slices=4 bits each)
    return ((int(top) << 20) |
            (int(s4)  << 16) |
            (int(s3)  << 12) |
            (int(s2)  << 8)  |
            (int(s1)  << 4)  |
            (int(s0)))

def pfn_to_slices(pfn: int):
    top = (pfn >> 20) & 0x1
    s4  = (pfn >> 16) & 0xF
    s3  = (pfn >> 12) & 0xF
    s2  = (pfn >> 8)  & 0xF
    s1  = (pfn >> 4)  & 0xF
    s0  = (pfn >> 0)  & 0xF
    return top, s4, s3, s2, s1, s0

def va_to_L1L2(va: int):
    # From your persisted decision: L1 = (VA>>12)&0x1FF, L2 = (VA>>21)&0x1FF
    l1 = (va >> 12) & 0x1FF
    l2 = (va >> 21) & 0x1FF
    return l2, l1  # order: Va_L2, Va_L1

def latency_to_cluster(lat_ns: int) -> int:
    # simple buckets: <100us=0, <1ms=1, <10ms=2, else 3
    if lat_ns < 100_000: return 0
    if lat_ns < 1_000_000: return 1
    if lat_ns < 10_000_000: return 2
    return 3

def empty_entry(pid: int = 0) -> Dict[str, Any]:
    row = {
        'Va_L2':0,'Va_L1':0,
        'PFN_Top_region':0,'PFN_slice_4':0,'PFN_slice_3':0,'PFN_slice_2':0,'PFN_slice_1':0,'PFN_slice_0':0,
        'PID':pid,'folio_index':0,'mapping':0,'lat_cluster':0,'start_ns':0,
        'PFN':0
    }
    return row

def ensure_row_defaults(row: Dict[str, Any], pid: int) -> Dict[str, Any]:
    # Ensure all required keys exist
    base = empty_entry(pid)
    base.update(row or {})
    if 'PFN' not in base or base['PFN'] == 0:
        base['PFN'] = reconstruct_pfn(
            base['PFN_Top_region'], base['PFN_slice_4'], base['PFN_slice_3'],
            base['PFN_slice_2'], base['PFN_slice_1'], base['PFN_slice_0']
        )
    return base
