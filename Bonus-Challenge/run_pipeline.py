"""
End-to-End Pipeline Runner: Robotic Arm Joint Health Monitoring System
Course: 23IF02 System Automation — Bonus Challenge

Demonstrates all 5 challenge requirements and proves that all 4 final decisions
(SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP) are fully reachable.
Also demonstrates detection of a spoofed sensor attack.
"""

import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.health_monitor import RoboticArmHealthMonitor

def print_separator(title="", width=80):
    if title:
        print(f"\n{'='*15} {title.upper()} {'='*(width - 17 - len(title))}")
    else:
        print("=" * width)

def format_decision_banner(decision: str) -> str:
    colors = {
        "SAFE": "\033[92m[ SAFE ]\033[0m",
        "MONITOR": "\033[93m[ MONITOR ]\033[0m",
        "SCHEDULE_MAINTENANCE": "\033[94m[ SCHEDULE_MAINTENANCE ]\033[0m",
        "EMERGENCY_STOP": "\033[91m[ EMERGENCY_STOP ]\033[0m"
    }
    return colors.get(decision, f"[{decision}]")

def main():
    print_separator("23IF02 SYSTEM AUTOMATION — BONUS CHALLENGE DEMONSTRATION")
    print("Initializing Robotic Arm Joint Health Monitoring System...")
    monitor = RoboticArmHealthMonitor()
    print("Safety Interlock, Predictive ML Model, NLP Analyzer & Spoof Defense Loaded Successfully.\n")

    # =========================================================================
    # SCENARIO 1: Expected Outcome -> SAFE
    # =========================================================================
    print_separator("Scenario 1: Normal Nominal Assembly Operation")
    arm_2_readings = {
        "shoulder": {"torque_nm": 62.5, "temperature_c": 46.2, "vibration_mms": 1.35, "operating_hours": 1200, "load_kg": 3.0},
        "elbow":    {"torque_nm": 41.0, "temperature_c": 42.5, "vibration_mms": 1.10, "operating_hours": 1200, "load_kg": 3.0},
        "wrist":    {"torque_nm": 17.5, "temperature_c": 38.0, "vibration_mms": 0.85, "operating_hours": 1200, "load_kg": 3.0}
    }
    result_1 = monitor.evaluate_arm("Arm-2", arm_2_readings)
    print(f"Target: Arm-2")
    print(f"Telemetries: Shoulder 62.5 Nm / 46.2°C / 1.35 mm/s | Elbow 41.0 Nm | Wrist 17.5 Nm")
    print(f"FINAL DECISION: {format_decision_banner(result_1['final_decision'])}")
    print(f"Rationale:      {result_1['summary']}")
    print(f"Action:         {result_1['action_required']}")

    # =========================================================================
    # SCENARIO 2: Expected Outcome -> MONITOR
    # =========================================================================
    print_separator("Scenario 2: Early Warning Signs & Technician Note")
    arm_1_readings = {
        "shoulder": {"torque_nm": 70.0, "temperature_c": 52.0, "vibration_mms": 1.6, "operating_hours": 4200, "load_kg": 4.5},
        "elbow":    {"torque_nm": 56.8, "temperature_c": 62.4, "vibration_mms": 3.12, "operating_hours": 4500, "load_kg": 4.5},
        "wrist":    {"torque_nm": 22.0, "temperature_c": 44.0, "vibration_mms": 1.3, "operating_hours": 4500, "load_kg": 4.5}
    }
    result_2 = monitor.evaluate_arm("Arm-1", arm_1_readings)
    print(f"Target: Arm-1")
    print(f"Telemetries: Elbow elevated to 62.4°C / 3.12 mm/s / 56.8 Nm (Moderate wear)")
    print(f"Tech Notes:  Elena logged 'elbow joint slightly warm... minor rhythmic clicking'")
    print(f"FINAL DECISION: {format_decision_banner(result_2['final_decision'])}")
    print(f"Rationale:      {result_2['summary']}")
    print(f"Action:         {result_2['action_required']}")

    # =========================================================================
    # SCENARIO 3: Expected Outcome -> SCHEDULE_MAINTENANCE
    # =========================================================================
    print_separator("Scenario 3: Severe Predictive Wear & Critical Technician Note")
    arm_3_readings = {
        "shoulder": {"torque_nm": 72.0, "temperature_c": 51.0, "vibration_mms": 1.7, "operating_hours": 7500, "load_kg": 5.0},
        "elbow":    {"torque_nm": 48.0, "temperature_c": 49.0, "vibration_mms": 1.4, "operating_hours": 7500, "load_kg": 5.0},
        "wrist":    {"torque_nm": 33.2, "temperature_c": 76.0, "vibration_mms": 5.80, "operating_hours": 9200, "load_kg": 5.0}
    }
    result_3 = monitor.evaluate_arm("Arm-3", arm_3_readings)
    print(f"Target: Arm-3")
    print(f"Telemetries: Wrist high vibration 5.80 mm/s / 76.0°C / 9200 operating hours")
    print(f"Tech Notes:  Marcus logged 'URGENT OBSERVATION on Arm-3: Heavy metallic grinding noise audible from wrist...'")
    print(f"FINAL DECISION: {format_decision_banner(result_3['final_decision'])}")
    print(f"Rationale:      {result_3['summary']}")
    print(f"Action:         {result_3['action_required']}")

    # =========================================================================
    # SCENARIO 4: Expected Outcome -> EMERGENCY_STOP (Deterministic Safety Interlock)
    # =========================================================================
    print_separator("Scenario 4: Deterministic Hard Safety Threshold Violation")
    arm_critical_readings = {
        "shoulder": {"torque_nm": 162.4, "temperature_c": 55.0, "vibration_mms": 2.1, "operating_hours": 3000, "load_kg": 7.0},
        "elbow":    {"torque_nm": 45.0,  "temperature_c": 44.0, "vibration_mms": 1.2, "operating_hours": 3000, "load_kg": 7.0},
        "wrist":    {"torque_nm": 20.0,  "temperature_c": 41.0, "vibration_mms": 1.0, "operating_hours": 3000, "load_kg": 7.0}
    }
    result_4 = monitor.evaluate_arm("Arm-6", arm_critical_readings)
    print(f"Target: Arm-6")
    print(f"Telemetries: Shoulder torque spiked to 162.4 Nm (Hard Limit: 140.0 Nm) — Jam / Collision Event")
    print(f"FINAL DECISION: {format_decision_banner(result_4['final_decision'])}")
    print(f"Trigger:        {result_4['trigger']}")
    print(f"Rationale:      {result_4['summary']}")
    print(f"Action:         {result_4['action_required']}")

    # =========================================================================
    # SCENARIO 5: Spoofed-Sensor Attack Detected & Defended
    # =========================================================================
    print_separator("Scenario 5: Spoofed-Sensor Cyber Attack Defended")
    print("Attack Vector: An attacker tampers with the edge telemetry, falsifying shoulder torque to 18.0 Nm")
    print("              to pretend the joint is running cool & free, while physical friction has driven")
    print("              joint temperature to 82.5°C with severe 7.1 mm/s bearing chatter vibration.")
    
    spoofed_readings = {
        "shoulder": {
            "torque_nm": 18.0,       # FAKE NOMINAL VALUE INJECTED BY ATTACKER
            "temperature_c": 82.5,   # REAL PHYSICAL HEAT (Near thermal threshold)
            "vibration_mms": 7.10,   # REAL CHATTER VIBRATION
            "operating_hours": 8900,
            "load_kg": 7.5
        },
        "elbow":    {"torque_nm": 42.0, "temperature_c": 43.0, "vibration_mms": 1.1, "operating_hours": 8900, "load_kg": 7.5},
        "wrist":    {"torque_nm": 19.0, "temperature_c": 39.0, "vibration_mms": 0.9, "operating_hours": 8900, "load_kg": 7.5}
    }
    result_5 = monitor.evaluate_arm("Arm-7", spoofed_readings)
    print(f"\nTarget: Arm-7")
    print(f"Reported: Shoulder torque = {spoofed_readings['shoulder']['torque_nm']} Nm (Falsified!)")
    print(f"FINAL DECISION: {format_decision_banner(result_5['final_decision'])}")
    print(f"Trigger:        {result_5['trigger']}")
    print(f"Spoof Defense:  {result_5['spoof_defense']['alert']}")
    print(f"Action:         {result_5['action_required']}")

    print_separator("SUMMARY OF RESULTS")
    all_decisions = [result_1['final_decision'], result_2['final_decision'], result_3['final_decision'], result_4['final_decision']]
    print(f"Reachable Decisions Verified: {set(all_decisions)}")
    assert "SAFE" in all_decisions, "SAFE outcome was not reached!"
    assert "MONITOR" in all_decisions, "MONITOR outcome was not reached!"
    assert "SCHEDULE_MAINTENANCE" in all_decisions, "SCHEDULE_MAINTENANCE outcome was not reached!"
    assert "EMERGENCY_STOP" in all_decisions, "EMERGENCY_STOP outcome was not reached!"
    print("All 4 target decisions successfully demonstrated and validated!\n")

if __name__ == "__main__":
    main()
