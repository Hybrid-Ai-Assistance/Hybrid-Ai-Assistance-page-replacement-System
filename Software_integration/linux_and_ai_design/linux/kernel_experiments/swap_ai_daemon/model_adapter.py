# model_adapter.py — wraps your Keras V3 model to output FUTURE horizon via autoregressive rollout
from typing import Dict, Any, Optional
import numpy as np
from utils import reconstruct_pfn
from config import SEQ_LEN, FUTURE

class V3PredictorAdapter:
    def __init__(self, keras_model):
        self.model = keras_model

    def _predict_one(self, X_seq: np.ndarray, aux: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        # model outputs: [top_out, s4_out, s3_out, s2_out, s1_out, s0_out]
        preds = self.model.predict(
            {"seq_input": X_seq,
             "pid_in":   aux["pid_in"],
             "folio_in": aux["folio_in"],
             "map_in":   aux["map_in"],
             "latc_in":  aux["latc_in"]},
            batch_size=1, verbose=0
        )
        return {
            "top": np.argmax(preds[0], axis=1).astype(int),
            "s4":  np.argmax(preds[1], axis=1).astype(int),
            "s3":  np.argmax(preds[2], axis=1).astype(int),
            "s2":  np.argmax(preds[3], axis=1).astype(int),
            "s1":  np.argmax(preds[4], axis=1).astype(int),
            "s0":  np.argmax(preds[5], axis=1).astype(int),
        }

    def predict_horizon(self, X_seq: np.ndarray, aux: Dict[str, np.ndarray], future:int=FUTURE) -> Dict[str, np.ndarray]:
        seq = X_seq.copy()  # (1,SEQ_LEN,8)
        tops, s4s, s3s, s2s, s1s, s0s, pfns = [], [], [], [], [], [], []
        for _ in range(future):
            out = self._predict_one(seq, aux)
            t,a4,a3,a2,a1,a0 = [int(out[k][0]) for k in ["top","s4","s3","s2","s1","s0"]]
            tops.append(t); s4s.append(a4); s3s.append(a3); s2s.append(a2); s1s.append(a1); s0s.append(a0)
            pfns.append(reconstruct_pfn(t,a4,a3,a2,a1,a0))
            # feedback predicted step into sequence tail (no VA for predictions)
            pred_vec = np.array([[[0,0,t,a4,a3,a2,a1,a0]]], dtype=np.int32)  # (1,1,8)
            seq = np.concatenate([seq[:,1:,:], pred_vec], axis=1)

        return {
            "future": future,
            "pred_top": np.array(tops, dtype=int),
            "pred_s4":  np.array(s4s, dtype=int),
            "pred_s3":  np.array(s3s, dtype=int),
            "pred_s2":  np.array(s2s, dtype=int),
            "pred_s1":  np.array(s1s, dtype=int),
            "pred_s0":  np.array(s0s, dtype=int),
            "pred_pfn": np.array(pfns, dtype=np.int64),
        }
