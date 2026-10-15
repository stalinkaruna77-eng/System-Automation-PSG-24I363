import numpy as np
class SpoofedSensorDetector:
    def __init__(self, variance_threshold=0.005):
        self.variance_threshold = variance_threshold
        self.history_buffer = {}

    def _get_buffer_key(self, arm_id, joint):
        return f"{arm_id.lower()}_{joint.lower()}"
    def update_history(self, arm_id, joint, torque, window_size=5):
        key = self._get_buffer_key(arm_id, joint)
        if key not in self.history_buffer:
            self.history_buffer[key] = []
        self.history_buffer[key].append(torque)
        if len(self.history_buffer[key]) > window_size:
            self.history_buffer[key].pop(0)

    def check_frozen_sensor(self, arm_id, joint):
        key = self._get_buffer_key(arm_id, joint)
        buffer = self.history_buffer.get(key, [])
        if len(buffer) >= 4:
            variance = float(np.var(buffer))
            if variance < self.variance_threshold:
                return True, (
                    f"FROZEN_SIGNAL_ATTACK: {joint.upper()} torque variance is {variance:.6f}. "
                    f"Signal is completely flat and likely replayed."
                )
        return False, None
    def check_physical_cross_correlation(self, joint, torque, temperature, vibration):
        joint_key = joint.lower()

        stress_torque_floors = {
            "shoulder": 50.0,
            "elbow": 35.0,
            "wrist": 15.0
        }
        floor = stress_torque_floors.get(joint_key, 30.0)
        if vibration >= 4.5 and temperature >= 65.0 and torque < floor:
            return True, "CROSS_CORRELATION_VIOLATION", (
                f"SPOOF_ATTACK_DETECTED: {joint.upper()} reports elevated vibration ({vibration:.2f} mm/s) "
                f"and thermal distress ({temperature:.1f} °C), but reported torque is suspiciously low "
                f"({torque:.1f} Nm < expected minimum {floor:.1f} Nm under active distress). "
                f"Torque sensor is likely spoofed to mask hardware fault!"
            )
        if temperature >= 75.0 and torque < (floor * 0.75):
            return True, "THERMAL_DISSIPATION_MISMATCH", (
                f"SPOOF_ATTACK_DETECTED: {joint.upper()} exhibits extreme temperature ({temperature:.1f} °C) "
                f"with negligible torque ({torque:.1f} Nm)."
            )

        return False, None, None

    def check_gravitational_payload_consistency(self, joint, torque, load_kg):
        joint_key = joint.lower()
        if joint_key == "shoulder" and load_kg >= 6.0 and torque < 25.0:
            return True, (
                f"PAYLOAD_PHYSICS_VIOLATION: Shoulder reported torque ({torque:.1f} Nm) is "
                f"too low to support active {load_kg:.1f} kg payload."
            )
        if joint_key == "elbow" and load_kg >= 6.0 and torque < 15.0:
            return True, (
                f"PAYLOAD_PHYSICS_VIOLATION: Elbow reported torque ({torque:.1f} Nm) is "
                f"too low to support active {load_kg:.1f} kg payload."
            )
        return False, None
    def evaluate_reading(self, arm_id, joint, reading):
        torque = float(reading.get("torque_nm", 0.0))
        temp = float(reading.get("temperature_c", 25.0))
        vib = float(reading.get("vibration_mms", 1.0))
        load_kg = float(reading.get("load_kg", 0.0))
        self.update_history(arm_id, joint, torque)
        is_cross_spoof, anomaly_type, cross_msg = self.check_physical_cross_correlation(
            joint, torque, temp, vib
        )
        if is_cross_spoof:
            return {
                "is_spoofed": True,
                "confidence": 0.95,
                "attack_type": anomaly_type,
                "message": cross_msg,
                "unmasked_danger": temp > 80.0 or vib > 7.0
            }
        is_load_spoof, load_msg = self.check_gravitational_payload_consistency(joint, torque, load_kg)
        if is_load_spoof:
            return {
                "is_spoofed": True,
                "confidence": 0.90,
                "attack_type": "GRAVITATIONAL_LOAD_MISMATCH",
                "message": load_msg,
                "unmasked_danger": False
            }
        is_frozen, frozen_msg = self.check_frozen_sensor(arm_id, joint)
        if is_frozen:
            return {
                "is_spoofed": True,
                "confidence": 0.88,
                "attack_type": "FROZEN_REPLAY_ATTACK",
                "message": frozen_msg,
                "unmasked_danger": False
            }

        return {
            "is_spoofed": False,
            "confidence": 0.0,
            "attack_type": "NONE",
            "message": "Sensor telemetry is physically consistent and verified.",
            "unmasked_danger": False
        }

    def evaluate_arm(self, arm_id, arm_readings):
        spoofed_joints = []
        highest_confidence = 0.0
        primary_alert = None
        has_unmasked_danger = False
        for joint, reading in arm_readings.items():
            res = self.evaluate_reading(arm_id, joint, reading)
            if res["is_spoofed"]:
                spoofed_joints.append(joint)
                if res["confidence"] > highest_confidence:
                    highest_confidence = res["confidence"]
                    primary_alert = res["message"]
                if res.get("unmasked_danger", False):
                    has_unmasked_danger = True
        return {
            "is_spoofed": len(spoofed_joints) > 0,
            "spoofed_joints": spoofed_joints,
            "confidence": highest_confidence,
            "alert": primary_alert or "No spoofing detected.",
            "unmasked_danger": has_unmasked_danger
        }
