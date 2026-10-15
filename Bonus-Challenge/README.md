# Bonus Challenge: Robotic Arm Joint Health Monitoring System

This project implements an automated health monitoring system for 6-axis robotic arms. It tracks torque, temperature, and vibration on the shoulder, elbow, and wrist joints, and combines sensor readings with technician maintenance notes to make decisions.

---

## Written Report

### 1. Safety Threshold Rationale for the Immediate-Stop Check
The immediate safety-stop operates as a hard deterministic check before running any machine learning model or text parsing. If a robotic arm experiences a collision or severe hardware failure, waiting for model inference or relying on an ML probability could lead to physical damage or safety hazards.

I selected the following limits based on typical robotic arm joint sizes and operating loads:
- **Torque limits (joint-specific):**
  - **Shoulder: 140 Nm** (Normal operation is around 50–80 Nm. The shoulder carries the entire arm and payload, but anything over 140 Nm indicates a collision, severe payload overload, or mechanical jam).
  - **Elbow: 95 Nm** (Normal range is 35–55 Nm. An elbow reading above 95 Nm points to gearbox binding or axis seizure).
  - **Wrist: 45 Nm** (Normal range is 15–25 Nm. The wrist uses smaller harmonic/planetary gears, so exceeding 45 Nm can shear gear teeth or damage the tool flange).
- **Temperature limit: 85°C across all joints** (Normal running temperature is 40–55°C. At temperatures above 85°C, joint lubricants thin out, seals can degrade, and motor magnets risk demagnetization).
- **Vibration limit: 7.5 mm/s RMS** (Nominal vibration is 1.0–2.0 mm/s. A reading above 7.5 mm/s indicates dangerous mechanical vibration such as bearing race fracture, loose mounting bolts, or severe gear wear).

### 2. Combining ML Predictions and Maintenance Logs
The decision engine fuses the quantitative sensor predictions with the qualitative technician notes:

1. **Predictive Wear Model:** A Random Forest classifier trained on labeled historical sensor data (`joint_wear_history.csv`) predicts whether each joint is `Normal`, `Warning`, or `Failure`, along with an overall continuous wear score (0.0 to 1.0).
2. **Technician Log Analyzer:** A text parsing module scans free-text entries in `maintenance_notes.txt`. It filters out general facility notes (like cleaning benches, paper towel refills, or camera dust cover checks) and searches for mentions of specific arms (e.g. `Arm-1`, `Arm-3`) and joint names. It checks for critical keywords (`grinding`, `leakage`, `backlash`, `excessively hot`) and warning keywords (`clicking`, `warm`, `chatter`), while accounting for common negations (e.g., *"no visible oil leakage"* is treated as normal, not a leak).

**Decision Combination Logic:**
- If the deterministic safety check trips $\rightarrow$ **`EMERGENCY_STOP`** (immediate priority).
- If a spoofed sensor is detected $\rightarrow$ **`SCHEDULE_MAINTENANCE`** (or **`EMERGENCY_STOP`** if temperature/vibration indicate danger).
- If the ML model predicts `Failure` OR the technician logged a `CRITICAL` issue $\rightarrow$ **`SCHEDULE_MAINTENANCE`**.
- If the ML model predicts `Warning` OR the technician logged a `WARNING` issue $\rightarrow$ **`MONITOR`**.
- If sensors are nominal and no issues are found in notes $\rightarrow$ **`SAFE`**.

### 3. Spoofed-Sensor Defense Mechanism
The spoofing defense catches situations where someone sends a fake low torque value to hide a failing joint or bypass safety rules.

- **How it works:**
  - **Physical Cross-Check (Torque vs. Temp & Vibration):** Mechanical friction inevitably turns into heat and vibration. If a joint reports very high temperature (>65–75°C) and heavy vibration (>4.5 mm/s), but reports a low/normal torque (e.g. 18 Nm on a shoulder), the readings are physically contradictory. The system flags this as a spoofed torque sensor.
  - **Payload Check:** A robotic arm holding a 7 kg payload at full reach must exert a minimum gravitational holding torque. Reporting near-zero torque under load triggers an anomaly.
  - **Frozen Signal Check:** Real analog sensors always have small fluctuations. If incoming torque values have zero variance across consecutive readings, it detects a frozen or replayed signal.
- **What it catches:**
  - An attacker overriding torque readings to look normal while the arm is overheating or vibrating heavily.
  - Replay attacks or stuck sensor values transmitting flatline numbers.
  - Mismatches between commanded payload and reported joint load.
- **What it would not catch:**
  - A sophisticated attacker who compromises all sensors simultaneously (torque, temperature, and vibration) and fakes a coordinated, physically plausible set of readings.
  - Small calibration errors or minor signal drifts that stay within normal operating tolerances.

---

## Project Structure

```
Bonus-Challenge/
├── README.md                  # Project documentation and report
├── generate_synthetic_data.py # Generates historical sensor dataset and trains the model
├── run_pipeline.py            # Demonstrates all 4 reachable states and spoof defense
├── test_system.py             # Unit tests for all modules
├── data/
│   ├── joint_wear_history.csv # 120 historical sensor readings with labels
│   └── maintenance_notes.txt  # Technician shift log (relevant and irrelevant notes)
├── models/
│   └── joint_wear_model.pkl   # Trained predictive model
└── src/
    ├── safety_interlock.py    # Hard limit immediate stop check
    ├── predictive_wear.py     # ML classifier for joint wear
    ├── text_log_analyzer.py   # Free-text technician log parser
    ├── spoof_detector.py      # Sensor cross-validation and spoof detection
    └── health_monitor.py      # Decision logic combining all signals
```

---

## How to Run

1. **Run the test suite:**
   ```bash
   python test_system.py
   ```

2. **Run the demonstration pipeline:**
   ```bash
   python run_pipeline.py
   ```
   This will run 5 scenarios demonstrating:
   - Scenario 1: Arm-2 $\rightarrow$ `SAFE`
   - Scenario 2: Arm-1 $\rightarrow$ `MONITOR`
   - Scenario 3: Arm-3 $\rightarrow$ `SCHEDULE_MAINTENANCE`
   - Scenario 4: Arm-6 $\rightarrow$ `EMERGENCY_STOP` (Safety interlock)
   - Scenario 5: Arm-7 $\rightarrow$ `EMERGENCY_STOP` (Spoofed torque attack detected)
