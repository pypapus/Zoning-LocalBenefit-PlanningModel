import pandas as pd, geopandas as gpd, os
from SetupTransmissionAndZones import assignGensToPRegions, importPRegions, importCountysubs
from GetNewRenewableCFs import *
from GetTransmissionCost import *
import numpy as np
from ApplyZoningOrdinanceMod import *
from GetZoningDataParcelsRegions import *
from GetEconomicImpacts import *
# from GetRenewableCFs import jurisdict

################################################################################
# power_density = {
#     'wind': 2,
#     'solar': 20
# }
          
# re = 'solar'  
# reTypeScenario = 'Solar'  # What re zoning ordinances are applied 'Solar' and 'wind'
# scenario_key = "scenario18e"  # What types of ordinances
# Land_use = 'cultivated'

# tgtTz = 'EST'
# reSourceMERRA = False
# reDownFactor = 1
# reYear = 2012
# currYear = 2020
# siteLeastCap = 5  # MW

# scenario_key = "scenario18e"  # What types of ordinances

# jurisdiction = 'county'  # 'subdivision' and 'county'

# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# countyShapes = importCounty()

# # subdivShapes.crs = pRegionShapes.crs
# # countyShapes.crs = pRegionShapes.crs


# # newTechsCE = pd.read_csv('C:\\Users\\owusup\\Desktop\\Model\\MacroCEM\\Python\\newTechsCE.csv')
# sitestoFilter = 100

# newCfs = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\Results_scenario18e_S0_W0_EI_32448000_EIMs_all_costWgt_1.0\2025CO2Cap129\CE\windSolarNewCFs2025.csv', index_col=0)
# maxCapWind = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\Results_scenario18e_S0_W0_EI_32448000_EIMs_all_costWgt_1.0\2025CO2Cap129\CE\buildWindLimitsForCE2025.csv')
# maxCapSolar = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\Results_scenario18e_S0_W0_EI_32448000_EIMs_all_costWgt_1.0\2025CO2Cap129\CE\buildSolarLimitsForCE2025.csv')
# newTechsCE = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\Results_scenario18e_S0_W0_EI_32448000_EIMs_all_costWgt_1.0\2025CO2Cap129\CE\newTechsCE2025.csv')


##########################################################################################



def addWSSitesToNewTechs(newCfs,maxCapWind, maxCapSolar, newTechsCE,pRegionShapes,subdivShapes, countyShapes, reTypeScenario, currYear, jurisdiction):
    sitesDfList = list()
    #For wind & solar, repeat tech row for each potential site, then remove original row
    for l,f in zip(['wind','solar'],['Wind','Solar']):
        re = newTechsCE.loc[newTechsCE['FuelType']==f]
        sites = [c for c in newCfs if l in c]
        sitesDf = pd.concat([re]*len(sites),ignore_index=True) 
        sitesDf['PlantType'] = sites
        txt = sitesDf['PlantType'].str.split('lat',expand=True)[1]
        sitesDf[['Latitude','Longitude']] = txt.str.split('lon',expand=True).astype(float)
        newTechsCE.drop(re.index,inplace=True)
        sitesDfList.append(sitesDf)

    #Combine wind & solar rows into df, then map to regions & concat onto newTechsCE
    sitesDf = pd.concat(sitesDfList)
    sitesDf = sitesDf.drop('region',axis=1)
    sitesDf = assignGensToPRegions(sitesDf,pRegionShapes,subdivShapes,countyShapes,jurisdiction).reset_index(drop=True)
    
    #select wind and solar sites
    newSolarSitesDf = sitesDf[sitesDf['FuelType'] == reTypeScenario]
    newSolarSitesDf = newSolarSitesDf.drop_duplicates(subset=['GEOID'],keep='first').reset_index(drop=True)
    newWindSitesDf = sitesDf[sitesDf['FuelType'] != reTypeScenario]
    newWindSitesDf = newWindSitesDf.drop_duplicates(subset=['GEOID'],keep='first').reset_index(drop=True)

    #Update capacity 
    newSolarSitesDf.drop(['Capacity (MW)'], axis = 1, inplace=True)
    newWindSitesDf.drop(['Capacity (MW)'], axis = 1, inplace=True)
    newSolarSitesDf = pd.merge(newSolarSitesDf, maxCapSolar[['GEOID', 'Capacity (MW)']], 
                               left_on='GEOID', right_on='GEOID').reset_index(drop=True)
    newWindSitesDf = pd.merge(newWindSitesDf, maxCapWind[['GEOID', 'Capacity (MW)']], 
                              left_on='GEOID', right_on='GEOID').reset_index(drop=True) 
    
    #Include transmission costs for solar sites and wind sites
    trans_cost = getTransCost(currYear, jurisdiction)
    newSolarSitesDf = pd.merge(newSolarSitesDf, trans_cost, left_on='GEOID', right_on='GEOID')
    newWindSitesDf = pd.merge(newWindSitesDf, trans_cost, left_on='GEOID', right_on='GEOID')
    # Add economic impacts to newTechs
    economicImpacts = getEconomicImpacts(jurisdiction, currYear)
    newSolarSitesDf = addEItoNewTechs(newSolarSitesDf, economicImpacts, reTypeScenario)

    sitesDf = pd.concat([newSolarSitesDf, newWindSitesDf]).reset_index(drop=True)

    #Add new wind and solar sites to newtechs
    newTechsCE = pd.concat([newTechsCE,sitesDf],ignore_index=True)
    newTechsCE.reset_index(inplace=True,drop=True)
    #Create GAMS symbol as plant type + region
    newTechsCE['region'] = newTechsCE['region'].fillna(newTechsCE['PCA_Code'])
    newTechsCE['GAMS Symbol'] = newTechsCE['PlantType'] + newTechsCE['region']

    #Relabel new CF columns to match GAMS symbols (needed for GAMS model later)
    reRows = newTechsCE.loc[newTechsCE['ThermalOrRenewableOrStorage']=='renewable']
    reRows.index = reRows['PlantType']
    gamsDict = reRows['GAMS Symbol'].to_dict()
    newCfs = newCfs[[k for k in gamsDict]].rename(gamsDict,axis=1)
    return newTechsCE, newCfs, sitesDf