# Script for running MacroCEM
# Order of inputs: interconn, co2cap, scenario_key, solarGenFracOfDemand, windGenFracOfDemand

import sys
import os
import warnings
from MacroCEM import runMacroCEM

# Suppress warnings
warnings.filterwarnings("ignore")

# Set the working directory to the location of this script
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Validate and process inputs
try:
    inputData = sys.argv[1:]  # Exclude the first item (script name)

    if len(inputData) < 10:
        raise ValueError("Insufficient arguments provided. Expected 10 arguments.")

    interconn = inputData[0]
    co2Cap = float(inputData[1])
    solarGenFracOfDemand = float(inputData[2])
    windGenFracOfDemand = float(inputData[3])
    scenario_key = inputData[4]
    economic_impacts = inputData[5]
    eim_measure = inputData[6]
    tx_distance = inputData[7]
    capex_discount_rate = float(inputData[8])
    costWgt = float(inputData[9]) if inputData[9].lower() != "none" else None

except ValueError as e:
    print(f"Error processing inputs: {e}")
    sys.exit(1)
except IndexError as e:
    print(f"Missing required input arguments: {e}")
    sys.exit(1)

# Log inputs for debugging
print(f"Inputs processed:\n"
      f"Interconnection: {interconn}\n"
      f"CO2 Cap: {co2Cap}\n"
      f"Solar Generation Fraction: {solarGenFracOfDemand}\n"
      f"Wind Generation Fraction: {windGenFracOfDemand}\n"
      f"Scenario Key: {scenario_key}\n"
      f"Economic Impacts: {economic_impacts}\n"
      f"EIM Measure: {eim_measure}\n"
      f"TX Distance: {tx_distance}\n"
      f"CAPEX Discount Rate: {capex_discount_rate}\n"
      f"Cost Weight: {costWgt}")

# Run the main function from MacroCEM
try:
    runMacroCEM(
        interconn,
        co2Cap,
        solarGenFracOfDemand,
        windGenFracOfDemand,
        scenario_key,
        economic_impacts,
        eim_measure,
        tx_distance,
        capex_discount_rate,
        costWgt
    )
except Exception as e:
    print(f"An error occurred while running MacroCEM: {e}")
    sys.exit(1)
