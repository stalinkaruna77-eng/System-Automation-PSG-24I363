"""
Requirement 5: Robotic Arm Joint Health Monitoring System (Fusion Engine)
Course: 23IF02 System Automation — Bonus Challenge

Integrates:
1. Deterministic Safety Interlock (Priority 0)
2. Spoofed Sensor Defense (Priority 1)
3. Predictive Wear Machine Learning Model (Priority 2)
4. Free-Text Technician Maintenance Log NLP (Priority 2)

Produces exactly one final decision per robotic arm:
- SAFE
- MONITOR
- SCHEDULE_MAINTENANCE
- EMERGENCY_STOP
"""

from typing import Dict, Any, Optional
from src.safety_interlock import SafetyInterlock
from src.predictive_wear import JointWearPredictor
from src.text_log_analyzer import MaintenanceLogAnalyzer
from src.spoof_detector import SpoofedSensorDetector

class RoboticArmHealthMonitor:
    """
    Central Health Monitoring and Decision Fusion Engine for 6-Axis Robotic Arms.
    """

    def __init__(
        self,
        safety_limits: Optional[Dict[str, Any]] = None,
        model_path: Optional[str] = None,
        log_file_path: Optional[str] = None
    ):
        self.safety_interlock = SafetyInterlock(safety_limits)
        self.wear_predictor = JointWearPredictor(model_path) if model_path else JointWearPredictor()
        self.log_analyzer = MaintenanceLogAnalyzer(log_file_path)
        self.spoof_detector = SpoofedSensorDetector()

    def evaluate_arm(self, arm_id: str, arm_readings: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate full operational state of a single robotic arm.
        
        Args:
            arm_id: e.g. "Arm-1", "Arm-3"
            arm_readings: Dict of joint readings, e.g.
                {
                    "shoulder": {"torque_nm": 65.0, "temperature_c": 48.0, "vibration_mms": 1.4, ...},
                    "elbow":    {"torque_nm": 42.0, "temperature_c": 44.0, "vibration_mms": 1.2, ...},
                    "wrist":    {"torque_nm": 18.0, "temperature_c": 40.0, "vibration_mms": 0.9, ...}
                }
                
        Returns:
            Structured diagnostic dictionary including final decision, rationale, and component signals.
        """
        # =========================================================================
        # STAGE 1: IMMEDIATE DETERMINISTIC SAFETY STOP (Zero-latency hardware check)
        # =========================================================================
        # This check NEVER depends on ML and executes first before any other stage.
        is_tripped, trip_reason, trip_details = self.safety_interlock.evaluate_arm(arm_readings)
        if is_tripped:
            return {
                "arm_id": arm_id,
                "final_decision": "EMERGENCY_STOP",
                "trigger": "SAFETY_INTERLOCK_TRIPPED",
                "summary": f"Hardware safety limit violated: {trip_reason}",
                "safety_interlock": {"tripped": True, "details": trip_details},
                "spoof_defense": None,
                "predictive_ml": None,
                "maintenance_log": None,
                "action_required": "IMMEDIATE HARDWARE POWER CUT AND INSPECTION."
            }

        # =========================================================================
        # STAGE 2: SPOOFED-SENSOR DEFENSE CHECK (Cross-sensor physics & replay test)
        # =========================================================================
        spoof_report = self.spoof_detector.evaluate_arm(arm_id, arm_readings)
        if spoof_report["is_spoofed"]:
            if spoof_report.get("unmasked_danger", False):
                return {
                    "arm_id": arm_id,
                    "final_decision": "EMERGENCY_STOP",
                    "trigger": "CRITICAL_SPOOF_MASKING_DANGER",
                    "summary": f"CRITICAL: Spoofed sensor attack detected masking imminent mechanical danger! {spoof_report['alert']}",
                    "safety_interlock": {"tripped": False},
                    "spoof_defense": spoof_report,
                    "predictive_ml": None,
                    "maintenance_log": None,
                    "action_required": "EMERGENCY POWER ISOLATION: Tampered telemetry masking hazardous state."
                }
            else:
                return {
                    "arm_id": arm_id,
                    "final_decision": "SCHEDULE_MAINTENANCE",
                    "trigger": "SENSOR_SPOOFING_DETECTED",
                    "summary": f"Sensor anomaly / spoofing detected: {spoof_report['alert']}",
                    "safety_interlock": {"tripped": False},
                    "spoof_defense": spoof_report,
                    "predictive_ml": None,
                    "maintenance_log": None,
                    "action_required": "Dispatch technician to inspect encoder/torque sensor wiring and physical calibration."
                }

        # =========================================================================
        # STAGE 3: PREDICTIVE ML WEAR MODEL & MAINTENANCE LOG ANALYSIS
        # =========================================================================
        ml_prediction = self.wear_predictor.predict_arm(arm_readings)
        log_signal = self.log_analyzer.get_signal_for_arm(arm_id)

        ml_state = ml_prediction["aggregate_state"]  # "Normal", "Warning", "Failure"
        log_risk = log_signal["risk_level"]          # "CRITICAL", "WARNING", "NORMAL", "NONE"

        # =========================================================================
        # STAGE 4: DECISION MATRIX / SIGNAL FUSION
        # =========================================================================
        # High Wear or Critical Tech Observation -> SCHEDULE_MAINTENANCE
        if ml_state == "Failure" or log_risk == "CRITICAL":
            final_decision = "SCHEDULE_MAINTENANCE"
            reasons = []
            if ml_state == "Failure":
                reasons.append(f"ML predictive wear model indicates severe failure risk (Wear score: {ml_prediction['max_wear_score']:.2f})")
            if log_risk == "CRITICAL":
                reasons.append(f"Technician notes report critical observation: '{log_signal['summary']}'")
            summary = " | ".join(reasons)
            action = "Dispatch maintenance team to replace degraded joint component before full failure."

        # Moderate Wear or Warning in Tech Log -> MONITOR
        elif ml_state == "Warning" or log_risk == "WARNING":
            final_decision = "MONITOR"
            reasons = []
            if ml_state == "Warning":
                reasons.append(f"ML model flags moderate wear progression (Wear score: {ml_prediction['max_wear_score']:.2f})")
            if log_risk == "WARNING":
                reasons.append(f"Technician logged warning note: '{log_signal['summary']}'")
            summary = " | ".join(reasons)
            action = "Increase sensor logging frequency to 10 Hz; re-evaluate after current batch cycle."

        # All signals Nominal -> SAFE
        else:
            final_decision = "SAFE"
            summary = "All joint parameters within nominal limits; ML model reports healthy state; no adverse technician notes."
            action = "Continue standard automated assembly line operations."

        return {
            "arm_id": arm_id,
            "final_decision": final_decision,
            "trigger": f"FUSION_RESULT [ML={ml_state}, LOG={log_risk}]",
            "summary": summary,
            "safety_interlock": {"tripped": False},
            "spoof_defense": spoof_report,
            "predictive_ml": ml_prediction,
            "maintenance_log": log_signal,
            "action_required": action
        }
