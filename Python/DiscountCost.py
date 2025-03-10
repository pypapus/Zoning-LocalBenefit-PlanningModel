#Papa Yaw
#Nov 19, 2024
#Function to discount CAPEX for specific States

import os, pandas as pd

# Discount CAPEX based on State

def discountCapexForState(newTechsCE, statesToDiscountCost, currYear, capex_discount_rate):
    TechsToDiscount = ['Solar']
    # Cap the current year at 2050
    if currYear > 2050:
        currYear = 2050
    # # Filter rows for the states and techs that need CAPEX discounting
    # statefp = {'MN': 27, 'WI': 55, 'IL': 17, 'MI': 26, 'IN': 18, 'OH': 39}
    # #reverse the dictionary
    # statefp = {v: k for k, v in statefp.items()}
    # #create new column STATE BY MAPPING STATEFP TO STATE
    # newTechsCE['STATE'] = newTechsCE['STATEFP'].map(statefp)
    discounted_states = newTechsCE['STATE'].isin(statesToDiscountCost) & newTechsCE['FuelType'].isin(TechsToDiscount)
    # Apply the discount to CAPEX(2012$/MW) for the filtered rows
    newTechsCE.loc[discounted_states, 'CAPEX(2012$/MW)'] *= (1 - capex_discount_rate)
    newTechsCE.loc[discounted_states, 'FOM(2012$/MW/yr)'] *= (1 - capex_discount_rate)
    return newTechsCE