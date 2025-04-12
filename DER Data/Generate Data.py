import csv
import numpy as np
from datetime import datetime, timedelta

# Simulation parameters
DAYS = 1
HOURS_PER_DAY = 24
TESLA_CHARGING_HOURS = [11, 12, 13, 18, 19]  # Tesla charges during midday and evening
BATTERY_CAPACITY = 7.0  # kWh
BATTERY_DISCHARGE_RATE = 2.0  # Max discharge rate in kW
TESLA_CHARGE_KW = 7.7  # Tesla charger power draw
HOME_BASE_LOAD = 1.5  # kW

# Attack types
ATTACK_TYPES = ["clean", "mitm", "dos", "battery_drain", "grid_manipulation"]

def solar_generation(hour):
    peak_solar_hour = 13  # Solar peak at 1 PM
    max_solar_output = 6.5  # Max solar output in kW
    return max_solar_output * max(0, np.sin(np.pi * (hour - 6) / (peak_solar_hour - 6)))

def apply_attack(attack_type, data_entry):
    if attack_type == "mitm":
        data_entry[1] *= np.random.uniform(0.8, 1.2)  # Alter solar generation
        data_entry[4] *= np.random.uniform(0.8, 1.2)  # Alter battery charge level
    elif attack_type == "dos":
        if np.random.rand() < 0.2:  # 20% chance of missing data
            return None
    elif attack_type == "battery_drain":
        data_entry[2] += np.random.uniform(0.5, 1.0)  # Increase home load
        data_entry[3] += np.random.uniform(1.0, 2.0)  # Increase Tesla charger load
    elif attack_type == "grid_manipulation":
        data_entry[6] *= np.random.uniform(0.8, 1.2)  # Alter grid import values
        data_entry[7] *= np.random.uniform(0.8, 1.2)  # Alter grid export values
    return data_entry

# Select attack type
attack_type = "clean"  # Change this to any attack type from ATTACK_TYPES

start_time = datetime(2025, 4, 1, 0, 0, 0)
battery_level = 3.5  # Start battery at half capacity

data = []
for day in range(DAYS):
    for hour in range(HOURS_PER_DAY):
        timestamp = start_time + timedelta(hours=day * 24 + hour)
        solar_kW = solar_generation(hour)
        home_kW = HOME_BASE_LOAD + np.random.uniform(-0.5, 0.5)  # Small variation in home load
        tesla_kW = TESLA_CHARGE_KW if hour in TESLA_CHARGING_HOURS else 0.0
        
        # Battery charge/discharge logic
        charge_power = 0.0  # Initialize
        if solar_kW > (home_kW + tesla_kW):  # Excess solar -> charge battery
            charge_power = min(solar_kW - home_kW - tesla_kW, BATTERY_CAPACITY - battery_level)
            battery_level += charge_power
            battery_discharge_kW = 0.0
        else:  # Not enough solar -> discharge battery or import from grid
            needed_power = home_kW + tesla_kW - solar_kW
            battery_discharge_kW = min(needed_power, battery_level, BATTERY_DISCHARGE_RATE)
            battery_level -= battery_discharge_kW
            needed_power -= battery_discharge_kW
        
        grid_import_kW = max(0, needed_power)  # Import remaining power from grid
        grid_export_kW = max(0, solar_kW - home_kW - tesla_kW - (battery_level - charge_power))
        
        # Store log data
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
        
        # Apply attack if selected
        modified_entry = apply_attack(attack_type, data_entry)
        if modified_entry:
            data.append(modified_entry)

# Write to CSV file
with open("./DER Data/Logs/der_simulation_log.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Solar_Generation_kW", "Home_Load_kW", "Tesla_Charger_kW", "Battery_Charge_kWh", "Battery_Discharge_kW", "Grid_Import_kW", "Grid_Export_kW"])
    writer.writerows(data)

print(f"DER simulation log saved to der_simulation_log.csv with attack type: {attack_type}")
