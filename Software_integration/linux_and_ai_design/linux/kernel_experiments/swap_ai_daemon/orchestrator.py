# orchestrator.py
from typing import Optional, Dict, Any, List
import numpy as np
import tensorflow as tf
from tensorflow import keras
from config import FUTURE, TRIGGER_EVERY, MIN_GAP_NS, LOG_EVERY_FAULTS, MODEL_PATH
from queue_manager import QueueManager
from model_adapter import V3PredictorAdapter

class SliceLayer(keras.layers.Layer):
    def __init__(self, index, **kwargs):
        super().__init__(**kwargs)
        self.index = int(index)

    def call(self, x):
        return x[:, :, self.index:self.index+1]

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"index": self.index})
        return cfg

class KLConsistencyLayer(keras.layers.Layer):
    def __init__(self, weight=0.5, **kwargs):
        super().__init__(**kwargs)
        self.weight = float(weight)

    def call(self, inputs):
        # inputs: [top_probs, proj_probs]  — both (B, F, C)
        top_probs, proj_probs = inputs
        # Add KL penalty as a model loss so it’s saved with the graph
        kl = tf.keras.losses.KLDivergence()(proj_probs, top_probs)
        self.add_loss(self.weight * tf.reduce_mean(kl))
        return top_probs  # passthrough logits/probs

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"weight": self.weight})
        return cfg


class AIDaemonOrchestrator:
    def __init__(self, model_path: str = MODEL_PATH):
        # lazy import to keep startup fast if TF heavy
        self.model = tf.keras.models.load_model(
        model_path,
        custom_objects={"KLConsistencyLayer": KLConsistencyLayer,"SliceLayer": SliceLayer},
        safe_mode=False )
        
        self.predictor = V3PredictorAdapter(self.model)
        self.mgr = QueueManager(trigger_every=TRIGGER_EVERY, min_gap_ns=MIN_GAP_NS)
        self._event_ctr = 0

    def process(self, pid: int, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process one (pid,row) fault; returns brief status dict sometimes."""
        self.mgr.ingest_fault(pid, row, self.predictor)
        self._event_ctr += 1

        if (self._event_ctr % LOG_EVERY_FAULTS) == 0:
            past, fut = self.mgr.snapshot(pid)
            fut_pfns = [f.get("PFN", 0) for f in fut]
            return {
                "pid": pid,
                "events": self._event_ctr,
                "future_pfns": fut_pfns,
                "future_len": FUTURE,
            }
        return None
