#Papa Yaw
#Date: 4/1/2024
#Add Installation, O&M, and Decommissioning impacts to new solar techs

import os, pandas as pd, numpy as np
from GetEconomicImpacts import *

# reTypeScenario = 'Solar'
# jurisdiction = 'county'
# currYear = 2025
# newTechsCE = pd.read_csv('C:\\Users\\owusup\\Desktop\\Model\\MacroCEM_EIM\\Python\\Results_scenario13_S0_W0_EI_270\\2025CO2Cap209\\CE\\newTechsCE2025.csv')

def addEItoNewTechs(newTechsCE, economicImpacts, reTypeScenario):
    newSolarTechs = newTechsCE.loc[newTechsCE['FuelType']==reTypeScenario]
    newSolarTechs = newSolarTechs.merge(economicImpacts, how='inner', on='GEOID')
    return newSolarTechs

def getEconomicImpacts(jurisdiction, currYear):
    file_path = os.path.join('Data', 'EIM_data')
    if jurisdiction == 'subdivision':
        file_path = os.path.join('Data', 'EIM_data', 'subdivisions')
        economicImpacts = pd.read_excel(os.path.join(file_path, str(currYear) + '.xlsx'))
        economicImpacts = economicImpacts.drop(columns=['COUSUB_NAME', 'STATEFP','COUNTYFP','FIPS',
                                                        'COUSUBFP','COUNTY_NAME','STATE'])
    elif jurisdiction == 'county':
        economicImpacts = pd.read_excel(os.path.join(file_path, 'county_impacts.xlsx'), sheet_name = str(currYear))
        economicImpacts =  economicImpacts.drop(columns=['STATEFP', 'COUNTYFP','COUNTY_NAME','STATE',
                                                        'GEOGRAPHY','State','County'])
    economicImpacts = economicImpacts.rename(columns = {'FIPS':'GEOID'})
    return economicImpacts
