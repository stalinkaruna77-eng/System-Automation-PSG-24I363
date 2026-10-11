import csv
import os
import random
import time

LOG_FILE = "day1_log.txt"
CSV_FILE = "day2/data/rule_engine_data.csv"

# ---------------------------------------------------------------------------
# STEP 1 — Generate simulated sensor data
# ---------------------------------------------------------------------------
def generate_sensor_data():
    """Return a dict with at least 'temperature', 'pressure', 'vibration'."""
    # TODO: fill in realistic random values, e.g. temperature 50-95 (deg C)
    return {
        "temperature": random.randint(50,95),   # TODO
        "pressure": random.randint(20,100),      # TODO
        "vibration": round(random.uniform(0.1, 5.0), 2),     # TODO
        "current": round(random.uniform(5, 20), 2),
        "rpm": random.randint(1180, 1600),
    }
    # STRETCH GOAL (after the 8 steps below all work): real sensors aren't
    # perfectly clean. Try making one field randomly return None (a
    # dropout) or spike far outside its normal range every so often, then
    # update evaluate_rules() so a dropout doesn't crash your engine.
# ---------------------------------------------------------------------------
# STEP 2 — Write your first automation rules
# STEP 7 — Add a rule of your own (add another dict to this list)
# STEP 8 — Add one priority rule (lower "priority" number checked first)
# ---------------------------------------------------------------------------
RULES = [
    {
        "name": "HIGH_TEMP",
        "priority": 1,
        "condition": lambda r: r["temperature"] > 80,
        "action": "STOP_MACHINE"
    },
    {
        "name": "HIGH_PRESSURE",
        "priority": 2,
        "condition": lambda r: r["pressure"] > 35,
        "action": "REDUCE_PRESSURE"
    },
    {
        "name": "HIGH_VIBRATION",
        "priority": 3,
        "condition": lambda r: r["vibration"] > 4.0,
        "action": "CHECK_MACHINE"
    },
    {
    "name": "HIGH_CURRENT",
    "priority": 4,
    "condition": lambda r: r["current"] > 18,
    "action": "STOP_MACHINE"
    },
    {
    "name": "LOW_PRESSURE",
    "priority": 5,
    "condition": lambda r: r["pressure"] < 25,
    "action": "CHECK_MACHINE"
    },
    {
    "name": "CRITICAL_TEMP",
    "priority": 0,
    "condition": lambda r: r["temperature"] > 90,
    "action": "STOP_MACHINE"
    },
]
# ---------------------------------------------------------------------------
# STEP 3 — Detect machine state from the rules
# ---------------------------------------------------------------------------
def evaluate_rules(reading, rules):
    sorted_rules = sorted(rules, key=lambda rule: rule["priority"])
    for rule in sorted_rules:
        if rule["condition"](reading):
            return rule["name"], rule["action"]
    return "NO_RULE_FIRED", "CONTINUE_NORMAL"

# ---------------------------------------------------------------------------
# STEP 4 — Trigger an action when a rule fires
# ---------------------------------------------------------------------------
def take_action(action):
    """Return a human-readable string describing what happens for this action."""
    # TODO: map action names (e.g. "STOP_MACHINE") to a message
    actions = {
        "STOP_MACHINE": "Machine stopped due to high temperature.",
        "REDUCE_PRESSURE": "Reducing machine pressure.",
        "CHECK_MACHINE": "Machine inspection required due to high vibration.",
        "CONTINUE_NORMAL": "Machine operating normally."
    }

    return actions.get(action, f"(no handler yet for action: {action})")


# ---------------------------------------------------------------------------
# STEP 5 — Log every decision made
# ---------------------------------------------------------------------------
def log_decision(reading, rule_name, action):
    """Append one line to LOG_FILE with the reading, rule fired, and action."""
    # TODO: open(LOG_FILE, "a") and write a line
    with open(LOG_FILE, "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(
            f"{timestamp} | Reading: {reading} | "
            f"Rule: {rule_name} | Action: {action}\n"
        )

def log_csv(reading, rule_name):
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

    file_exists = os.path.exists(CSV_FILE)

    if rule_name in ("CRITICAL_TEMP", "HIGH_TEMP", "HIGH_CURRENT"):
        state = "Failure"
    elif rule_name in ("HIGH_PRESSURE", "HIGH_VIBRATION", "LOW_PRESSURE"):
        state = "Warning"
    else:
        state = "Normal"

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "temperature", "pressure", "vibration",
                "rpm", "current", "state"
            ])

        writer.writerow([
            reading["temperature"],
            reading["pressure"],
            reading["vibration"],
            reading["rpm"],
            reading["current"],
            state
        ])
# ---------------------------------------------------------------------------
# STEP 6 — Add a second sensor to the system
# TODO: add e.g. "current" to generate_sensor_data(), then use it in a rule
# ---------------------------------------------------------------------------


def main():
    for tick in range(1, 30):
        reading = generate_sensor_data()
        rule_name, action = evaluate_rules(reading, RULES)
        outcome = take_action(action)

        print(f"[Tick {tick:02d}] SENSE -> {reading}")
        print(f"           THINK -> {rule_name}")
        print(f"           ACT   -> {outcome}\n")

        log_decision(reading, rule_name, action)
        log_csv(reading, rule_name)
        time.sleep(0.2)


if __name__ == "__main__":
    main()