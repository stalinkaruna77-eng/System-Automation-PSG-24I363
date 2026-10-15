"""
Requirement 2: Predictive Wear Detection Model
Course: 23IF02 System Automation — Bonus Challenge

Trains a supervised machine learning model (RandomForestClassifier) on historical joint
sensor data to detect premature joint wear before crossing safety thresholds.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

MODEL_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "joint_wear_model.pkl")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "joint_wear_history.csv")

FEATURE_COLUMNS = [
    "joint_shoulder", "joint_elbow", "joint_wrist",
    "torque_nm", "temperature_c", "vibration_mms",
    "operating_hours", "load_kg"
]

def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare feature matrix with explicit one-hot encoding for joints."""
    df_feat = pd.DataFrame(index=df.index)
    joint_col = df["joint"].str.lower()
    df_feat["joint_shoulder"] = (joint_col == "shoulder").astype(int)
    df_feat["joint_elbow"] = (joint_col == "elbow").astype(int)
    df_feat["joint_wrist"] = (joint_col == "wrist").astype(int)

    for col in ["torque_nm", "temperature_c", "vibration_mms", "operating_hours", "load_kg"]:
        df_feat[col] = df[col].astype(float)

    return df_feat[FEATURE_COLUMNS]

def train_predictive_model(data_path: str = DATA_FILE, model_path: str = MODEL_FILE) -> Dict[str, Any]:
    """Train RandomForest model on historical labeled joint failure dataset."""
    df = pd.read_csv(data_path)
    X = preprocess_features(df)
    y = df["state"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump({"model": clf, "feature_columns": FEATURE_COLUMNS}, model_path)

    return {
        "accuracy": acc,
        "classification_report": report,
        "model_path": model_path,
        "n_train": len(X_train),
        "n_test": len(X_test)
    }

class JointWearPredictor:
    """Predictive wear evaluation engine using the trained model artifact."""

    def __init__(self, model_path: str = MODEL_FILE):
        self.model_path = model_path
        self.artifact = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            # Auto-train if model artifact doesn't exist yet
            train_predictive_model(model_path=self.model_path)
        self.artifact = joblib.load(self.model_path)
        self.model: RandomForestClassifier = self.artifact["model"]

    def predict_joint(self, joint_name: str, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict wear state for a single joint.
        
        Returns:
            dict containing predicted_state, confidence, probabilities, wear_score (0.0 to 1.0)
        """
        row = {
            "joint": joint_name.lower(),
            "torque_nm": reading.get("torque_nm", 50.0),
            "temperature_c": reading.get("temperature_c", 45.0),
            "vibration_mms": reading.get("vibration_mms", 1.2),
            "operating_hours": reading.get("operating_hours", 2000),
            "load_kg": reading.get("load_kg", 3.0),
        }
        df_single = pd.DataFrame([row])
        X = preprocess_features(df_single)

        pred_state = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]
        classes = list(self.model.classes_)
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probs)}

        # Continuous wear score synthesis (0.0=pure Normal, 0.5=Warning, 1.0=Failure)
        p_warn = prob_dict.get("Warning", 0.0)
        p_fail = prob_dict.get("Failure", 0.0)
        wear_score = round(float((p_warn * 0.5) + (p_fail * 1.0)), 3)

        return {
            "joint": joint_name.lower(),
            "predicted_state": pred_state,
            "confidence": round(float(np.max(probs)), 3),
            "probabilities": prob_dict,
            "wear_score": wear_score
        }

    def predict_arm(self, arm_readings: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate predictions across all monitored joints of an arm.
        Returns the highest wear severity across the joints.
        """
        joint_results = {}
        worst_score = 0.0
        worst_state = "Normal"
        state_severity = {"Normal": 0, "Warning": 1, "Failure": 2}

        for joint_name, reading in arm_readings.items():
            res = self.predict_joint(joint_name, reading)
            joint_results[joint_name] = res
            if state_severity[res["predicted_state"]] > state_severity[worst_state]:
                worst_state = res["predicted_state"]
            if res["wear_score"] > worst_score:
                worst_score = res["wear_score"]

        return {
            "aggregate_state": worst_state,
            "max_wear_score": worst_score,
            "joint_details": joint_results
        }

if __name__ == "__main__":
    print("Training Predictive Wear Model...")
    res = train_predictive_model()
    print(f"Model successfully saved to: {res['model_path']}")
    print(f"Accuracy: {res['accuracy'] * 100:.2f}%")
