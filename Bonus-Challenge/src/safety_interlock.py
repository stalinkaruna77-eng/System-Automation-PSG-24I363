SAFETY_LIMITS = {
    "torque": {
        "shoulder": 140.0,  
        "elbow": 95.0,      
        "wrist": 45.0,      
    },
    "temperature": 85.0,    
    "vibration": 7.5,       
}

class SafetyInterlock:
    def __init__(self, limits=None):
        self.limits = limits or SAFETY_LIMITS
    def evaluate_joint(self, joint_name, reading):
        joint_key = joint_name.lower()
        torque = reading.get("torque_nm", 0.0)
        temp = reading.get("temperature_c", 0.0)
        vib = reading.get("vibration_mms", 0.0)
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

    def evaluate_arm(self, arm_readings):
        for joint, reading in arm_readings.items():
            tripped, reason, details = self.evaluate_joint(joint, reading)
            if tripped:
                return True, reason, details
        return False, None, None
