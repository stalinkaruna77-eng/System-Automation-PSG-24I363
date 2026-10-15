"""
Requirement 4: Spoofed-Sensor Defense Engine
Course: 23IF02 System Automation — Bonus Challenge

Defends against sensor spoofing attacks where an adversary or compromised edge device
injects forged, artificially suppressed, or frozen joint-torque readings to disguise
underlying physical damage or dangerous operational conditions.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np

class SpoofedSensorDetector:
    """
    Physics-informed and statistical cross-sensor spoofing detector.
    
    Verifies that reported torque is physically consistent with:
    1. Cross-sensor electro-mechanical dissipation (Temperature & Vibration vs Torque)
    2. Minimum static gravitational load requirement (Payload vs Shoulder/Elbow Torque)
    3. Natural ADC sensor micro-noise (Temporal variance / Frozen sensor detection)
    """

    def __init__(self, variance_threshold: float = 0.005):
        self.variance_threshold = variance_threshold
        # Rolling history per arm and joint to detect frozen/replay spoofing
        self.history_buffer: Dict[str, List[float]] = {}

    def _get_buffer_key(self, arm_id: str, joint: str) -> str:
        return f"{arm_id.lower()}_{joint.lower()}"

    def update_history(self, arm_id: str, joint: str, torque: float, window_size: int = 5):
        """Record torque sample in rolling temporal buffer."""
        key = self._get_buffer_key(arm_id, joint)
        if key not in self.history_buffer:
            self.history_buffer[key] = []
        self.history_buffer[key].append(torque)
        if len(self.history_buffer[key]) > window_size:
            self.history_buffer[key].pop(0)

    def check_frozen_sensor(self, arm_id: str, joint: str) -> Tuple[bool, Optional[str]]:
        """
        Detect zero-variance / frozen signal attacks where an attacker streams
        an identical synthetic float to appear steady.
        """
        key = self._get_buffer_key(arm_id, joint)
        buffer = self.history_buffer.get(key, [])
        if len(buffer) >= 4:
            variance = float(np.var(buffer))
            if variance < self.variance_threshold:
                return True, (
                    f"FROZEN_SIGNAL_ATTACK: {joint.upper()} torque variance is {variance:.6f} "
                    f"(below physical ADC noise threshold {self.variance_threshold}). "
                    f"Sensor signal appears artificially clamped or replayed."
                )
        return False, None

    def check_physical_cross_correlation(
        self,
        joint: str,
        torque: float,
        temperature: float,
        vibration: float
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Physics Check 1: Electro-mechanical energy dissipation coupling.
        
        Severe mechanical friction or bearing failure generates elevated heat and vibration.
        If vibration > 4.5 mm/s AND temperature > 65°C, but reported torque is unrealistically
        low or nominal, the torque reading is physically impossible and spoofed.
        """
        joint_key = joint.lower()

        # Expected minimum friction torque under severe vibrational/thermal stress
        stress_torque_floors = {
            "shoulder": 50.0,  # Nm
            "elbow": 35.0,     # Nm
            "wrist": 15.0      # Nm
        }
        floor = stress_torque_floors.get(joint_key, 30.0)

        # High vibration and high temperature with suppressed torque reading
        if vibration >= 4.5 and temperature >= 65.0 and torque < floor:
            return True, "CROSS_CORRELATION_VIOLATION", (
                f"SPOOF_ATTACK_DETECTED: {joint.upper()} reports elevated vibration ({vibration:.2f} mm/s) "
                f"and thermal distress ({temperature:.1f} °C), but reported torque is suspiciously low "
                f"({torque:.1f} Nm < expected minimum {floor:.1f} Nm under active distress). "
                f"Torque sensor is likely spoofed to mask hardware fault!"
            )

        # Severe thermal runaway with baseline torque
        if temperature >= 75.0 and torque < (floor * 0.75):
            return True, "THERMAL_DISSIPATION_MISMATCH", (
                f"SPOOF_ATTACK_DETECTED: {joint.upper()} exhibits extreme thermal dissipation ({temperature:.1f} °C) "
                f"with negligible torque ({torque:.1f} Nm). Violates thermodynamic conservation of energy."
            )

        return False, None, None

    def check_gravitational_payload_consistency(
        self,
        joint: str,
        torque: float,
        load_kg: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Physics Check 2: Gravitational moment consistency.
        
        A robot arm holding a 6+ kg tool cannot experience near-zero torque on its shoulder/elbow.
        """
        joint_key = joint.lower()
        if joint_key == "shoulder" and load_kg >= 6.0 and torque < 25.0:
            return True, (
                f"PAYLOAD_PHYSICS_VIOLATION: Shoulder reported torque ({torque:.1f} Nm) is "
                f"insufficient to support active {load_kg:.1f} kg payload. Signal appears artificially suppressed."
            )
        if joint_key == "elbow" and load_kg >= 6.0 and torque < 15.0:
            return True, (
                f"PAYLOAD_PHYSICS_VIOLATION: Elbow reported torque ({torque:.1f} Nm) is "
                f"insufficient to support active {load_kg:.1f} kg payload."
            )
        return False, None

    def evaluate_reading(
        self,
        arm_id: str,
        joint: str,
        reading: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run full spoof detection pipeline on a single joint reading.
        """
        torque = float(reading.get("torque_nm", 0.0))
        temp = float(reading.get("temperature_c", 25.0))
        vib = float(reading.get("vibration_mms", 1.0))
        load_kg = float(reading.get("load_kg", 0.0))

        # Update history buffer
        self.update_history(arm_id, joint, torque)

        # 1. Physics cross-sensor check
        is_cross_spoof, anomaly_type, cross_msg = self.check_physical_cross_correlation(joint, torque, temp, vib)
        if is_cross_spoof:
            return {
                "is_spoofed": True,
                "confidence": 0.95,
                "attack_type": anomaly_type,
                "message": cross_msg,
                "unmasked_danger": temp > 80.0 or vib > 7.0
            }

        # 2. Gravitational payload consistency
        is_load_spoof, load_msg = self.check_gravitational_payload_consistency(joint, torque, load_kg)
        if is_load_spoof:
            return {
                "is_spoofed": True,
                "confidence": 0.90,
                "attack_type": "GRAVITATIONAL_LOAD_MISMATCH",
                "message": load_msg,
                "unmasked_danger": False
            }

        # 3. Temporal frozen sensor check
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

    def evaluate_arm(self, arm_id: str, arm_readings: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate all joints for an arm and report any detected spoofing attack."""
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
