# swap_reader.py
import select, traceback, time
from typing import Optional, Tuple, Dict, Any

from struct_parser import (
    open_region, open_netlink, nl_get_payload_pid,
    read_region, find_pid_window, feat_to_row
)

class SwapDeviceReader:
    """Wraps /dev/swap_ai + netlink to yield (pid, row) events."""

    def __init__(self):
        try:
            self.fd, self.mm = open_region()
            self.nl = open_netlink()
            self.enable = True

        except Exception as e:
            self.enable = False
            self.fd, self.mm = None, None
            raise RuntimeError(f"Unexpected error during region open: {e}")

    def next_event(self, timeout_sec: float = 1.0) -> Optional[Tuple[int, Dict[str, Any]]]:
        """Return (pid, row) or None on timeout."""
        rlist, _, _ = select.select([self.nl], [], [], timeout_sec)
        if self.nl not in rlist:
            return None
        
        try:
            dat = self.nl.recv(4096)
            pid = nl_get_payload_pid(dat)
            if pid is None:
                if len(dat) >= 4:
                    pid = int.from_bytes(dat[-4:], "little")
                else:
                    return None

            windows = read_region(self.mm)
            w = find_pid_window(windows, pid)
            if not w or w["count"] == 0:
                return None

            # pick the newest feature from this PID window
            idx = max(0, w["count"] - 1)
            feat = w["feats"][idx]
            row = feat_to_row(pid, feat)
            return pid, row
        
        except Exception:
            traceback.print_exc()
            time.sleep(0.01)
            return None

    def close(self):
        try:
            self.mm.close()
        except Exception:
            pass
        try:
            self.nl.close()
        except Exception:
            pass
