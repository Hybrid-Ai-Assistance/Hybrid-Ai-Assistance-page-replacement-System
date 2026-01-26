# queue_manager.py — per-PID sliding window, repair, threshold, micro-batch suppression, p/q merge
from collections import deque
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from config import (
    INPUT_COLS_T, EXTRA_COLS, SEQ_LEN, FUTURE, QUEUE_SIZE,
    TRIGGER_EVERY, MIN_GAP_NS, HALF_READY_RATIO
)
from utils import empty_entry, reconstruct_pfn, ensure_row_defaults

class PIDChainState:
    def __init__(self, pid:int, trigger_every:int=TRIGGER_EVERY, min_gap_ns:int=MIN_GAP_NS):
        self.pid = pid
        self.trigger_every = max(1, int(trigger_every))
        self.min_gap_ns = max(0, int(min_gap_ns))

        self.q = deque([empty_entry(pid) for _ in range(QUEUE_SIZE)], maxlen=QUEUE_SIZE)
        self.fault_count = 0
        self.last_fault_ns = 0
        self.micro_batch_active = False
        self.future_q: Optional[List[Dict[str,Any]]] = None

    # ---- helpers
    def _filled_inputs(self) -> int:
        past = list(self.q)[:SEQ_LEN]
        return sum(1 for r in past if int(r.get('PFN',0)) != 0)

    def _half_ready(self) -> bool:
        return self._filled_inputs() >= int(SEQ_LEN * HALF_READY_RATIO)

    def _left_slide(self):
        self.q.popleft()
        self.q.append(empty_entry(self.pid))

    def _expected_future0(self) -> Dict[str,Any]:
        return self.q[SEQ_LEN]

    def _write_tail(self, row: Dict[str,Any]):
        self.q[-1] = row

    def _set_future_chain(self, chain_rows: List[Dict[str,Any]]):
        for i in range(FUTURE):
            idx = SEQ_LEN + i
            self.q[idx] = chain_rows[i] if i < len(chain_rows) else empty_entry(self.pid)

    def _nearest_choice(self, c_pfn:int, p_head:int, q_head:Optional[int]) -> str:
        BIG = 1<<62
        dp = abs(c_pfn - p_head) if p_head is not None else BIG
        dq = abs(c_pfn - q_head) if q_head is not None else BIG
        if dp < dq: return 'p'
        if dq < dp: return 'q'
        return 'tie'

    def _last_seq_df(self) -> pd.DataFrame:
        rows = list(self.q)[:SEQ_LEN]
        df = pd.DataFrame(rows)
        for c in INPUT_COLS_T + EXTRA_COLS:
            if c not in df.columns: df[c] = 0
        return df[INPUT_COLS_T + EXTRA_COLS].fillna(0)

    # ---- main
    def ingest_fault(self, actual_row: Dict[str,Any], predictor) -> None:
        base = ensure_row_defaults(actual_row, self.pid)

        # time-gap → micro-batch detect
        now = int(base.get('start_ns', 0))
        gap = (now - self.last_fault_ns) if self.last_fault_ns else (1<<60)
        self.micro_batch_active = (gap < self.min_gap_ns)
        self.last_fault_ns = now

        # slide queue + repair
        expected = self._expected_future0()
        exp_pfn = int(expected.get('PFN', reconstruct_pfn(
            expected['PFN_Top_region'], expected['PFN_slice_4'], expected['PFN_slice_3'],
            expected['PFN_slice_2'], expected['PFN_slice_1'], expected['PFN_slice_0']
        )))
        act_pfn = int(base['PFN'])

        self._left_slide()
        if exp_pfn != act_pfn:
            self._write_tail(base)                  # reality injection
        else:
            tail = dict(self.q[-1]); tail['start_ns'] = base.get('start_ns', tail.get('start_ns', 0))
            tail['PID'] = self.pid
            self._write_tail(tail)

        self.fault_count += 1

        # gates
        if self.micro_batch_active: return
        if not self._half_ready():  return
        if predictor is None:       return
        if (self.fault_count % self.trigger_every) != 0: return

        # build inputs
        win = self._last_seq_df()
        X = win[['Va_L2','Va_L1','PFN_Top_region','PFN_slice_4','PFN_slice_3','PFN_slice_2','PFN_slice_1','PFN_slice_0']].astype('int32').to_numpy()[np.newaxis,:,:]
        aux = {
            'pid_in':   np.array([win.iloc[-1]['PID']], dtype=np.int32),
            'folio_in': np.array([win.iloc[-1]['folio_index']], dtype=np.int32),
            'map_in':   np.array([win.iloc[-1]['mapping']], dtype=np.int32),
            'latc_in':  np.array([win.iloc[-1]['lat_cluster']], dtype=np.int32),
        }

        pred = predictor.predict_horizon(X, aux, FUTURE)
        chain_p = []
        for t in range(pred["future"]):
            r = empty_entry(self.pid)
            r['PFN_Top_region'] = int(pred['pred_top'][t])
            r['PFN_slice_4']    = int(pred['pred_s4'][t])
            r['PFN_slice_3']    = int(pred['pred_s3'][t])
            r['PFN_slice_2']    = int(pred['pred_s2'][t])
            r['PFN_slice_1']    = int(pred['pred_s1'][t])
            r['PFN_slice_0']    = int(pred['pred_s0'][t])
            r['PFN'] = reconstruct_pfn(r['PFN_Top_region'], r['PFN_slice_4'], r['PFN_slice_3'],
                                       r['PFN_slice_2'], r['PFN_slice_1'], r['PFN_slice_0'])
            chain_p.append(r)

        p_head = chain_p[0]['PFN']
        q_head = int(self.q[SEQ_LEN]['PFN']) if isinstance(self.q[SEQ_LEN], dict) else None
        choice = self._nearest_choice(act_pfn, p_head, q_head)
        if choice in ('p','tie'):
            self._set_future_chain(chain_p)  # soft-merge (here K=FUTURE)
            self.future_q = chain_p[:]
        else:
            self.future_q = [self.q[SEQ_LEN+i] for i in range(FUTURE)]

class QueueManager:
    def __init__(self, trigger_every:int=TRIGGER_EVERY, min_gap_ns:int=MIN_GAP_NS):
        self.trigger_every = trigger_every
        self.min_gap_ns = min_gap_ns
        self.by_pid: Dict[int, PIDChainState] = {}

    def state(self, pid:int) -> PIDChainState:
        if pid not in self.by_pid:
            self.by_pid[pid] = PIDChainState(pid, self.trigger_every, self.min_gap_ns)
        return self.by_pid[pid]

    def ingest_fault(self, pid:int, actual_row:Dict[str,Any], predictor) -> None:
        self.state(pid).ingest_fault(actual_row, predictor)

    def snapshot(self, pid:int):
        st = self.state(pid)
        past = list(st.q)[:SEQ_LEN]
        fut  = list(st.q)[SEQ_LEN:]
        return past, fut
