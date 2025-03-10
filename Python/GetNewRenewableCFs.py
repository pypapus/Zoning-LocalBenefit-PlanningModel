import os, copy, datetime, pandas as pd, datetime as dt, numpy as np
from os import path
from netCDF4 import Dataset
from GetRenewableCFs import *
from GetSitesForCE import *
from SetupTransmissionAndZones import importCountysubs, importPRegions, importCounty
from GetEconomicImpacts import *

# # Define power density values and filtering parameters
# power_densities = {
#     'wind': 2,
#     'solar': 20
# }

# re = 'solar'  # Change to 'Solar' if needed
# reTypeScenario = 'Solar'  # What re zoning ordinances are applied 'Solar' and 'wind'
# scenario_key = "scenario13"  # What types of ordinances
# Land_use = 'cultivated'

# tgtTz = 'EST'
# reSourceMERRA = False
# reDownFactor = 1
# reYear = 2012
# currYear = 2020
# siteLeastCap = 5  # MW

# # scenario_key = "scenario18e"  # What types of ordinances

# # Call scenariosites function for scenario13 with the chosen parameters
# jurisdiction = 'county'
# parcels = getParcels()
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# regions = getRegions(pRegionShapes, subdivShapes, counties)
# zoningData = getZoningdataSubdivs(regions) 

# genFleet = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\ResultsPropTax_scenario18e_S0_W0_EI_40560000_EIMs_all_costWgt_1.0\2025CO2Cap162\CE\genFleetForCE2025.csv')

# # sitestoFilter = {
# # ("scenario13", "wind"): 22,
# # ("scenario13", "solar"): 22,
# # ("scenario18e", "solar"): 9,
# # ("scenario21e", "solar"): 12,
# # }
# tracking = 1

# states = ['MN', 'WI', 'IL', 'MI', 'IN', 'OH']
     
# # sitestoFilter = {
# # ("scenario13", "wind"): 30,
# # ("scenario13", "solar"): 30,
# # ("scenario18e", "solar"): 16,
# # ("scenario21e", "solar"): 27,
# # } 

# sitestoFilter = 20
# tx_distance = 'all'



#Output: dfs of wind and solar generation (8760 dt rows, arbrary cols)
def getNewRenewableCFs(genFleet, tgtTz, reYear, currYear, reDownFactor, reSourceMERRA, 
                       scenario_key, reTypeScenario, Land_use, zoningData, parcels, regions,
                       power_densities, sitestoFilter,siteLeastCap, jurisdiction, tracking, pRegionShapes, states, 
                       startYear, endYear, yearStepCE, tx_distance):
    
    if currYear > 2050: currYear = 2050
    #Get list of wind / solar units in fleet
    windUnits, solarUnits = getREInFleet('Wind', genFleet), getREInFleet('Solar', genFleet)
    #Get list of wind / solar sites in region.
    #does not work with MERRA
    if reSourceMERRA: lats, lons, cf, latlonRegion = loadMerraData(reYear, pRegionShapes)
    else: cfbyRegion = loadNonMerraData(reYear, jurisdiction, tracking)
    solarCfs, maxCapSolar = calcNewCfs(solarUnits,cfbyRegion,'solar',currYear, scenario_key,reTypeScenario, Land_use, 
                                       zoningData,parcels,regions, jurisdiction, power_densities, sitestoFilter,siteLeastCap,states, 
                                       startYear, endYear, yearStepCE, tx_distance)
    windCfs, maxCapWind = calcNewCfs(windUnits,cfbyRegion,'wind',currYear, scenario_key, reTypeScenario, Land_use, 
                                     zoningData,parcels,regions, jurisdiction, power_densities, sitestoFilter,siteLeastCap,states, 
                                     startYear, endYear, yearStepCE, tx_distance)

    #Downscale if desired
    windCfs, solarCfs = windCfs[windCfs.columns[::reDownFactor]],solarCfs[solarCfs.columns[::reDownFactor]]
    #Shift to target timezone
    windCfs, solarCfs = shiftTznewCF(windCfs, tgtTz, currYear, 'wind'), shiftTznewCF(solarCfs, tgtTz, currYear, 'solar')
    newCfs = pd.concat([windCfs, solarCfs], axis=1)
    return newCfs, maxCapWind, maxCapSolar 

# cfs = pd.read_csv(r'E:\papa_yaw\EIM\Results_scenario18e_S0_W0_EI_40560000_EIMs_all_costWgt_1.0\2040CO2cap40\CE\windAndSolarNewCFsCE2040.csv', index_col=0)
# cfs = pd.read_csv(r'C:\Users\owusup\Desktop\Model\MacroCEM_EIM\Python\ResultspropTax_scenario18e_S0_W0_EI_40560000_EIMs_all_costWgt_1.0\2025CO2cap162\CE\windSolarNewCFsFullYr2025.csv', index_col=0)
# cfs= cfs.T
# # cfs = pd.read_csv(r'E:\papa_yaw\EIM\Results_scenario18e_S0_W0_EI_40560000_EIMs_all_costWgt_1.0\2025CO2Cap162\CE\windSolarNewCFsFullYr2025.csv', index_col=0)
# cfs['mean'] = cfs.mean(axis=1)
# cfs = cfs[['mean']].reset_index()
# cfs.reset_index(inplace=True)
# cfs['tech'] = cfs['index'].apply(lambda x: 'Solar' if 'solar' in x else ('Wind' if 'wind' in x else 'Unknown'))
# cfs_solar = cfs[cfs['tech']=='Solar']
# cfs_solar['lat'] = cfs_solar['index'].str.extract(r'lat([-\d.]+)').astype(float)
# cfs_solar['lon'] = cfs_solar['index'].str.extract(r'lon([-\d.]+)').astype(float)
# cfs_solar = cfs_solar.drop(columns=['index'])

# # import geopandas as gpd
# cfs_solar = gpd.GeoDataFrame(cfs_solar, geometry=gpd.points_from_xy(cfs_solar.lon, cfs_solar.lat))
# counties = gpd.GeoDataFrame(counties, geometry='geometry')

# cfs_solar_ = gpd.sjoin(cfs_solar, counties, how='right', op='intersects')
# #remove nan values in mean
# cfs_solar_ = cfs_solar_[cfs_solar_['mean'].notna()]
# cfs_solar__ = cfs_solar_[~(cfs_solar_['mean']==0)]

# #plot the mean
# import matplotlib.pyplot as plt
# plt.style.use('seaborn-white')
# # Plot of the mean capacity factor
# fig, ax = plt.subplots(figsize=(10, 10))  # Adjust these values to your preferred size
# cfs_solar__.plot(column='mean', 
#              cmap='viridis', 
#              legend=True,
#              linewidth=0.8, ax=ax)
# counties.boundary.plot(ax=ax, linewidth=0.8)
# plt.show()


# solarCfs = solarCfs.T
# solarCfs['mean'] = solarCfs.mean(axis=1)
# solarCfs = solarCfs[['mean']].reset_index()

# solarCfs['lat'] = solarCfs['time'].str.extract(r'lat([-\d.]+)').astype(float)
# solarCfs['lon'] = solarCfs['time'].str.extract(r'lon([-\d.]+)').astype(float)

# # Drop the original 'time' column
# solarCfs = solarCfs.drop(columns=['time'])

# import geopandas as gpd
# solarCfs = gpd.GeoDataFrame(solarCfs, geometry=gpd.points_from_xy(solarCfs.lon, solarCfs.lat))
# counties = gpd.GeoDataFrame(counties, geometry='geometry')

# #plot the mean
# import matplotlib.pyplot as plt
# plt.style.use('seaborn-white')
# # Plot of the mean capacity factor
# fig, ax = plt.subplots(figsize=(10, 10))  # Adjust these values to your preferred size
# solarCfs.plot(column='mean', 
#              cmap='OrRd', 
#              legend=True,
#              linewidth=0.8, ax=ax)
# counties.boundary.plot(ax=ax, linewidth=0.8)
# plt.show()



def calcNewCfs(existingSubdivCap, cfbyRegion, re, currYear, scenario_key, reTypeScenario, Land_use, 
               zoningData,parcels,regions, jurisdiction, power_densities, sitestoFilter,siteLeastCap,states, tx_distance,
               startYear, endYear, yearStepCE):
    if currYear > 2050: currYear = 2050

    #Get max available area for RE at location
    if re == 'wind': 
        maxCap = scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, "NoZoning", 
                                re,siteLeastCap, power_densities, sitestoFilter, states, tx_distance)
    elif re == 'solar':
        maxCap = scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, scenario_key, 
                                re,siteLeastCap, power_densities, sitestoFilter, states, tx_distance)
    
    # filter cfbyRegion to only include the regions of interest (filtering for subdivisions that are 2 miles of transmission lines)
    if jurisdiction == 'subdivision':
        distance_to_transmission = getDistancetoTransmission(tx_distance).reset_index()
        cfbyRegion[re] = cfbyRegion[re][cfbyRegion[re]['GEOID'].isin(distance_to_transmission['GEOID'].tolist())]    

    # make sure you have the capacity factor for each location you obtain from your site analysis
    maxCap = maxCap[maxCap['GEOID'].isin(cfbyRegion[re]['GEOID'].tolist())] 
    #make sure you have economic impacts for each location you obtain from your site analysis
    economicImpacts = getEconomicImpacts(jurisdiction, currYear)
    maxCap = maxCap[maxCap['GEOID'].isin(economicImpacts['GEOID'].tolist())]    
    #Get existing capacity at location (what is already built)
    # existingSubdivCap = existingSubdivCap[existingSubdivCap['YearAddedCE'].isin(range(startYear, endYear, yearStepCE))]
    existingUnits = existingSubdivCap.groupby('GEOID')['Capacity (MW)'].sum().reset_index()
    #Merge existing locations with new locations
    maxCap_update = pd.merge(existingUnits, maxCap, on='GEOID', how='right')
    # If for a location, the existing capacity is greater than the max capacity for that location, set the new available capacity of the location to 0
    # If the existing capacity is less than the max capacity for that location, set the new available capacity of the location to the difference between the max capacity and the existing capacity
    maxCap_update['Capacity (MW)'] = (maxCap_update['Capacity (MW)_y'] - maxCap_update['Capacity (MW)_x']).clip(0)
    maxCap_update['Capacity (MW)'] = maxCap_update['Capacity (MW)'].fillna(maxCap_update['Capacity (MW)_y'])
    maxCap_update = maxCap_update[['GEOID','Capacity (MW)']]
    #remove rows with 0 capacity
    # maxCap_update = maxCap_update[maxCap_update['Capacity (MW)'] > 0]
    #filter cfbyRegion to only include the regions of interest
    cfbyRegion[re] = cfbyRegion[re][cfbyRegion[re]['GEOID'].isin(maxCap_update['GEOID'].tolist())]
    #sort in order of maxCap_update
    cfbyRegion[re] = cfbyRegion[re].merge(maxCap_update, on='GEOID').sort_values('GEOID', ascending=True).reset_index(drop=True)
   
    # format the cfs     
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
    #Add dt and set to Dataframe
    idx = pd.date_range('1/1/' + str(currYear) + ' 0:00','12/31/' + str(currYear) + ' 23:00', freq='H')
    idx = idx.drop(idx[(idx.month == 2) & (idx.day == 29)])
    cfs = pd.DataFrame(cfs, index=idx, columns=col_names)
    cfs.columns.names = ['time']
    return cfs, maxCap_update

#shift tz (MERRA in UTC)
def shiftTznewCF(reGen,tz,yr,reType):
    origIdx = reGen.index
    tzOffsetDict = {'PST':-7,'CST': -6,'EST': -5}
    reGen.index = reGen.index.shift(tzOffsetDict[tz],freq='H')
    reGen = reGen[reGen.index.year==yr]
    reGen = reGen.append(reGen.iloc[[-1]*abs(tzOffsetDict[tz])],ignore_index=True)
    if reType=='solar': reGen.iloc[-5:] = 0 #set nighttime hours to 0
    # Set all values less than 0.1 to 0
    # reGen[reGen < 0.1] = 0
    reGen.index=origIdx
    return reGen



# cols = ['GEOID'] + [str(x) for x in range(0,8759)]
# cfbyRegion[re] = cfbyRegion[re][cols].set_index('GEOID')
# transposed = cfbyRegion[re].T 
# cfbyRegion[re]['mean'] = transposed.mean()
# cfbyRegion[re] = cfbyRegion[re][['mean']].reset_index()


# counties = importCounty().to_crs(epsg=4326)

# counties = counties.merge(cfbyRegion[re], left_on='CNTY_GEOID', right_on='GEOID')


# import matplotlib.pyplot as plt
# plt.style.use('seaborn-white')
# # Plot of the mean capacity factor
# fig, ax = plt.subplots(figsize=(10, 10))  # Adjust these values to your preferred size
# counties.plot(column='mean', 
#              cmap='OrRd', 
#              legend=True,
#              linewidth=0.8, ax=ax)
# plt.show()




