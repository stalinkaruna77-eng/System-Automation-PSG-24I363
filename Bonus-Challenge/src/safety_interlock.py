"""
Requirement 1: Immediate Safety Stop Interlock
Course: 23IF02 System Automation — Bonus Challenge

Deterministic, zero-latency safety engine that evaluates raw sensor readings
independently of any ML model. If any single joint crosses an unambiguous danger
threshold, an immediate EMERGENCY_STOP is triggered.
"""

from typing import Dict, Any, Tuple, Optional

# Safety Thresholds based on industrial robotics standards (ISO 10816-3 & joint mechanical ratings)
# Shoulder carries primary mechanical moment; elbow bears intermediate articulation; wrist has delicate gearing.
SAFETY_LIMITS = {
    "torque": {
        "shoulder": 140.0,  # Nm (rated nominal ~65-110 Nm; >140 Nm indicates severe jam/collision)
        "elbow": 95.0,      # Nm (rated nominal ~42-75 Nm; >95 Nm indicates binding/gearbox seizure)
        "wrist": 45.0,      # Nm (rated nominal ~18-32 Nm; >45 Nm indicates tool collision or shear risk)
    },
    "temperature": 85.0,    # °C across all joints (lubricant breakdown & neodymium magnet demag risk)
    "vibration": 7.5,       # mm/s RMS (ISO 10816-3 Zone D: dangerous vibration, bearing fracture hazard)
}

class SafetyInterlock:
    """
    Hardware-level safety interlock emulator.
    Must never rely on ML predictions or network inference.
    """

    def __init__(self, limits: Optional[Dict[str, Any]] = None):
        self.limits = limits or SAFETY_LIMITS

    def evaluate_joint(self, joint_name: str, reading: Dict[str, float]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Evaluate a single joint's raw sensor readings against hard physical limits.
        
        Args:
            joint_name: 'shoulder', 'elbow', or 'wrist'
            reading: dict containing 'torque_nm', 'temperature_c', 'vibration_mms'
            
        Returns:
            (is_tripped, violation_reason, detail_dict)
        """
        joint_key = joint_name.lower()
        torque = reading.get("torque_nm", 0.0)
        temp = reading.get("temperature_c", 0.0)
        vib = reading.get("vibration_mms", 0.0)

        # 1. Torque threshold check (joint-specific mechanical rating)
        max_torque = self.limits["torque"].get(joint_key, 100.0)
        if torque > max_torque:
            details = {
                "rule": "TORQUE_LIMIT_EXCEEDED",
                "joint": joint_key,
                "metric": "torque_nm",
                "value": torque,
                "limit": max_torque,
                "action": "EMERGENCY_STOP"
            }
            reason = f"CRITICAL: {joint_key.upper()} torque {torque:.1f} Nm exceeds hard safety limit of {max_torque:.1f} Nm"
            return True, reason, details

        # 2. Temperature threshold check (insulation/lubrication limit)
        max_temp = self.limits["temperature"]
        if temp > max_temp:
            details = {
                "rule": "CRITICAL_TEMPERATURE_EXCEEDED",
                "joint": joint_key,
                "metric": "temperature_c",
                "value": temp,
                "limit": max_temp,
                "action": "EMERGENCY_STOP"
            }
            reason = f"CRITICAL: {joint_key.upper()} temperature {temp:.1f} °C exceeds thermal ceiling of {max_temp:.1f} °C"
            return True, reason, details

        # 3. Vibration threshold check (ISO 10816-3 Zone D)
        max_vib = self.limits["vibration"]
        if vib > max_vib:
            details = {
                "rule": "DANGEROUS_VIBRATION_EXCEEDED",
                "joint": joint_key,
                "metric": "vibration_mms",
                "value": vib,
                "limit": max_vib,
                "action": "EMERGENCY_STOP"
            }
            reason = f"CRITICAL: {joint_key.upper()} vibration {vib:.2f} mm/s exceeds structural limit of {max_vib:.2f} mm/s"
            return True, reason, details

        return False, None, None

    def evaluate_arm(self, arm_readings: Dict[str, Dict[str, float]]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check all monitored joints of an arm ('shoulder', 'elbow', 'wrist').
        Returns immediate trip if ANY single joint reading crosses dangerous limits.
        """
        for joint, reading in arm_readings.items():
            tripped, reason, details = self.evaluate_joint(joint, reading)
            if tripped:
                return True, reason, details
        return False, None, None
