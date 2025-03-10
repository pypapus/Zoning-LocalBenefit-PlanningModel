import sys
import os
import warnings
warnings.filterwarnings("ignore")
from MacroCEM_SBM import runMacroCEM

def main():
    # Set working directory to location of this script
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Define the range of values for each argument
    interconn_values = ["EI"]  # Example values for interconn
    timesteps_values = [2030] # Example values for timesteps
    co2Cap_values = [202800000]  # Example values for co2Cap
    reGenFracOfDemand_values = [5]  # Example values for solarGenFracOfDemand
    cleanGenFracOfDemand_values = [0]  # Example values for windGenFracOfDemand
    scenario_key_values = ['CurrentZoning']  # Example values for scenario_key
    scope_values = ["RE_Clean"] #Which economic impact to run, whether value-added, propoerty tax, or both
    tx_distance = ['SolarTxAll']  # Example value for tx_distance
    capex_discount_rate = [1.0]  # Example value for capex_discount_rate
    costWgt_values = [1.0]  # Example values for costWgt


    # Loop through all combinations of values
    for interconn in interconn_values:
        for timesteps in timesteps_values:
            for co2Cap in co2Cap_values:
                for reGenFracOfDemand in reGenFracOfDemand_values:
                    for cleanGenFracOfDemand in cleanGenFracOfDemand_values:
                        for scenario_key in scenario_key_values:
                            for scope in scope_values:
                                for tx_distance in tx_distance:
                                    for capex_discount in capex_discount_rate:
                                        for costWgt in costWgt_values:
                                            # Call runMacroCEM with current combination of values
                                            runMacroCEM(interconn, timesteps, co2Cap, reGenFracOfDemand, cleanGenFracOfDemand, scenario_key, scope, tx_distance, capex_discount, costWgt)

if __name__ == "__main__":
    main()
