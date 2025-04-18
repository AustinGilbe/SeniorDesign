import csv
import os
import numpy as np
from datetime import datetime, timedelta

# Simulation parameters
DAYS = 1
HOURS_PER_DAY = 24
TESLA_CHARGING_HOURS = [11, 12, 13, 18, 19]
BATTERY_CAPACITY = 7.0
BATTERY_DISCHARGE_RATE = 2.0
TESLA_CHARGE_KW = 7.7
HOME_BASE_LOAD = 1.5

ATTACK_TYPES = ["clean", "mitm", "dos", "bd", "gm"]

def solar_generation(hour):
    max_solar_output = 6.5
    if 6 <= hour <= 18:
        # Scale to π from 6 AM to 6 PM (12-hour daylight window)
        return max_solar_output * np.sin(np.pi * (hour - 6) / 12)
    else:
        return 0.0  # Nighttime

def apply_attack(attack_type, data_entry, hour):
    if attack_type == "mitm":
        # MITM strictly alters solar data in impossible ways (night solar) and makes inconsistent battery readings
        if 0 <= hour <= 5 or 20 <= hour <= 23:  # Night hours
            # Add impossible solar generation at night
            data_entry[1] = np.random.uniform(1.5, 3.0)
        else:
            # Alter daytime solar by random factors
            data_entry[1] *= np.random.uniform(0.6, 1.4)
        
        # Erratic battery behavior - inconsistent with energy equations
        data_entry[4] = data_entry[4] * np.random.uniform(0.7, 1.3)

    elif attack_type == "dos":
        # DoS strictly removes data points or zeros critical values
        if 10 <= hour <= 14 or 18 <= hour <= 20:
            # Higher chance of complete data loss during peak hours
            if np.random.rand() < 0.8:
                return None
        
        # Sometimes zero out critical values
        if np.random.rand() < 0.3:
            data_entry[1] = 0.0  # Solar
            data_entry[4] = 0.0  # Battery

    elif attack_type == "bd":  # Battery Drain
        # Always force high home load and constant Tesla charging
        data_entry[2] = HOME_BASE_LOAD + np.random.uniform(2.0, 3.5)  # High home load
        data_entry[3] = TESLA_CHARGE_KW  # Always charging Tesla
        
        # Battery depletes faster
        data_entry[4] = max(0.5, data_entry[4] - np.random.uniform(0.5, 1.0))

    elif attack_type == "gm":  # Grid Manipulation
        # Always create grid anomalies - either negative values or very high values
        if np.random.rand() < 0.5:
            # Impossible negative grid import values
            data_entry[6] = -np.random.uniform(1.0, 5.0)
        else:
            # Abnormally high grid values
            multiplier = np.random.uniform(3.0, 8.0)
            if np.random.rand() < 0.5:
                data_entry[6] *= multiplier  # Import
            else:
                data_entry[7] *= multiplier  # Export

    return data_entry

# Ensure output directory exists
os.makedirs("./Data2/Logs", exist_ok=True)

# Run simulation for each attack type, 10 times each
for attack_type in ATTACK_TYPES:
    for i in range(10):
        start_time = datetime(2025, 4, 1, 0, 0, 0)
        battery_level = 3.5
        data = []

        for day in range(DAYS):
            for hour in range(HOURS_PER_DAY):
                timestamp = start_time + timedelta(hours=day * 24 + hour)
                solar_kW = solar_generation(hour)
                home_kW = HOME_BASE_LOAD + np.random.uniform(-0.2, 0.2)
                tesla_kW = TESLA_CHARGE_KW if hour in TESLA_CHARGING_HOURS else 0.0

                charge_power = 0.0
                if solar_kW > (home_kW + tesla_kW):
                    charge_power = min(solar_kW - home_kW - tesla_kW, BATTERY_CAPACITY - battery_level)
                    battery_level += charge_power
                    battery_discharge_kW = 0.0
                else:
                    needed_power = home_kW + tesla_kW - solar_kW
                    battery_discharge_kW = min(needed_power, battery_level, BATTERY_DISCHARGE_RATE)
                    battery_level -= battery_discharge_kW
                    needed_power -= battery_discharge_kW

                grid_import_kW = max(0, needed_power)
                grid_export_kW = max(0, solar_kW - home_kW - tesla_kW - (battery_level - charge_power))

                data_entry = [
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    round(solar_kW, 2),
                    round(home_kW, 2),
                    round(tesla_kW, 2),
                    round(battery_level, 2),
                    round(battery_discharge_kW, 2),
                    round(grid_import_kW, 2),
                    round(grid_export_kW, 2)
                ]

                modified_entry = apply_attack(attack_type, data_entry, hour)
                if modified_entry:
                    data.append(modified_entry)

        # Write to CSV with a numbered suffix
        filename = f"./Data2/Logs/{attack_type}/{attack_type}_simulation_log_{i+1}.csv"
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Solar_Generation_kW", "Home_Load_kW", "Tesla_Charger_kW", "Battery_Charge_kWh", "Battery_Discharge_kW", "Grid_Import_kW", "Grid_Export_kW"])
            writer.writerows(data)

        print(f"[✓] Log saved: {filename}")

