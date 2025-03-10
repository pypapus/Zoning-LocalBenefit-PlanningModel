#not used
import os, pandas as pd, numpy as np, matplotlib.pyplot as plt, sys
from GetTransmissionCost import *
from SetupTransmissionAndZones import importPRegions
from GetRenewableCFs import loadNonMerraData

currYear = 2050
reYear = 2012
# tgtTz = 'EST'
# re='solar'
resolution = 'county'


def getLCOEScenarioCurrYear(data,reYear,currYear,tgtTz,re, resolution):
    LCOE_inputs = getLCOEInputs(currYear)
    cfbyRegion = loadNonMerraData(reYear, resolution)
    #select resource points based on the results from zoning ordinance
    #calculate LCOE_inputs for each resource point
    data['CAPEX ($/MW)'] = LCOE_inputs['CAPEX ($/MW)'][0]
    # data['FOM($)'] = data['Capacity (MW)']*LCOE_inputs['FOM ($/MW-yr)'][0]
    data['FOM ($/MW-yr)'] = LCOE_inputs['FOM ($/MW-yr)'][0]
    data['CRF']= LCOE_inputs['CRF'][0]
    data['Discount rate']= LCOE_inputs['Discount rate'][0]
    data['Lifetime']= LCOE_inputs['Lifetime'][0]
    #include the cost of transmission for each resource point
    txCost = getTransCost(currYear)
    data = pd.merge(data, txCost, left_on='GEOID', right_on='GEOID')
    #calculate annual generation for each resource point
    cfbyRegion[re] = pd.merge(cfbyRegion[re], data[['GEOID', 'Capacity (MW)']], left_on='GEOID', right_on='GEOID')
    solarGeneration = calcGeneration(cfbyRegion, re, currYear)
    #Shift to target timezone
    solarGeneration = shiftTznewCF(solarGeneration, tgtTz, currYear, re)
    #Sum each column to get total generation for each GEOID
    solarGeneration = solarGeneration.sum(axis=0)
    solarGeneration = pd.DataFrame({'Annual Generation (MWh)': solarGeneration})
    #Merge with LCOE_inputs
    solarGeneration = solarGeneration.reset_index()
    data = pd.merge(data, solarGeneration[['GEOID','Annual Generation (MWh)','region', 'state']], left_on='GEOID', right_on='GEOID')
    data = calcLCOE(data)
    data = calcLCOT(data)
    data['Total LCOE ($/MWh)'] = data['LCOE ($/MWh)'] + data['LCOT ($/MWh)']
    return data

def getLCOEInputs(currYear):
    LCOE_inputs = pd.read_excel(os.path.join('Data','LCOE_Data','Parameters.xlsx'))
    LCOE_inputs = LCOE_inputs.loc[LCOE_inputs['core_metric_variable'] == currYear]
    LCOE_inputs['CAPEX ($/MW)'] = LCOE_inputs['CAPEX ($/kW)']*1000 
    LCOE_inputs['FOM ($/MW-yr)'] = LCOE_inputs['FOM ($/kW-yr)']*1000
    return LCOE_inputs.reset_index()

#calculate LCOE
def calcLCOE(re_data):
    re_data['CAPEX($/MW-yr)'] = re_data['CAPEX ($/MW)']*re_data['CRF']
    re_data['LCOE ($/MWh)'] = (re_data['CAPEX($/MW-yr)'] + re_data['FOM ($/MW-yr)']) * re_data['Capacity (MW)'] \
                                /(re_data['Annual Generation (MWh)'])
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


def formatPlotLCOEDataAll(data):
    #Get data for each scenario
    data_all = data.copy()
    data_all.sort_values(by='Total LCOE ($/MWh)', inplace=True)
    data_all.reset_index(drop=True, inplace=True)
    data_all['Cumulative Capacity (MW)'] = data_all['Capacity (MW)'].cumsum()
    data_all.reset_index(drop=True, inplace=True)
    new_row = data_all.iloc[0].copy()
    new_row['Cumulative Capacity (MW)'] = 0
    data_all.loc[-1] = new_row
    data_all.index = data_all.index + 1
    data_all = data_all.sort_index()
    return data_all
