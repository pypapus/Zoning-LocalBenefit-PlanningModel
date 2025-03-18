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
    scenario_key_values = ['CurrentZoning']  # Example values for scenario_key
    costWgt_values = [1.0]  # Example values for costWgt


    # Loop through all combinations of values
    for interconn in interconn_values:
        for scenario_key in scenario_key_values:
            for costWgt in costWgt_values:
                # Call runMacroCEM with current combination of values
                runMacroCEM(interconn, scenario_key, costWgt)

if __name__ == "__main__":
    main()

