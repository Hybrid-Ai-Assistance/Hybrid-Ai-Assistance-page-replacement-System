
# ==============================================================
#  swap_predictor.py
#  Generate fixed-length future swap/page fault sequences
#  Author: Shubham
#  Fix: Handles 'mse' load error & returns denormalized predictions
# ==============================================================

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import os

class SwapFaultPredictor:
    def __init__(self, model_path="swap_lstm_model.h5", scaler_ref="swap_log.csv", seq_len=10, feature_dim=5):
        """
        Initialize LSTM predictor for swap fault prediction.
        :param model_path: Path to trained model (.h5 or .keras)
        :param scaler_ref: CSV used during training for feature scaling
        :param seq_len: Sequence length used during training
        :param feature_dim: Number of features per timestep
        """
        self.seq_len = seq_len
        self.feature_dim = feature_dim
        self.model_path = model_path

        # --- Fix for "Could not locate function 'mse'" ---
        custom_objects = {"mse": tf.keras.losses.MeanSquaredError()}

        print(f"🔄 Loading model from: {model_path}")
        self.model = load_model(model_path, custom_objects=custom_objects, compile=False)
        print("✅ Model loaded successfully")

        # Load scaler reference (for denormalization)
        if os.path.exists(scaler_ref):
            self.scaler = self._fit_scaler_from_csv(scaler_ref)
            print(f"📊 Scaler initialized from: {scaler_ref}")
        else:
            self.scaler = None
            print("⚠️ Warning: Scaler reference CSV not found — raw normalized output only.")

    def _fit_scaler_from_csv(self, csv_path):
        """Recreate MinMaxScaler from original training CSV."""
        df = pd.read_csv(csv_path)

        # Convert hex → int where applicable
        def hex_to_int(x):
            try:
                if isinstance(x, str) and x.startswith("0x"):
                    return int(x, 16)
                else:
                    return int(x)
            except:
                return 0

        df["VA"] = df["VA"].apply(hex_to_int)
        df["PFN"] = df["PFN"].apply(hex_to_int)
        df["mapping"] = df["mapping"].apply(hex_to_int)

        scaler = MinMaxScaler()
        scaler.fit(df[["VA", "PFN", "folio_index", "mapping", "latency_ns"]])
        return scaler

    def predict_future_sequence(self, input_seq, steps=10, denormalize=True):
        """
        Predict next N swap/page fault vectors using trained LSTM model.
        :param input_seq: numpy array of shape (seq_len, feature_dim)
        :param steps: number of future steps to generate
        :param denormalize: if True, convert back to original scale
        :return: numpy array of shape (steps, feature_dim)
        """
        if input_seq.shape != (self.seq_len, self.feature_dim):
            raise ValueError(f"Input must have shape ({self.seq_len}, {self.feature_dim})")

        seq = input_seq[np.newaxis, :, :]  # reshape for LSTM input
        preds = []

        for _ in range(steps):
            next_pred = self.model.predict(seq, verbose=0)
            preds.append(next_pred[0])
            seq = np.concatenate([seq[:, 1:, :], next_pred.reshape(1, 1, -1)], axis=1)

        preds = np.array(preds)

        if denormalize and self.scaler:
            preds = self.scaler.inverse_transform(preds)

        return preds