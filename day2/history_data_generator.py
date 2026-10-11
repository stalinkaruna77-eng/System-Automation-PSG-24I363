import csv
import random
from pathlib import Path
Path("day2/data").mkdir(parents=True, exist_ok=True)
with open("day2/data/sensor_history.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "temperature", "pressure", "vibration",
        "rpm", "current", "state"
    ])
    for _ in range(50):
        temperature = round(random.uniform(20, 99), 1)
        pressure = round(random.uniform(3, 10), 2)
        vibration = round(random.uniform(2, 12), 1)
        rpm = round(random.uniform(1180, 1600), 1)
        current = round(random.uniform(5, 13), 1)
        if temperature >= 90 or pressure>=8.5 or vibration >= 10 or current >= 12:
            state = "Failure"
        elif temperature >= 65 or pressure >= 5.5 or vibration >= 7 or current >= 8:
            state = "Warning"
        else:
            state = "Normal"
        writer.writerow([
            temperature, pressure, vibration,
            rpm, current, state
        ])
print("sensor_history.csv generated successfully!")