#Get import zoning database and generate scenarios to run
import pandas as pd, os, numpy as np, geopandas as gpd
from SetupTransmissionAndZones import importCountysubs
from Supplycurves_func import *


subdivShapes = importCountysubs()
All_P = getZoningScenario("scenario13",reYear,currYear,tgtTz,re,reTypeScenario,Land_use,zoningData,parcels,regions)
subdivShapes = subdivShapes.merge(All_P, left_on='GEOID', right_on='GEOID')


#list column names for All_P
All_P.columns
subdivShapes.columns

#include state names
states = {39: 'Ohio', 55: 'Wisconsin', 17: 'Illinois', 18: 'Indiana', 27: 'Minnesota', 26: 'Michigan'}
subdivShapes['STATE'] = subdivShapes['STATEFP_x'].map(states)

#merge the values in the 'STATEFP_x' and 'COUNTYFP' columns
subdivShapes['county_geoid'] = subdivShapes['STATEFP_x'].astype(str) + subdivShapes['COUNTYFP'].astype(str)
subdivShapes['county_geoid'] = subdivShapes['county_geoid'].astype(int)

#select columns
subdivShapes = subdivShapes[['STATEFP_x','COUNTYFP','COUSUBFP','COUSUBNS','GEOID', 'NAME', 'STATE', 'county_geoid']]



#change the column name to county_name
subdivShapes = subdivShapes.rename(columns={'NAME':'CountySubdivision_name'})


def importCounty():
    file = os.listdir(os.path.join('Data','County'))
    path = [os.path.join('Data','County', i) for i in file if ".shp" in i]
    counties = gpd.GeoDataFrame(pd.concat([gpd.read_file(i) for i in path], 
                        ignore_index=True), crs=gpd.read_file(path[0]).crs)
    return counties


county = importCounty()
county['GEOID'] = county['GEOID'].astype(int)

subdivShapes2 = subdivShapes.merge(county, left_on='county_geoid', right_on='GEOID')
county = county.rename(columns={'NAME':'County_name'})

subdivShapes2.columns








#select columns
subdivShapes2.to_csv('subdivShapes2.csv')