import os, pandas as pd, numpy as np
from GetTransmissionCost import *
from GetSitesForCE import *
from GetRenewableCFs import *
from GetNewRenewableCFs import *

from ApplyZoningOrdinanceMod import *
from GetZoningDataParcelsRegions import *
from SetupTransmissionAndZones import importPRegions, importCountysubs, importCounty

# Set up main parameters

# scenario_key = "scenario13" #scenario_key = "scenario13" and "scenario18e" and "scenario21e"
# # re = ['solar','wind'] #re = 'solar' and 'wind'
# re = 'solar'
# tech = ['Solar','Wind']
# windPowerDensity = 2
# solarPowerDensity = 20
# reTypeScenario = 'Solar'# ['Solar', 'Wind'] #reTypeScenario = 'Solar' and 'Wind'
# Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'
# jurisdiction = 'county' #jurisdiction = 'subdivision' and 'county'
# parcels = getParcels()
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# regions = getRegions(pRegionShapes, subdivShapes, counties)
# zoningData = getZoningdataSubdivs(regions)
# siteLeastCap = 5 
# currYear = 2020
# reYear = 2012
# tgtTz = 'EST'
# reSourceMERRA = False
# reDownFactor =1
# tracking = 1

# power_densities = {
#     'wind': 2,
#     'solar': 20}
# states = ['MN', 'WI', 'IL', 'MI', 'IN', 'OH']

# sitestoFilter = 20
# tx_distance = 'all'
# tracking = 1

def getZoningLCOEScenarioCurrYear(scenario_key,currYear,tgtTz,re,reTypeScenario,Land_use,zoningData,parcels,regions,
                                  siteLeastCap, power_densities, sitestoFilter, states, tx_distance, tracking, reYear, jurisdiction):
    LCOE_inputs = getLCOEInputs(currYear,tech)
    #select resource points based on the results from zoning ordinance
    data = scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, scenario_key, 
            re, siteLeastCap, power_densities, sitestoFilter, states, tx_distance)
    #calculate LCOE_inputs for each resource point
    data['CAPEX ($/MW)'] = LCOE_inputs['CAPEX ($/MW)'][0]
    data['FOM ($/MW-yr)'] = LCOE_inputs['FOM ($/MW-yr)'][0]
    data['CRF']= LCOE_inputs['CRF'][0]
    data['Discount rate']= LCOE_inputs['Discount rate'][0]
    data['Lifetime']= LCOE_inputs['Lifetime'][0]
    #include the cost of transmission for each resource point
    txCost = getTransCost(currYear, jurisdiction)
    data = pd.merge(data, txCost, left_on='GEOID', right_on='GEOID', how='inner')
    #calculate annual generation for each resource point
    cfbyRegion = loadNonMerraData(reYear, jurisdiction, tracking)

    cfbyRegion[re] = pd.merge(cfbyRegion[re], data[['GEOID', 'Capacity (MW)','STATEFP','PCA_Code']], left_on='GEOID', right_on='GEOID')
    
    reGeneration  = calcGeneration(cfbyRegion, re, currYear)
    reGeneration  = shiftTznewCF(reGeneration, tgtTz, currYear, re)
    #Sum each column to get total generation for each GEOID
    reGeneration  = reGeneration.sum(axis=0)
    reGeneration  = pd.DataFrame({'Annual Generation (MWh)': reGeneration }).reset_index()
    #Merge with LCOE_inputs
    data = pd.merge(data, reGeneration [['GEOID','Annual Generation (MWh)']], left_on='GEOID', right_on='GEOID')
    data= data[data['Capacity (MW)']>0]
    data = calcLCOE(data)
    # data = calcLCOT(data)
    data['Total LCOE ($/MWh)'] = data['LCOE ($/MWh)'] #+ data['LCOT ($/MWh)']
    data = data.drop(columns=['index'])
    return data

#put 0-8759 in columns
# cols = [str(i) for i in range(8760)]
# # find mean of cols
# cfbyRegion[re]['mean'] = cfbyRegion[re][cols].mean(axis=1)
# newcols = ['GEOID', 'CNTY_NAME', 'geometry', 'Center', 'lat', 'lon', 'mean']
# cfbyRegion[re] = cfbyRegion[re][newcols]
# cfbyRegion[re].drop(columns=['geometry'], inplace=True)
# #change to geodataframe
# import geopandas as gpd
# cfbyRegion[re] = pd.merge(cfbyRegion[re], counties, left_on='GEOID', right_on='CNTY_GEOID', how='inner')
# cfbyRegion[re] = gpd.GeoDataFrame(cfbyRegion[re], geometry=cfbyRegion[re]['geometry'])
# #plot mean
# cfbyRegion[re].plot(column='mean', legend=True)



def getLCOEInputs(currYear,re):
    LCOE_inputs = pd.read_excel(os.path.join('Data','LCOE_Data','Parameters.xlsx'))
    LCOE_inputs = LCOE_inputs.loc[(LCOE_inputs['Tech'] == re) & (LCOE_inputs['core_metric_variable'] == currYear)]
    LCOE_inputs['CAPEX ($/MW)'] = LCOE_inputs['CAPEX ($/kW)']*1000 
    LCOE_inputs['FOM ($/MW-yr)'] = LCOE_inputs['FOM ($/kW-yr)']*1000
    return LCOE_inputs.reset_index()

#calculate LCOE
def calcLCOE(re_data):
    re_data['CAPEX($/MW-yr)'] = re_data['CAPEX ($/MW)']*re_data['CRF']
    re_data['LCOE ($/MWh)'] = ((re_data['CAPEX($/MW-yr)'] + re_data['FOM ($/MW-yr)'] + re_data['Tx_Cost ($/MW-yr)'] ) * re_data['Capacity (MW)']) \
                                /re_data['Annual Generation (MWh)']
    return re_data

#calculate LCOT
def calcLCOT(re_data):
    re_data['LCOT ($/MWh)'] = (re_data['Tx_Cost ($/MW-yr)'] * re_data['Capacity (MW)'])/re_data['Annual Generation (MWh)']
    return re_data


def calcGeneration(cfbyRegion, re, currYear):
    #get the nameplate capacity of each resource point
    RE_nameplate = np.tile(cfbyRegion[re]['Capacity (MW)'].astype(float),(8760,1)) 
    #get the capacity factor of each resource point
    cf_entries = list(range(8760))
    cols = ['lat' ,'lon'] + [str(i) for i in cf_entries]
    cfs =  cfbyRegion[re][cols]
    cfs['lat_lon'] = cfs[['lat','lon']].apply(tuple, axis=1)
    cfs = cfs.drop(columns=['lat', 'lon'])
    cfs = cfs.T
    cols_row = cfs.iloc[-1].values
    cfs = cfs.iloc[:-1,:]
    #Rename columns in dataframe with lat/lon
    col_names = []
    for lat, lon in cols_row:
        col_names += [re+'lat'+str(lat)+'lon'+str(lon)]
    cfs.columns = col_names
    cfs = cfs.astype(float).to_numpy()

    #multiple the capacity factor by the name plate capacity
    RE_capacity = np.multiply(RE_nameplate, cfs)
    
    #hours (no leap day!)
    idx = pd.date_range('1/1/'+str(currYear)  + ' 0:00','12/31/' + str(currYear)  + ' 23:00',freq='H')
    idx = idx.drop(idx[(idx.month==2) & (idx.day ==29)])
    reGen = pd.DataFrame(RE_capacity,index=idx,columns=[col_names,
                                                        cfbyRegion[re]['PCA_Code'].values,
                                                        cfbyRegion[re]['STATEFP'].values,
                                                        cfbyRegion[re]['GEOID'].values])
                                                        
    reGen.columns.names = ['GAMS Symbol', 'region','state','GEOID']
    return reGen


#shift tz (MERRA in UTC)
def shiftTznewCF(reGen,tz,yr,reType):
    origIdx = reGen.index
    tzOffsetDict = {'PST':-7,'CST': -6,'EST': -5}
    reGen.index = reGen.index.shift(tzOffsetDict[tz],freq='H')
    reGen = reGen[reGen.index.year==yr]
    reGen = reGen.append(reGen.iloc[[-1]*abs(tzOffsetDict[tz])],ignore_index=True)
    if reType=='solar': reGen.iloc[-5:] = 0 #set nighttime hours to 0
    reGen.index=origIdx
    return reGen



sites = []

for re_type in re:
    if re_type == "solar": 
        tech = "Solar"
    else:
        tech = "Wind"
    data = getZoningLCOEScenarioCurrYear(scenario_key,currYear,tgtTz,re_type,reTypeScenario,Land_use,zoningData,parcels,regions,
                                  siteLeastCap, power_densities, sitestoFilter, states, tx_distance, tracking, reYear, jurisdiction)
    data = data[['GEOID','Total LCOE ($/MWh)']]
    data['Tech'] = re_type
    sites.append(data)

sites = pd.concat(sites)
#SAVE TO CSV
sites.to_csv(os.path.join('Data','LCOE_Data','LCOE_county_sites.csv'), index=False)






#################################################### PLOTS #################################################################

#sot by Total LCOE no grouping
def formatPlotLCOEDataAll(data):
    #Get data for each scenario
    data_all = data.copy()
    data_all.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    data_all.reset_index(drop=True, inplace=True)
    data_all['Cumulative Capacity (TW)'] = data_all['Capacity (MW)'].cumsum()/1000000
    data_all.reset_index(drop=True, inplace=True)
    new_row = data_all.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    data_all.loc[-1] = new_row
    data_all.index = data_all.index + 1
    data_all = data_all.sort_index()
    return data_all

#sort by LCOT no grouping
def formatPlotLCOEDataAll_LCOT(data):
    #Get data for each scenario
    data_all = data.copy()
    data_all.sort_values(by='LCOT ($/MWh)', inplace=True)
    data_all.reset_index(drop=True, inplace=True)
    data_all['Cumulative Capacity (TW)'] = data_all['Capacity (MW)'].cumsum()/1000000
    data_all.reset_index(drop=True, inplace=True)
    new_row = data_all.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    data_all.loc[-1] = new_row
    data_all.index = data_all.index + 1
    data_all = data_all.sort_index()
    return data_all

#sort by LCOE no grouping
def formatPlotLCOEDataAll_LCOE(data):
    #Get data for each scenario
    data_all = data.copy()
    data_all.sort_values(by='LCOE ($/MWh)', inplace=True)
    data_all.reset_index(drop=True, inplace=True)
    data_all['Cumulative Capacity (TW)'] = data_all['Capacity (MW)'].cumsum()/1000000
    data_all.reset_index(drop=True, inplace=True)
    new_row = data_all.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    data_all.loc[-1] = new_row
    data_all.index = data_all.index + 1
    data_all = data_all.sort_index()
    return data_all


#plot LCOE + LCOT by state
def formatPlotTotalLCOEDataState(data, id):
    #Format data by state
    state_data = data[data['STATEFP'] == id]
    state_data.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    state_data.reset_index(drop=True, inplace=True)
    state_data['Cumulative Capacity (TW)'] = state_data['Capacity (MW)'].cumsum()/1000000
    state_data.reset_index(drop=True, inplace=True)
    new_row = state_data.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    state_data.loc[-1] = new_row
    state_data.index = state_data.index + 1
    state_data = state_data.sort_index()
    return state_data


#plot LCOE + LCOT by region
def formatPlotTotalLCOEData2(data, id):
    #Format data by region
    pregion_data = data[data['PCA_Code'] == id]
    pregion_data.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    pregion_data['Cumulative Capacity (TW)'] = pregion_data['Capacity (MW)'].cumsum()/1000000
    pregion_data.reset_index(drop=True, inplace=True)
    new_row = pregion_data.iloc[0].copy()
    new_row['Cumulative Capacity (TW)'] = 0
    pregion_data.loc[-1] = new_row
    pregion_data.index = pregion_data.index + 1
    pregion_data = pregion_data.sort_index()
    return pregion_data


