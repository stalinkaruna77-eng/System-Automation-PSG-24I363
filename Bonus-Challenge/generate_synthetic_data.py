"""
Synthetic Dataset Generator for Robotic Arm Joint Wear & Failure Prediction
Course: 23IF02 System Automation — Bonus Challenge

Generates realistic historical sensor readings for 6-axis robotic arms
focusing on the 3 primary load-bearing joints: Shoulder, Elbow, and Wrist.
Outputs at least 50 labeled records (default: 120 samples across Normal, Warning, Failure).
"""

import os
import random
import pandas as pd
import numpy as np

def generate_joint_history_dataset(n_samples=120, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    joints = ["shoulder", "elbow", "wrist"]
    # Baseline nominal parameters per joint
    # Shoulder carries heaviest moment; wrist has highest precision & lower torque capacity.
    joint_specs = {
        "shoulder": {
            "torque_mean": 65.0, "torque_std": 8.0,
            "temp_mean": 48.0, "temp_std": 4.0,
            "vib_mean": 1.4, "vib_std": 0.3
        },
        "elbow": {
            "torque_mean": 42.0, "torque_std": 6.0,
            "temp_mean": 44.0, "temp_std": 3.5,
            "vib_mean": 1.2, "vib_std": 0.25
        },
        "wrist": {
            "torque_mean": 18.0, "torque_std": 3.0,
            "temp_mean": 40.0, "temp_std": 3.0,
            "vib_mean": 0.9, "vib_std": 0.2
        }
    }

    records = []
    
    # Generate balanced distribution: ~50% Normal, ~30% Warning (Moderate Wear), ~20% Failure (Severe Wear)
    states = ["Normal"] * int(n_samples * 0.50) + \
             ["Warning"] * int(n_samples * 0.30) + \
             ["Failure"] * (n_samples - int(n_samples * 0.50) - int(n_samples * 0.30))
    random.shuffle(states)

    for i, state in enumerate(states):
        arm_num = (i % 8) + 1
        arm_id = f"Arm-{arm_num}"
        joint = random.choice(joints)
        spec = joint_specs[joint]

        if state == "Normal":
            # Normal operating conditions
            torque = np.random.normal(spec["torque_mean"], spec["torque_std"])
            temp = np.random.normal(spec["temp_mean"], spec["temp_std"])
            vib = np.random.normal(spec["vib_mean"], spec["vib_std"])
            hours = random.randint(100, 3500)
            cycle_count = hours * random.randint(45, 60)
            load_kg = round(random.uniform(1.0, 7.0), 1)

        elif state == "Warning":
            # Developing wear: slight harmonic play, increased friction, higher thermal dissipation
            torque = np.random.normal(spec["torque_mean"] * 1.35, spec["torque_std"] * 1.2)
            temp = np.random.normal(spec["temp_mean"] + 18.0, spec["temp_std"] * 1.3)
            vib = np.random.normal(spec["vib_mean"] * 2.6, spec["vib_std"] * 1.4)
            hours = random.randint(4000, 8500)
            cycle_count = hours * random.randint(45, 60)
            load_kg = round(random.uniform(3.0, 8.5), 1)

        else: # Failure
            # Severe degradation: bearing galling, high friction torque, thermal runaway, chatter
            torque = np.random.normal(spec["torque_mean"] * 1.85, spec["torque_std"] * 1.5)
            temp = np.random.normal(spec["temp_mean"] + 36.0, spec["temp_std"] * 1.8)
            vib = np.random.normal(spec["vib_mean"] * 4.8, spec["vib_std"] * 1.6)
            hours = random.randint(8000, 15000)
            cycle_count = hours * random.randint(50, 65)
            load_kg = round(random.uniform(4.0, 10.0), 1)

        # Physical realistic clamps
        torque = max(5.0, round(float(torque), 2))
        temp = max(20.0, round(float(temp), 2))
        vib = max(0.2, round(float(vib), 2))

        records.append({
            "record_id": f"REC-{i+1:04d}",
            "arm_id": arm_id,
            "joint": joint,
            "torque_nm": torque,
            "temperature_c": temp,
            "vibration_mms": vib,
            "operating_hours": hours,
            "cycle_count": cycle_count,
            "load_kg": load_kg,
            "state": state
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "joint_wear_history.csv")

    df = generate_joint_history_dataset(n_samples=120)
    df.to_csv(out_file, index=False)
    print(f"Generated synthetic dataset with {len(df)} records at: {out_file}")
    print("\nClass breakdown:")
    print(df["state"].value_counts())
    print("\nSample records:")
    print(df.head(5))
