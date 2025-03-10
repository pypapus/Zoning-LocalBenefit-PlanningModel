import os, copy, datetime, pandas as pd, geopandas as gpd, datetime as dt, numpy as np
from os import path
from statistics import mode
from netCDF4 import Dataset
#Does not work with MERRA

######################################################################################################
# genFleet = pd.read_csv('E:\\papa_yaw\\EIM\\Results_scenario18e_S0_W0_EI_40560000_EIMs_all_costWgt_1.0\\genFleetInitial.csv')
# reYear = 2012
# currYear = 2020
# reType = 'Solar'

# # # #load PCA regions - to be taken out since called in function 
# pRegionShapes = gpd.read_file(os.path.join('Data','REEDS','Shapefiles', 'PCAs.shp'))
# # pRegionShapes['centroid'] = pRegionShapes['geometry'].centroid

# from SetupTransmissionAndZones import importCountysubs, importCounty
# subdivShapes = importCountysubs()
# countyShapes = importCounty()

# tgtTz = 'EST'
# reSourceMERRA = False
# dataDir= os.path.join('Data','NSRDB') 
# yr = '2025'
# tracking = 1
# jurisdiction = 'county'

#################################################################################################33

#Output: dfs of wind and solar generation (8760 dt rows, arbitrary cols)
def getREGen(genFleet, tgtTz, reYear, currYear, reSourceMERRA, jurisdiction, tracking, pRegionShapes):
    if currYear > 2050: currYear = 2050
    #Get list of wind / solar sites in region #Does not work with MERRA
    if reSourceMERRA: lats,lons, cf, latlonRegion = loadMerraData(reYear, pRegionShapes)
    else: cfbyRegion = loadNonMerraData(reYear,jurisdiction,tracking)
    #Isolate wind & solar units
    windUnits, solarUnits = getREInFleet('Wind', genFleet),getREInFleet('Solar', genFleet)
    #get county or subdivision IDs  
    #Match to CFs
    cfWindUnits = getCFforFleet(windUnits, 'wind', cfbyRegion) 
    cfSolarUnits = getCFforFleet(solarUnits, 'solar', cfbyRegion) 
    #Get hourly generation (8760 x n df, n = num generators). Use given met year data but set dt index to currYear.
    windGen = get_hourly_RE_impl(windUnits,cfWindUnits, currYear)
    solarGen = get_hourly_RE_impl(solarUnits,cfSolarUnits, currYear)
    #Shift into right tz
    windGen, solarGen = shiftTz(windGen, tgtTz, currYear, 'wind'),shiftTz(solarGen, tgtTz, currYear, 'solar')
    #Combine by region and fill in missing regions with zeros
    windGenByRegion = windGen.groupby(level='region', axis=1).sum()
    solarGenByRegion = solarGen.groupby(level='region', axis=1).sum()
    #Combine capacity factors by region and fill in missing regions with zeros
    for genByRegion in [windGenByRegion, solarGenByRegion]:
        regionsNoGen = [r for r in genFleet['region'].unique() if r not in genByRegion.columns]
        for r in regionsNoGen: genByRegion[r] = 0
    return windGen, solarGen, windGenByRegion, solarGenByRegion


#Get solar and wind generation in existing fleet 
def getREInFleet(reType, genFleet):
    reUnits = genFleet.loc[genFleet['FuelType'] == reType]
    return reUnits

# Map solar units to capacity factors and retrieve structured numpy array for solar
def getCFforFleet(reUnits, reType, cfs):
    reUnits_mapped = pd.merge(reUnits, cfs[reType], how='left', left_on='GEOID', right_on='GEOID')
    reUnits_mapped = reUnits_mapped.round({'lat':4, 'lon':4})
    cols = list(range(8760))
    cols = [str(i) for i in cols]
    cfREUnits = reUnits_mapped[cols].to_numpy()
    return cfREUnits  

# Find expected hourly capacity for RE generators. Of shape (8760 hrs, num generators)
def get_hourly_RE_impl(reUnits, cfREUnits,yr):
    # combine summer and winter capacities
    RE_nameplate = np.tile(reUnits["Capacity (MW)"].astype(float),(8760,1)) #shape((8760, 211))
    RE_capacity = np.multiply(RE_nameplate, cfREUnits.T)
    #hours (no leap day!)
    yr = str(yr)
    idx = pd.date_range('1/1/'+yr + ' 0:00','12/31/' + yr + ' 23:00',freq='H')
    idx = idx.drop(idx[(idx.month==2) & (idx.day ==29)])
    reGen = pd.DataFrame(RE_capacity,index=idx,columns=[reUnits['GAMS Symbol'].values,
                                                        reUnits['region'].values,
                                                        reUnits['GEOID'].values])
    reGen.columns.names = ['GAMS Symbol','region','GEOID']
    return reGen

#shift tz (MERRA in UTC)
def shiftTz(reGen,tz,yr,reType):
    origIdx = reGen.index
    tzOffsetDict = {'PST':-7,'CST': -6,'EST': -5}
    reGen.index = reGen.index.shift(tzOffsetDict[tz],freq='H')
    reGen = reGen[reGen.index.year==yr]
    reGen = reGen.append([reGen.iloc[-1]]*abs(tzOffsetDict[tz]),ignore_index=True)
    if reType=='solar': reGen.iloc[-5:] = 0 #set nighttime hours to 0
    reGen.index=origIdx
    return reGen

  
# Get all necessary information from powGen netCDF files, VRE capacity factors and lat/lons
# Outputs: numpy arrays of lats and lons, and then a dictionary w/ wind and solar cfs
# as an np array of axbxc, where a/b/c = # lats/# longs/# hours in year
def loadMerraData(reYear, pRegionShapes, dataDir=os.path.join('Data','MERRA')):
    #File and dir
    solarFile, windFile = path.join(dataDir, str(reYear) + '_solar_generation_cf_US.nc'), path.join(dataDir, str(reYear) + '_wind_generation_cf_US.nc')
    # Error Handling
    if not (path.exists(solarFile) and path.exists(windFile)):
        error_message = 'Renewable Generation files not available:\n\t'+solarFile+'\n\t'+windFile
        raise RuntimeError(error_message)
    #Load data
    solarPowGen = Dataset(solarFile)
    windPowGen = Dataset(windFile) #assume solar and wind cover same geographic region

    #Get lat and lons for both datasets
    lats,lons = np.array(solarPowGen.variables['lat'][:]), np.array(solarPowGen.variables['lon'][:])
    latsPd = pd.DataFrame(lats, columns = ['lat'])
    lonsPd = pd.DataFrame(lons, columns=['lon'])

    latsAll = pd.Series(lats)
    lonsAll = pd.Series(lons)

    latlonList = [(i, j)
               for i in latsPd.lat
               for j in lonsPd.lon]

    latlonPd = pd.DataFrame(data=latlonList, columns=['lat', 'lon'])
    latlonGpd = gpd.GeoDataFrame(latlonPd, geometry=gpd.points_from_xy(latlonPd.lon, latlonPd.lat))
    latlonPshapeJoin = gpd.sjoin(latlonGpd, pRegionShapes, how="inner", op='intersects')
    latlonPshapeJoin = latlonPshapeJoin.sort_values(by=['lat', 'lon'])
    latlonPshapeJoin = latlonPshapeJoin.reset_index()

    latlonRegion = (pd.crosstab(latlonPshapeJoin['lat'],
                                 latlonPshapeJoin['lon']).reindex(index = latsAll,
                                                                    columns = lonsAll,fill_value=0))
    #Store data
    cf = dict()
    cf["solar"] = np.array(solarPowGen.variables['cf'][:])
    cf["wind"] = np.array(windPowGen.variables['cf'][:])
    solarPowGen.close(), windPowGen.close()

    # Error Handling
    if cf['solar'].shape != (lats.size, lons.size, 8760):
        print("powGen Error. Expected array of shape",lats.size,lons.size,8760,"Found:",cf['solar'].shape)
        return -1
    return lats,lons,cf,latlonRegion

# Get all necessary information from powGen netCDF files, VRE capacity factors and lat/lons
# Outputs: numpy arrays of lats and lons, and then a dictionary w/ wind and solar cfs
# as an np array of axbxc, where a/b/c = # lats/# longs/# hours in year
def loadNonMerraData(reYear, jurisdiction, tracking, dataDir= os.path.join('Data','NSRDB')):
    # File and dir
    #dataDir 
    if tracking == 1:
        location = path.join(dataDir, 'Oneaxis')
    else:
        location = path.join(dataDir, 'Fixed')
    if jurisdiction == 'county':
        solarFile, windFile = path.join(location, 'solar_cf_county_' + str(reYear) + '.csv'), path.join(location, 'wind_cf_county_' + str(reYear) + '.csv')
        # Error Handling
        if not (path.exists(solarFile) and path.exists(windFile)):
            error_message = 'Renewable Generation files not available:\n\t'+solarFile+'\n\t'+windFile
            raise RuntimeError(error_message)
    else:
        solarFile, windFile = path.join(location, 'solar_cf_subdivision_' + str(reYear) + '.csv'), path.join(location, 'wind_cf_subdivision_' + str(reYear) + '.csv')
        # Error Handling
        if not (path.exists(solarFile) and path.exists(windFile)):
            error_message = 'Renewable Generation files not available:\n\t'+solarFile+'\n\t'+windFile
            raise RuntimeError(error_message)
    # Load data
    solarPowGen = pd.read_csv(solarFile)
    windPowGen = pd.read_csv(windFile) #assume solar and wind cover same geographic region
    #remove row if it has a nan value
    solarPowGen = solarPowGen.dropna()
    windPowGen = windPowGen.dropna()
    # convert lat and lon to 4 decimal places
    # solarPowGen = solarPowGen.round({'lat':4, 'lon':4})
    # windPowGen = windPowGen.round({'lat':4, 'lon':4})

    cfbyregion = dict()
    cfbyregion ['solar'] = solarPowGen
    cfbyregion ['wind'] = windPowGen
    return cfbyregion
    
