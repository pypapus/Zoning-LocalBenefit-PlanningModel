#Papa Yaw
#Nov 19, 2024
#Function to discount CAPEX for specific States

import os, pandas as pd

# Discount CAPEX based on State. some states have additional incentives for solar

def discountCapexForState(newTechsCE, statesToDiscountCost, currYear, capex_discount_rate):
    TechsToDiscount = ['Solar']
    if currYear > 2050:
        currYear = 2050
    discounted_states = newTechsCE['STATE'].isin(statesToDiscountCost) & newTechsCE['FuelType'].isin(TechsToDiscount)
    newTechsCE.loc[discounted_states, 'CAPEX(2012$/MW)'] *= (1 - capex_discount_rate)
    newTechsCE.loc[discounted_states, 'FOM(2012$/MW/yr)'] *= (1 - capex_discount_rate)
    return newTechsCE