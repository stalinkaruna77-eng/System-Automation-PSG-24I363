# Robotic Arm Joint Health Monitoring System
**Course:** 23IF02 · System Automation — Bonus Challenge  
**Target Environment:** 6-Axis Robotic Arms (Shoulder, Elbow, Wrist Monitoring)  

---

## 1. System Overview & Architecture

This repository delivers an automated, defense-in-depth condition monitoring and predictive maintenance system for a fleet of 6-axis articulated industrial robotic arms. The system monitors **joint torque** ($\text{Nm}$), **joint temperature** ($^\circ\text{C}$), and **vibration** ($\text{mm/s RMS}$) across the primary load-bearing joints (**Shoulder**, **Elbow**, and **Wrist**).

### High-Level Decision Flow
```
                     [Raw Joint Sensor Readings]
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │  Stage 1: Hardware Safety Interlock (Deterministic)    │
      └───────────────────────────┬────────────────────────────┘
                                  │
                 Is Hard Threshold Violated?
                                 / \
                                /   \
                        YES    /     \    NO
                              ▼       ▼
              [EMERGENCY_STOP]   ┌─────────────────────────────────────────┐
                                 │ Stage 2: Spoofed-Sensor Defense Engine  │
                                 └────────────────────┬────────────────────┘
                                                      │
                                           Is Spoofing Detected?
                                                    / \
                                            YES    /   \    NO
                                                  /     \
                          Is Thermal/Vib Severe?         ▼
                                 / \         ┌───────────────────────────────┐
                          YES   /   \   NO   │ Stage 3 & 4: Multi-Signal     │
                               ▼     ▼       │ ML Model & Log Fusion Engine  │
               [EMERGENCY_STOP]  [SCHEDULE_  └───────────────┬───────────────┘
                                  MAINTENANCE]                │
                                                              ▼
                                            ┌───────────────────────────────────┐
                                            │ Final Decision Matrix:            │
                                            │ • Severe Wear / Critical Log      │
                                            │     -> SCHEDULE_MAINTENANCE       │
                                            │ • Moderate Wear / Warning Log     │
                                            │     -> MONITOR                    │
                                            │ • Nominal Health & Clean Log      │
                                            │     -> SAFE                       │
                                            └───────────────────────────────────┘
```

---

## 2. Technical Explanation & Design Rationale

### A. Safety Threshold Rationale for Immediate-Stop Check
The immediate safety check operates deterministically at Priority 0. Per safety standard **ISO 13849-1 (Safety-related parts of control systems)**, software ML inference latency or model hallucinations must never compromise machine emergency stop circuits.

* **Torque Thresholds (Joint-Specific):**
  * **Shoulder:** **$> 140.0\text{ Nm}$** (Nominal operating range: $50\text{--}80\text{ Nm}$, continuous rated maximum: $120\text{ Nm}$). Exceeding $140\text{ Nm}$ indicates an uncommanded tool collision, catastrophic payload overload, or drive train lockup.
  * **Elbow:** **$> 95.0\text{ Nm}$** (Nominal: $35\text{--}55\text{ Nm}$, rated maximum: $80\text{ Nm}$). Exceeding $95\text{ Nm}$ indicates mechanical binding or joint cross-axis seizure.
  * **Wrist:** **$> 45.0\text{ Nm}$** (Nominal: $15\text{--}25\text{ Nm}$, rated maximum: $35\text{ Nm}$). The wrist contains delicate planetary/harmonic reducers; loads above $45\text{ Nm}$ risk stripping teeth or bending end-effector flanges.
* **Thermal Threshold:** **$> 85.0^\circ\text{C}$ across all joints.** While motor copper windings tolerate Class F temperatures ($155^\circ\text{C}$), synthetic bearing greases and harmonic drive elastomeric seals degrade exponentially above $85^\circ\text{C}$, and high-flux NdFeB permanent magnets risk irreversible thermal demagnetization.
* **Vibration Threshold:** **$> 7.5\text{ mm/s RMS}$ (ISO 10816-3 Zone D).** In rotating machinery, vibration above $7.5\text{ mm/s}$ corresponds to severe structural damage territory (bearing cage disintegration, rotor imbalance, or loose mounting bolts) requiring immediate shutdown before structural fracture occurs.

---

### B. Signal Fusion: Combining ML Predictions & Maintenance Logs
The decision engine fuses quantitative telemetry and unstructured human intelligence:

1. **Predictive Wear ML Model (`predictive_wear.py`):**
   * Supervised `RandomForestClassifier` trained on historical failure data (`joint_wear_history.csv`).
   * Evaluates multivariate degradation signatures across torque, operating hours, load, temperature, and vibration, outputting state probabilities and a continuous wear score ($0.0 \le \text{WearScore} \le 1.0$).
2. **Unstructured Maintenance Log NLP (`text_log_analyzer.py`):**
   * Parses free-text shift logs (`maintenance_notes.txt`).
   * Filters out irrelevant facility notes (e.g., paper towel replenishment, lunch breaks, camera dust cover cleaning).
   * Contextually extracts target arm IDs, affected joint names, and severity keywords with negation awareness (e.g., recognizing that *"no visible oil leakage"* is benign, whereas *"grease leakage spotted with metallic grinding"* is critical).
3. **Fusion Matrix:**
   $$\begin{array}{|c|c|c|}
   \hline
   \textbf{Predictive ML State} & \textbf{Technician Log Signal} & \textbf{Final Unified Decision} \\ \hline
   \text{Any} & \text{Any (Hard Limit Tripped)} & \mathbf{EMERGENCY\_STOP} \\ \hline
   \text{Any} & \text{Spoofed Sensor Detected} & \mathbf{SCHEDULE\_MAINTENANCE \text{ / } EMERGENCY\_STOP} \\ \hline
   \text{Failure (Wear} \ge 0.70\text{)} & \text{Any} & \mathbf{SCHEDULE\_MAINTENANCE} \\ \hline
   \text{Any} & \text{CRITICAL (e.g. grinding/backlash)} & \mathbf{SCHEDULE\_MAINTENANCE} \\ \hline
   \text{Warning (Wear} \ge 0.35\text{)} & \text{Any} & \mathbf{MONITOR} \\ \hline
   \text{Any} & \text{WARNING (e.g. clicking/warm)} & \mathbf{MONITOR} \\ \hline
   \text{Normal} & \text{NORMAL / NONE} & \mathbf{SAFE} \\ \hline
   \end{array}$$

---

### C. Spoofed-Sensor Defense: Mechanism, Capabilities & Limitations
The defense module (`spoof_detector.py`) guards against hostile or faulty edge transmitters falsifying joint-torque signals to disguise machine degradation.

#### 1. How It Works:
* **Electro-Mechanical Cross-Correlation Inconsistency:** Mechanical friction dissipates energy into heat and vibration:
  $$\Delta E_{\text{dissipated}} \propto \tau_{\text{friction}} \cdot \omega \implies \Delta T \uparrow \text{ and } V_{\text{RMS}} \uparrow$$
  If an adversary fakes a low or nominal torque (e.g., $18\text{ Nm}$) while bearing temperature exceeds $65\text{--}80^\circ\text{C}$ and vibration exceeds $4.5\text{ mm/s RMS}$, the system flags a physical impossibility: heat and acoustic vibration cannot exist without mechanical work or friction torque.
* **Gravitational Payload Inconsistency:** Newtonian statics dictates a minimum holding torque for a $6\text{--}8\text{ kg}$ tool at extension:
  $$\tau_{\text{shoulder}} \ge m_{\text{payload}} \cdot g \cdot r_{\text{lever}}$$
  Reporting $< 25\text{ Nm}$ under a $7.5\text{ kg}$ payload immediately triggers a payload physics violation.
* **Temporal Frozen Sensor / Replay Detection:** Real strain-gauge sensors exhibit micro-volts of analog-to-digital converter (ADC) quantization noise ($\sigma > 0.005$). Streaming identical static floats yields $\text{Var}(\tau) \to 0$, triggering a frozen signal alert.

#### 2. What Attacks It Catches:
* **Nominal-Masking Spoofing:** Suppressing reported torque to nominal baseline while the joint suffers mechanical friction or binding.
* **Zero-Variance / Freeze Replays:** Replaying previously recorded benign sensor frames.
* **Payload Under-Reporting:** Tampering with load-torque reporting to bypass payload rating limits.

#### 3. What Attacks It Would NOT Catch:
* **Full Multi-Sensor Synchronized Digital-Twin Spoofing:** If an advanced attacker compromises all three sensor channels (torque, temp, vibration) simultaneously and computes physically coupled synthetic data using a full dynamic simulation model.
* **Subtle Drift / Low-Amplitude Micro-Biases:** Small offsets ($\le 3\%$) that stay within natural sensor calibration tolerance envelopes.

---

## 3. Project Structure & Deliverables

```
Bonus-Challenge/
├── README.md                      # Comprehensive design document & submission report
├── generate_synthetic_data.py     # Generator for labeled historical sensor data
├── run_pipeline.py                # End-to-end runner demonstrating all 4 reachable outcomes
├── test_system.py                 # Automated unit & integration test suite (9 passing tests)
├── data/
│   ├── joint_wear_history.csv     # 120 synthetic historical joint wear records (Normal, Warning, Failure)
│   └── maintenance_notes.txt      # 9 free-text technician log entries (mix of relevant & irrelevant)
├── models/
│   └── joint_wear_model.pkl       # Trained ML predictive wear model artifact
└── src/
    ├── __init__.py
    ├── safety_interlock.py        # Req 1: Deterministic zero-latency emergency stop engine
    ├── predictive_wear.py         # Req 2: ML model training & inference engine
    ├── text_log_analyzer.py       # Req 3: Free-text NLP log analyzer with negation handling
    ├── spoof_detector.py          # Req 4: Physics-informed & cross-sensor spoof defense
    └── health_monitor.py          # Req 5: Multi-signal health decision fusion engine
```

---

## 4. Verification & How to Run

### Run All Unit and Integration Tests:
```bash
python test_system.py
```
*Expected Result:*
```
Ran 9 tests in 0.38s
OK
```

### Run the Complete End-to-End Pipeline Demonstration:
```bash
python run_pipeline.py
```
*Demonstrates all four required outcomes:*
* **Scenario 1:** Nominal Arm-2 $\to$ **`SAFE`**
* **Scenario 2:** Developing wear on Arm-1 $\to$ **`MONITOR`**
* **Scenario 3:** Degradation & grinding note on Arm-3 $\to$ **`SCHEDULE_MAINTENANCE`**
* **Scenario 4:** Hard safety torque spike on Arm-6 $\to$ **`EMERGENCY_STOP`**
* **Scenario 5:** Defends against spoofed torque attack on Arm-7 $\to$ **`EMERGENCY_STOP`**
