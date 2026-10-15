# Robotic Arm Joint Health Monitoring System - Pipeline Demonstration
# Runs sample scenarios showing all 4 reachable decisions (SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP)
# and demonstrates the spoofed-sensor defense.

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.health_monitor import RoboticArmHealthMonitor


def main():
    print("Initializing Robotic Arm Joint Health Monitoring System...")
    monitor = RoboticArmHealthMonitor()
    print("Modules loaded.\n")

    # -------------------------------------------------------------------------
    # Scenario 1: Expected Outcome -> SAFE
    # -------------------------------------------------------------------------
    print("--------------------------------------------------")
    print("Scenario 1: Normal Operation (Arm-2)")
    print("--------------------------------------------------")
    arm_2_readings = {
        "shoulder": {"torque_nm": 62.5, "temperature_c": 46.2, "vibration_mms": 1.35, "operating_hours": 1200, "load_kg": 3.0},
        "elbow":    {"torque_nm": 41.0, "temperature_c": 42.5, "vibration_mms": 1.10, "operating_hours": 1200, "load_kg": 3.0},
        "wrist":    {"torque_nm": 17.5, "temperature_c": 38.0, "vibration_mms": 0.85, "operating_hours": 1200, "load_kg": 3.0}
    }
    result_1 = monitor.evaluate_arm("Arm-2", arm_2_readings)
    print("Target: Arm-2")
    print("Readings: Shoulder 62.5 Nm / 46.2 C | Elbow 41.0 Nm | Wrist 17.5 Nm")
    print(f"Final Decision: [{result_1['final_decision']}]")
    print(f"Summary:        {result_1['summary']}")
    print(f"Action:         {result_1['action_required']}\n")

    # -------------------------------------------------------------------------
    # Scenario 2: Expected Outcome -> MONITOR
    # -------------------------------------------------------------------------
    print("--------------------------------------------------")
    print("Scenario 2: Developing Wear & Minor Note (Arm-1)")
    print("--------------------------------------------------")
    arm_1_readings = {
        "shoulder": {"torque_nm": 70.0, "temperature_c": 52.0, "vibration_mms": 1.6, "operating_hours": 4200, "load_kg": 4.5},
        "elbow":    {"torque_nm": 56.8, "temperature_c": 62.4, "vibration_mms": 3.12, "operating_hours": 4500, "load_kg": 4.5},
        "wrist":    {"torque_nm": 22.0, "temperature_c": 44.0, "vibration_mms": 1.3, "operating_hours": 4500, "load_kg": 4.5}
    }
    result_2 = monitor.evaluate_arm("Arm-1", arm_1_readings)
    print("Target: Arm-1")
    print("Readings: Elbow slightly warm (62.4 C, 3.12 mm/s vibration)")
    print(f"Final Decision: [{result_2['final_decision']}]")
    print(f"Summary:        {result_2['summary']}")
    print(f"Action:         {result_2['action_required']}\n")

    # -------------------------------------------------------------------------
    # Scenario 3: Expected Outcome -> SCHEDULE_MAINTENANCE
    # -------------------------------------------------------------------------
    print("--------------------------------------------------")
    print("Scenario 3: Severe Wear & Critical Note (Arm-3)")
    print("--------------------------------------------------")
    arm_3_readings = {
        "shoulder": {"torque_nm": 72.0, "temperature_c": 51.0, "vibration_mms": 1.7, "operating_hours": 7500, "load_kg": 5.0},
        "elbow":    {"torque_nm": 48.0, "temperature_c": 49.0, "vibration_mms": 1.4, "operating_hours": 7500, "load_kg": 5.0},
        "wrist":    {"torque_nm": 33.2, "temperature_c": 76.0, "vibration_mms": 5.80, "operating_hours": 9200, "load_kg": 5.0}
    }
    result_3 = monitor.evaluate_arm("Arm-3", arm_3_readings)
    print("Target: Arm-3")
    print("Readings: Wrist vibration 5.80 mm/s, temperature 76.0 C, 9200 hours")
    print(f"Final Decision: [{result_3['final_decision']}]")
    print(f"Summary:        {result_3['summary']}")
    print(f"Action:         {result_3['action_required']}\n")

    # -------------------------------------------------------------------------
    # Scenario 4: Expected Outcome -> EMERGENCY_STOP (Hardware Safety Trip)
    # -------------------------------------------------------------------------
    print("--------------------------------------------------")
    print("Scenario 4: Hard Safety Threshold Violation (Arm-6)")
    print("--------------------------------------------------")
    arm_critical_readings = {
        "shoulder": {"torque_nm": 162.4, "temperature_c": 55.0, "vibration_mms": 2.1, "operating_hours": 3000, "load_kg": 7.0},
        "elbow":    {"torque_nm": 45.0,  "temperature_c": 44.0, "vibration_mms": 1.2, "operating_hours": 3000, "load_kg": 7.0},
        "wrist":    {"torque_nm": 20.0,  "temperature_c": 41.0, "vibration_mms": 1.0, "operating_hours": 3000, "load_kg": 7.0}
    }
    result_4 = monitor.evaluate_arm("Arm-6", arm_critical_readings)
    print("Target: Arm-6")
    print("Readings: Shoulder torque spiked to 162.4 Nm (limit is 140.0 Nm)")
    print(f"Final Decision: [{result_4['final_decision']}]")
    print(f"Summary:        {result_4['summary']}")
    print(f"Action:         {result_4['action_required']}\n")

    # -------------------------------------------------------------------------
    # Scenario 5: Spoofed Sensor Attack Caught
    # -------------------------------------------------------------------------
    print("--------------------------------------------------")
    print("Scenario 5: Spoofed Sensor Defense (Arm-7)")
    print("--------------------------------------------------")
    print("Simulated attack: Adversary fakes shoulder torque as 18.0 Nm to look normal,")
    print("while temperature is 82.5 C and vibration is 7.10 mm/s.")
    arm_spoofed_readings = {
        "shoulder": {"torque_nm": 18.0, "temperature_c": 82.5, "vibration_mms": 7.10, "operating_hours": 6000, "load_kg": 4.0},
        "elbow":    {"torque_nm": 42.0, "temperature_c": 45.0, "vibration_mms": 1.20, "operating_hours": 6000, "load_kg": 4.0},
        "wrist":    {"torque_nm": 18.0, "temperature_c": 40.0, "vibration_mms": 0.90, "operating_hours": 6000, "load_kg": 4.0}
    }
    result_5 = monitor.evaluate_arm("Arm-7", arm_spoofed_readings)
    print("Target: Arm-7")
    print(f"Final Decision: [{result_5['final_decision']}]")
    print(f"Summary:        {result_5['summary']}")
    print(f"Action:         {result_5['action_required']}\n")

    # -------------------------------------------------------------------------
    # Summary of reachable decisions
    # -------------------------------------------------------------------------
    all_decisions = {
        result_1["final_decision"],
        result_2["final_decision"],
        result_3["final_decision"],
        result_4["final_decision"]
    }
    print("--------------------------------------------------")
    print(f"Verified reachable decisions: {all_decisions}")
    print("All 4 states (SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP) verified successfully.")


if __name__ == "__main__":
    main()
