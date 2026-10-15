# Synthetic Data Generator
# Creates labeled joint wear readings (Normal, Warning, Failure) for the 3 arm joints

import os
import random
import pandas as pd
import numpy as np


def generate_joint_history_dataset(n_samples=120, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    joints = ["shoulder", "elbow", "wrist"]

    # Baseline sensor distributions for each joint
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

    # Distribution: 50% Normal, 30% Warning, 20% Failure
    states = (
        ["Normal"] * int(n_samples * 0.50) +
        ["Warning"] * int(n_samples * 0.30) +
        ["Failure"] * (n_samples - int(n_samples * 0.50) - int(n_samples * 0.30))
    )
    random.shuffle(states)

    for i, state in enumerate(states):
        arm_num = (i % 8) + 1
        arm_id = f"Arm-{arm_num}"
        joint = random.choice(joints)
        spec = joint_specs[joint]

        if state == "Normal":
            torque = np.random.normal(spec["torque_mean"], spec["torque_std"])
            temp = np.random.normal(spec["temp_mean"], spec["temp_std"])
            vib = np.random.normal(spec["vib_mean"], spec["vib_std"])
            hours = random.randint(100, 3500)
            cycle_count = hours * random.randint(45, 60)
            load_kg = round(random.uniform(1.0, 7.0), 1)

        elif state == "Warning":
            torque = np.random.normal(spec["torque_mean"] * 1.35, spec["torque_std"] * 1.2)
            temp = np.random.normal(spec["temp_mean"] + 18.0, spec["temp_std"] * 1.3)
            vib = np.random.normal(spec["vib_mean"] * 2.6, spec["vib_std"] * 1.4)
            hours = random.randint(4000, 8500)
            cycle_count = hours * random.randint(45, 60)
            load_kg = round(random.uniform(3.0, 8.5), 1)

        else:  # Failure
            torque = np.random.normal(spec["torque_mean"] * 1.85, spec["torque_std"] * 1.5)
            temp = np.random.normal(spec["temp_mean"] + 36.0, spec["temp_std"] * 1.8)
            vib = np.random.normal(spec["vib_mean"] * 4.8, spec["vib_std"] * 1.6)
            hours = random.randint(8000, 15000)
            cycle_count = hours * random.randint(50, 65)
            load_kg = round(random.uniform(4.0, 10.0), 1)

        # Realistic minimum bounds
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

    return pd.DataFrame(records)


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "joint_wear_history.csv")

    df = generate_joint_history_dataset(n_samples=120)
    df.to_csv(out_file, index=False)
    print(f"Generated {len(df)} records in {out_file}")
    print("\nClass distribution:")
    print(df["state"].value_counts())
