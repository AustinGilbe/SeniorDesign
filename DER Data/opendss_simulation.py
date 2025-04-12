import dss

# Initialize OpenDSS
dss_engine = dss.DSS

# Create a new circuit
dss_engine.Text.Command = "Clear"
dss_engine.Text.Command = "New Circuit.MyCircuit BasekV=12.47 Phases=3 Bus1=SourceBus"

# Define a bus and add a voltage source
dss_engine.Text.Command = "New Vsource.Source Bus1=SourceBus BasekV=12.47 PU=1.0"

# Add a simple load
dss_engine.Text.Command = "New Load.MyLoad Bus1=SourceBus Phases=3 kW=150 PF=0.95"

# Solve the power flow
dss_engine.Text.Command = "Solve"

# Print total power
power = dss_engine.Circuit.TotalPower
print(f"Total Power: {power}")