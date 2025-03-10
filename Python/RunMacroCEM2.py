import sys
import os
import warnings
warnings.filterwarnings("ignore")
from MacroCEM import runMacroCEM

def main():
    # Set working directory to location of this script
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # Define the range of values for each argument
    interconn_values = ["EI"]  # Example values for interconn
    co2Cap_values = [32448000]  # Example values for co2Cap
    solarGenFracOfDemand_values = [0]  # Example values for solarGenFracOfDemand
    windGenFracOfDemand_values = [0]  # Example values for windGenFracOfDemand
    scenario_key_values = ['CurrentZoning']  # Example values for scenario_key
    economic_impacts_values = ["EIMs"]  # Example values for economic_impacts
    eim_measure = ["ValueAdded"] #Which economic impact to run, whether value-added, propoerty tax, or both
    tx_distance = ['SolarTxAll']  # Example value for tx_distance
    capex_discount_rate = [1.0]  # Example value for capex_discount_rate
    costWgt_values = [1.0]  # Example values for costWgt


    # Loop through all combinations of values
    for interconn in interconn_values:
        for co2Cap in co2Cap_values:
            for solarGenFracOfDemand in solarGenFracOfDemand_values:
                for windGenFracOfDemand in windGenFracOfDemand_values:
                    for scenario_key in scenario_key_values:
                        for economic_impacts in economic_impacts_values:
                            for eim in eim_measure:
                                for tx_distance in tx_distance:
                                    for capex_discount in capex_discount_rate:
                                        for costWgt in costWgt_values:
                                            # Call runMacroCEM with current combination of values
                                            runMacroCEM(interconn, co2Cap, solarGenFracOfDemand, windGenFracOfDemand, scenario_key, economic_impacts, eim, tx_distance, capex_discount, costWgt)

if __name__ == "__main__":
    main()

