import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import pandas as pd
import os
from ApplyZoningOrdinanceMod import *
from GetRenewableCFs import *
from GetZoningDataParcelsRegions import *
from SetupTransmissionAndZones import importPRegions, importCountysubs, importCounty
###################################################################################################
# reYear = 2012
# currYear = 2020
# jurisdiction = 'subdivision'
# tracking = 'one_axis'
# scenario_key = "scenario18" 
# re = 'solar' #re = 'solar' and 'wind'
# windPowerDensity = 2
# solarPowerDensity = 20
# reTypeScenario = 'Solar' #reTypeScenario = 'Solar' and 'Wind'
# Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'
# jurisdiction = 'subdivision' #jurisdiction = 'subdivision' and 'county'
# parcels = getParcels()
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# regions = getRegions(pRegionShapes, subdivShapes, counties)
# zoningData = getZoningdataSubdivs(regions)
# siteLeastCap = 5        
# power_densities = {
#     'wind': 2,
#     'solar': 20}
# tgtTz = 'EST'
# reSourceMERRA = False
# re = 'solar'
# reDownFactor =1



# Define functions for getting zoning sites and LCOE
def scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, scenario_key, 
                  re, siteLeastCap, power_densities):
    allSites = scenarios[scenario_key](reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction).reset_index()
    lcoe = getLCOE(re)
    power_density = power_densities[re]
    
    # Check the jurisdiction and calculate capacity accordingly
    if jurisdiction not in ['county']:
        allSites['Capacity (MW)'] = (allSites['subdiv_area'] * power_density) / 1000000
        allSites = allSites.merge(lcoe, on='GEOID', how='inner')
        # Filter based on distance to transmission lines
        distance_to_transmission = getDistancetoTransmission()
        allSites = pd.merge(allSites, distance_to_transmission, on='GEOID', how='inner')
    else:
        allSites['Capacity (MW)'] = (allSites['county_area'] * power_density) / 1000000
    
    # Filter sites based on capacity
    allSites = allSites[allSites['Capacity (MW)'] >= siteLeastCap]
    return allSites

def getLCOE(re):
    lcoe = pd.read_csv(os.path.join('Data', 'LCOE_Data', 'LCOE_Sites.csv'), index_col=0)
    lcoe = lcoe[lcoe['Tech'] == re]
    return lcoe.reset_index()

def getDistancetoTransmission():
    distance_to_transmission = pd.read_csv(os.path.join('Data', 'Transmission_cost','Final','Distance_to_transmission.csv'), index_col=0)
    return distance_to_transmission

####################################################################################

# # Define functions for getting zoning sites and LCOE
# def scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, scenario_key, 
#                   re, siteLeastCap, power_densities, reYear, currYear, tgtTz, tracking):
#     allSites = scenarios[scenario_key](reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction).reset_index()
#     # lcoe = getLCOE(re)
#     LCOE_inputs = getLCOEInputs()
#     power_density = power_densities[re]
    
#     # Check the jurisdiction and calculate capacity accordingly
#     if jurisdiction not in ['county']:
#         allSites['Capacity (MW)'] = (allSites['subdiv_area'] * power_density) / 1000000
#     else:
#         allSites['Capacity (MW)'] = (allSites['county_area'] * power_density) / 1000000
    
#     # Filter sites based on capacity
#     allSites = allSites[allSites['Capacity (MW)'] >= siteLeastCap]

#     allSites['Total Capital Cost($)'] = allSites['Capacity (MW)']*LCOE_inputs['CAPEX ($/MW)'][0]
#     allSites['FOM($)'] = allSites['Capacity (MW)']*LCOE_inputs['FOM ($/MW-yr)'][0]
#     allSites['CRF']= LCOE_inputs['CRF'][0]
#     allSites['PFF'] = LCOE_inputs['PFF'][0]
#     allSites['CFF'] = LCOE_inputs['CFF'][0]
#     #calculate annual generation for each resource point
#     cfbyRegion = loadNonMerraData(reYear, jurisdiction, tracking)
#     cfbyRegion[re] = pd.merge(cfbyRegion[re], allSites[['GEOID', 'Capacity (MW)']], left_on='GEOID', right_on='GEOID')
#     solarGeneration = calcGeneration(cfbyRegion, re, currYear)

#     solarGeneration = shiftTznewCF(solarGeneration, tgtTz, currYear, re)
#     #Sum each column to get total generation for each GEOID
#     solarGeneration = solarGeneration.sum(axis=0)
#     solarGeneration = pd.DataFrame({'Annual Generation (MWh)': solarGeneration})
    
#     solarGeneration = solarGeneration.reset_index()
#     allSites = pd.merge(allSites, solarGeneration[['GEOID','Annual Generation (MWh)']], left_on='GEOID', right_on='GEOID')
#     allSites = getTransCost(allSites)
#     allSites= allSites[allSites['Capacity (MW)']>0]
#     allSites = calcLCOE(allSites)
#     allSites = calcLCOT(allSites)
#     allSites['Total LCOE 2 ($/MWh)'] = allSites['LCOE ($/MWh)'] + allSites['LCOT ($/MWh)']

#     return allSites





# ####################################################################################

# #read input coefficients for LCOE
# def getTransCosts():
#     transCosts = pd.read_csv(os.path.join('Data','Transmission_cost','Final',
#                                             'Subdiv_Transmission_Cost.csv'), index_col=0)
#     return transCosts

# def getLCOEInputs():
#     LCOE_inputs = pd.read_excel(os.path.join('Data','LCOE_Data','Parameters.xlsx'))
#     LCOE_inputs['CAPEX ($/MW)'] = LCOE_inputs['CAPEX ($/kW)']*1000 
#     LCOE_inputs['FOM ($/MW-yr)'] = LCOE_inputs['FOM ($/kW-yr)']*1000
#     return LCOE_inputs




#(LCOE+LCOT) by state
def SupplyCurvesbyState(data, id):
    #Format data by state
    state_data = data[data['STATEFP'] == id]
    state_data.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    state_data['Cumulative Capacity (GW)'] = state_data['Capacity (MW)'].cumsum()/1000
    state_data.reset_index(drop=True, inplace=True)
    new_row = state_data.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    state_data.loc[-1] = new_row
    state_data.index = state_data.index + 1
    state_data = state_data.sort_index()
    return state_data

#plot LCOE + LCOT by region
def SupplyCurvesbyRegion(data, id):
    #Format data by region
    pregion_data = data[data['PCA_Code'] == id]
    pregion_data.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    pregion_data['Cumulative Capacity (GW)'] = pregion_data['Capacity (MW)'].cumsum()/1000
    pregion_data.reset_index(drop=True, inplace=True)
    new_row = pregion_data.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    pregion_data.loc[-1] = new_row
    pregion_data.index = pregion_data.index + 1
    pregion_data = pregion_data.sort_index()
    return pregion_data

#plot LCOE + LCOT for the entire region
def SupplyCurvesTotal(data):
    total = data.copy()
    total.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    total['Cumulative Capacity (TW)'] = total['Capacity (MW)'].cumsum()/1000000
    total.reset_index(drop=True, inplace=True)
    new_row = total.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    total.loc[-1] = new_row
    total.index = total.index + 1
    total = total.sort_index()
    return total

# def calcGeneration(cfbyRegion, re, currYear):
#     #get the nameplate capacity of each resource point
#     RE_nameplate = np.tile(cfbyRegion[re]['Capacity (MW)'].astype(float),(8760,1)) 
#     #get the capacity factor of each resource point
#     cf_entries = list(range(8760))
#     cols = ['lat' ,'lon'] + [str(i) for i in cf_entries]
#     cfs =  cfbyRegion[re][cols]
#     cfs['lat_lon'] = cfs[['lat','lon']].apply(tuple, axis=1)
#     cfs = cfs.drop(columns=['lat', 'lon'])
#     cfs = cfs.T
#     cols_row = cfs.iloc[-1].values
#     cfs = cfs.iloc[:-1,:]
#     #Rename columns in dataframe with lat/lon
#     col_names = []
#     for lat, lon in cols_row:
#         col_names += [re+'lat'+str(lat)+'lon'+str(lon)]
#     cfs.columns = col_names
#     cfs = cfs.astype(float).to_numpy()

#     #multiple the capacity factor by the name plate capacity
#     RE_capacity = np.multiply(RE_nameplate, cfs)
    
#     #hours (no leap day!)
#     idx = pd.date_range('1/1/'+str(currYear)  + ' 0:00','12/31/' + str(currYear)  + ' 23:00',freq='H')
#     idx = idx.drop(idx[(idx.month==2) & (idx.day ==29)])
#     reGen = pd.DataFrame(RE_capacity,index=idx,columns=[col_names,
#                                                         cfbyRegion[re]['STATEFP'].values,
#                                                         cfbyRegion[re]['GEOID'].values])
                                                        
#     reGen.columns.names = ['GAMS Symbol','state','GEOID']
#     return reGen


# #shift tz (MERRA in UTC)
# def shiftTznewCF(reGen,tz,yr,reType):
#     origIdx = reGen.index
#     tzOffsetDict = {'PST':-7,'CST': -6,'EST': -5}
#     reGen.index = reGen.index.shift(tzOffsetDict[tz],freq='H')
#     reGen = reGen[reGen.index.year==yr]
#     reGen = reGen.append(reGen.iloc[[-1]*abs(tzOffsetDict[tz])],ignore_index=True)
#     if reType=='solar': reGen.iloc[-5:] = 0 #set nighttime hours to 0
#     reGen.index=origIdx
#     return reGen

# #calculate LCOE
# def calcLCOE(re_data):
#     # re_data['Annaulized CC($)'] = (re_data['Total Capital Cost($)']*re_data['CRF']*re_data['PFF']
#     #                               *(1+re_data['CRF'])**30)/((1+re_data['CRF'])**30-1)
#     re_data['Annaulized CC($)'] = re_data['Total Capital Cost($)']*re_data['CRF']
#     re_data['LCOE ($/MWh)'] = (re_data['Annaulized CC($)'] + re_data['FOM($)'])/(re_data['Annual Generation (MWh)'])
#     return re_data

# #calculate LCOE
# def calcLCOT(re_data):
#     re_data['LCOT ($/MWh)'] = (re_data['Trans Cost ($/MW-yr)'] * re_data['Capacity (MW)'])/re_data['Annual Generation (MWh)']
#     return re_data

# #get the least cost of transmission for each resource point
# def getTransCost(data):
#     AllTransCost = getTransCosts()
#     data = pd.merge(data, AllTransCost, left_on='GEOID', right_on='GEOID')
#     data['Trans Cost ($/MW-yr)'] = data.apply(find_min_cost, axis=1)
#     return data


# def find_min_cost(row):
#     if row['Capacity (MW)'] >= 0:
#         # create a list of the interconnection costs for the given capacity
#         costs = [row['<100'], row['100-161'], row['220-287'], row['345'], row['>500']]
#         return min(costs)
    
###################################################################################################

# #read demand data for 2050
# def get2050DemandData1():
#     demand_2050_mean, demand_2050_peak = get2050DemandData()
#     demand_2050_mean = demand_2050_mean*1000
#     demand_2050_peak = demand_2050_peak*1000
#     peak_byRegion_2050 = demand_2050_peak.copy()
#     peak_byRegion_2050.loc['peak'] = peak_byRegion_2050.max()
#     peak_byRegion_2050 = peak_byRegion_2050.loc[['peak'], :]
#     peak_byRegion_2050 = peak_byRegion_2050.reset_index(drop=True)
#     total_peak = peak_byRegion_2050.sum(axis=1)
#     return demand_2050_mean, demand_2050_peak, peak_byRegion_2050, total_peak

# #read demand data for 2020
# def get2020DemandData1():
#     demand_2020_mean, demand_2020_peak = get2020DemandData()
#     demand_2020_mean = demand_2020_mean*1000
#     demand_2020_peak = demand_2020_peak*1000
#     peak_byRegion_2020 = demand_2020_peak.copy()
#     peak_byRegion_2020.loc['peak'] = peak_byRegion_2020.max()
#     peak_byRegion_2020 = peak_byRegion_2020.loc[['peak'], :]
#     peak_byRegion_2020 = peak_byRegion_2020.reset_index(drop=True)
#     total_peak = peak_byRegion_2020.sum(axis=1)
#     return demand_2020_mean, demand_2020_peak, peak_byRegion_2020, total_peak
