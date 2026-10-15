from src.safety_interlock import SafetyInterlock
from src.predictive_wear import JointWearPredictor
from src.text_log_analyzer import MaintenanceLogAnalyzer
from src.spoof_detector import SpoofedSensorDetector

class RoboticArmHealthMonitor:
    def __init__(self, safety_limits=None, model_path=None, log_file_path=None):
        self.safety_interlock = SafetyInterlock(safety_limits)
        self.wear_predictor = JointWearPredictor(model_path) if model_path else JointWearPredictor()
        self.log_analyzer = MaintenanceLogAnalyzer(log_file_path)
        self.spoof_detector = SpoofedSensorDetector()
    def evaluate_arm(self, arm_id, arm_readings):
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

        ml_prediction = self.wear_predictor.predict_arm(arm_readings)
        log_signal = self.log_analyzer.get_signal_for_arm(arm_id)

        ml_state = ml_prediction["aggregate_state"]  
        log_risk = log_signal["risk_level"]          
        if ml_state == "Failure" or log_risk == "CRITICAL":
            final_decision = "SCHEDULE_MAINTENANCE"
            reasons = []
            if ml_state == "Failure":
                reasons.append(f"ML predictive wear model indicates severe failure risk (Wear score: {ml_prediction['max_wear_score']:.2f})")
            if log_risk == "CRITICAL":
                reasons.append(f"Technician notes report critical observation: '{log_signal['summary']}'")
            summary = " | ".join(reasons)
            action = "Dispatch maintenance team to replace degraded joint component before full failure."

        elif ml_state == "Warning" or log_risk == "WARNING":
            final_decision = "MONITOR"
            reasons = []
            if ml_state == "Warning":
                reasons.append(f"ML model flags moderate wear progression (Wear score: {ml_prediction['max_wear_score']:.2f})")
            if log_risk == "WARNING":
                reasons.append(f"Technician logged warning note: '{log_signal['summary']}'")
            summary = " | ".join(reasons)
            action = "Increase sensor logging frequency to 10 Hz; re-evaluate after current batch cycle."
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
