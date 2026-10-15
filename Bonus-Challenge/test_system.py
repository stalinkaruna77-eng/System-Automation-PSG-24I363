# Unit and Integration Tests for Robotic Arm Joint Health Monitoring

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.safety_interlock import SafetyInterlock
from src.predictive_wear import JointWearPredictor
from src.text_log_analyzer import MaintenanceLogAnalyzer
from src.spoof_detector import SpoofedSensorDetector
from src.health_monitor import RoboticArmHealthMonitor


class TestRoboticArmMonitoringSystem(unittest.TestCase):

    def setUp(self):
        self.interlock = SafetyInterlock()
        self.log_analyzer = MaintenanceLogAnalyzer()
        self.spoof_detector = SpoofedSensorDetector()
        self.monitor = RoboticArmHealthMonitor()

    # 1. Immediate Safety Stop
    def test_safety_interlock_torque_limit(self):
        readings = {
            "shoulder": {"torque_nm": 145.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0,  "temperature_c": 45.0, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0,  "temperature_c": 40.0, "vibration_mms": 0.8}
        }
        tripped, reason, details = self.interlock.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "shoulder")
        self.assertIn("torque 145.0 Nm exceeds", reason)

    def test_safety_interlock_temperature_limit(self):
        readings = {
            "shoulder": {"torque_nm": 60.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0, "temperature_c": 87.5, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0, "temperature_c": 40.0, "vibration_mms": 0.8}
        }
        tripped, reason, details = self.interlock.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "elbow")

    def test_safety_interlock_vibration_limit(self):
        readings = {
            "shoulder": {"torque_nm": 60.0, "temperature_c": 50.0, "vibration_mms": 1.5},
            "elbow":    {"torque_nm": 40.0, "temperature_c": 45.0, "vibration_mms": 1.0},
            "wrist":    {"torque_nm": 15.0, "temperature_c": 40.0, "vibration_mms": 8.2}
        }
        tripped, reason, details = self.interlock.evaluate_arm(readings)
        self.assertTrue(tripped)
        self.assertEqual(details["action"], "EMERGENCY_STOP")
        self.assertEqual(details["joint"], "wrist")

    # 2. Predictive Wear Detection
    def test_predictive_model_inference(self):
        predictor = JointWearPredictor()
        # Normal reading
        normal_res = predictor.predict_joint("shoulder", {
            "torque_nm": 60.0, "temperature_c": 46.0, "vibration_mms": 1.2,
            "operating_hours": 800, "load_kg": 2.5
        })
        self.assertIn(normal_res["predicted_state"], ["Normal", "Warning"])
        self.assertLess(normal_res["wear_score"], 0.7)

        # Severe wear reading
        worn_res = predictor.predict_joint("shoulder", {
            "torque_nm": 125.0, "temperature_c": 82.0, "vibration_mms": 6.9,
            "operating_hours": 12000, "load_kg": 9.0
        })
        self.assertEqual(worn_res["predicted_state"], "Failure")
        self.assertGreater(worn_res["wear_score"], 0.8)

    # 3. Maintenance Notes Signal
    def test_maintenance_notes_parsing(self):
        arm3_signal = self.log_analyzer.get_signal_for_arm("Arm-3")
        self.assertTrue(arm3_signal["has_notes"])
        self.assertEqual(arm3_signal["risk_level"], "CRITICAL")
        self.assertIn("grinding", arm3_signal["matched_keywords"])

        arm2_signal = self.log_analyzer.get_signal_for_arm("Arm-2")
        self.assertTrue(arm2_signal["has_notes"])
        self.assertEqual(arm2_signal["risk_level"], "NORMAL")

    def test_irrelevant_notes_filtered(self):
        text = "Technician Dave took a lunch break at 12:30. Replaced paper towels in restroom."
        analysis = self.log_analyzer.analyze_text(text)
        self.assertEqual(analysis["risk_level"], "NONE")
        self.assertTrue(analysis["is_irrelevant"])

    # 4. Spoofed Sensor Defense
    def test_cross_correlation_spoof_detection(self):
        res = self.spoof_detector.evaluate_reading("Arm-7", "shoulder", {
            "torque_nm": 15.0,       # Falsified low torque
            "temperature_c": 82.0,   # High heat
            "vibration_mms": 6.8,    # High vibration
            "load_kg": 6.0
        })
        self.assertTrue(res["is_spoofed"])
        self.assertEqual(res["attack_type"], "CROSS_CORRELATION_VIOLATION")

    def test_frozen_signal_detection(self):
        detector = SpoofedSensorDetector()
        for _ in range(5):
            detector.update_history("Arm-X", "elbow", 40.0000)
        is_frozen, msg = detector.check_frozen_sensor("Arm-X", "elbow")
        self.assertTrue(is_frozen)
        self.assertIn("FROZEN_SIGNAL_ATTACK", msg)

    # 5. All 4 Decisions Reachable
    def test_all_four_decisions_reachable(self):
        # SAFE
        safe_readings = {
            "shoulder": {"torque_nm": 62.0, "temperature_c": 46.0, "vibration_mms": 1.3, "operating_hours": 1000, "load_kg": 3.0},
            "elbow":    {"torque_nm": 41.0, "temperature_c": 42.0, "vibration_mms": 1.1, "operating_hours": 1000, "load_kg": 3.0},
            "wrist":    {"torque_nm": 17.0, "temperature_c": 38.0, "vibration_mms": 0.8, "operating_hours": 1000, "load_kg": 3.0}
        }
        res_safe = self.monitor.evaluate_arm("Arm-2", safe_readings)
        self.assertEqual(res_safe["final_decision"], "SAFE")

        # MONITOR
        monitor_readings = {
            "shoulder": {"torque_nm": 70.0, "temperature_c": 52.0, "vibration_mms": 1.6, "operating_hours": 4200, "load_kg": 4.5},
            "elbow":    {"torque_nm": 56.8, "temperature_c": 62.4, "vibration_mms": 3.1, "operating_hours": 4500, "load_kg": 4.5},
            "wrist":    {"torque_nm": 22.0, "temperature_c": 44.0, "vibration_mms": 1.3, "operating_hours": 4500, "load_kg": 4.5}
        }
        res_monitor = self.monitor.evaluate_arm("Arm-1", monitor_readings)
        self.assertEqual(res_monitor["final_decision"], "MONITOR")

        # SCHEDULE_MAINTENANCE
        maint_readings = {
            "shoulder": {"torque_nm": 72.0, "temperature_c": 51.0, "vibration_mms": 1.7, "operating_hours": 7500, "load_kg": 5.0},
            "elbow":    {"torque_nm": 48.0, "temperature_c": 49.0, "vibration_mms": 1.4, "operating_hours": 7500, "load_kg": 5.0},
            "wrist":    {"torque_nm": 33.2, "temperature_c": 76.0, "vibration_mms": 5.8, "operating_hours": 9200, "load_kg": 5.0}
        }
        res_maint = self.monitor.evaluate_arm("Arm-3", maint_readings)
        self.assertEqual(res_maint["final_decision"], "SCHEDULE_MAINTENANCE")

        # EMERGENCY_STOP
        stop_readings = {
            "shoulder": {"torque_nm": 155.0, "temperature_c": 50.0, "vibration_mms": 1.5, "operating_hours": 2000, "load_kg": 5.0},
            "elbow":    {"torque_nm": 40.0,  "temperature_c": 45.0, "vibration_mms": 1.0, "operating_hours": 2000, "load_kg": 5.0},
            "wrist":    {"torque_nm": 18.0,  "temperature_c": 40.0, "vibration_mms": 0.9, "operating_hours": 2000, "load_kg": 5.0}
        }
        res_stop = self.monitor.evaluate_arm("Arm-6", stop_readings)
        self.assertEqual(res_stop["final_decision"], "EMERGENCY_STOP")


if __name__ == "__main__":
    unittest.main()
