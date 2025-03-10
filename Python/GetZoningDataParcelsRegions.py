#Papa Yaw
#3/10/23

#Get import zoning database and generate scenarios to run
import pandas as pd, os, numpy as np, geopandas as gpd

# from SetupTransmissionAndZones import importPRegions, importCountysubs, importCounty
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()

###########################################################################################################################################################################
#Generated to import zoning database from website 
###########################################################################################################################################################################
def getZoningdata():
    zoningDir = os.path.join('Data','Zoning_database','Energy Zoning data download-aug-22-2024.csv')
    data = pd.read_csv(zoningDir, index_col=0)
    data = data.replace(' ',np.nan) #replace empty spaces with NaN
    ### NOTES FROM EMAIL WITH MADELEINE
    #Every township that is marked as county zoned (column J) should have no wind and solar specific data filled in, as that data "lives" in the county entry
    #The online database (the maps and data tab) automatically pulls solar and wind info from the county for all those townships/villages/cities that are county zoned.
    #With the database set up that way, there should not be county-zoned townships with data for wind and solar data in columns N onwards. Therefore, there should be no contradictory ordinances. 
    #ACTION: Take out all county-zoned townships, because data already exists in the county entry
    condition1 = data['Who Has Zoning Jurisdiction'].isin(['county','County'])
    condition2 = data['Jurisdiction Type'].isin(['Township','Village','City', 'Unincorporated'])
    data = data[~(condition1 & condition2)]
    ### NOTES FROM EMAIL WITH MADELEINE
    #Sometimes, these county entries are empty (blanks in J), and sometimes not. 
    #That depends on the following: If no place in a county is county-zoned, then we entered data into the local jurisdiction (township, city, village) profiles, and the county profile stays empty (e.g. Calhoun County in MI). 
    #But if some jurisdictions in a county ARE county-zoned, then there is information in the county profile (e.g. Cheboygan County in MI). 
    #ACTION: Take out all county entries that are empty (blanks in J).These are duplicates as the data is already in the local jurisdiction profiles.
    condition3 = data['Jurisdiction Type'].isin(['county','County'])
    condition4 = data['Who Has Zoning Jurisdiction'].isna()
    data = data[~(condition3 & condition4)]
    data['Jurisdiction 10-digit FIPS'].fillna(data['County FIPS'], inplace=True) 
    # #change data type to integer
    data['Jurisdiction 10-digit FIPS'] = pd.to_numeric(data['Jurisdiction 10-digit FIPS'], errors='coerce').astype('Int64')
    # townships_with_rules['Jurisdiction 10-digit FIPS'] = pd.to_numeric(townships_with_rules['Jurisdiction 10-digit FIPS'], errors='coerce').astype('Int64')
    return data #townships_with_rules

###########################################################################################################################################################################
# import regions
def getRegions(pRegionShapes, subdivShapes, counties):
    #set the crs of the subdivShapes and counties to match the PCA regions
    subdivShapes.crs = pRegionShapes.crs
    counties.crs = pRegionShapes.crs
    subdivShapes = gpd.GeoDataFrame(subdivShapes, geometry=gpd.points_from_xy(subdivShapes.COUNSUB_LON, subdivShapes.COUNSUB_LAT))
    geoidlatlonPCA1 = gpd.sjoin(subdivShapes, pRegionShapes, predicate='intersects').reset_index(drop=True).drop_duplicates(subset=['GEOID'])
    geoidlatlonPCA1 = geoidlatlonPCA1.drop(columns=['index_right'])
    geoidlatlonPCA2 = gpd.sjoin(geoidlatlonPCA1, counties, predicate='intersects').reset_index(drop=True)   
    return geoidlatlonPCA2

#import synthetic parcels and link parcels to PCA regions
def getParcels():
    parcelDir = os.path.join('Data','Parcel_data','synthetic_parcels_final.csv')
    parcels = pd.read_csv(parcelDir)
    parcels = parcels.dropna(subset=['GEOID'])
    #we assume 19% of parcel perimeriter is road, 44% is PPL, 37% is Non-PPL
    parcels['road_length'] = parcels['Shape_Length']*0.19
    parcels['PPL_length'] = parcels['Shape_Length']*0.44
    parcels['Non-PPL_length'] = parcels['Shape_Length']*0.37
    parcels = parcels.drop(columns=['GEO_COUNTY', 'STATEFP'])
    return parcels


###########################################################################################################################################################################
def fillBlanks(data):
    data['Setback: Road (m)'] = data['Setback: Road (m)'].fillna(data['Setback: Road (m)'].mode()[0])
    data['Setback: Participating property line (m)'] = data['Setback: Participating property line (m)'].fillna(6.1)
    data['Setback: Non-participating property line (m)'] = data['Setback: Non-participating property line (m)'].fillna(data['Setback: Non-participating property line (m)'].mode()[0])
    data['Setback: Participating residence (m)'] = data['Setback: Participating residence (m)'].fillna(data['Setback: Participating residence (m)'].mode()[0])
    data['Setback: Non-participating residence (m)'] = data['Setback: Non-participating residence (m)'].fillna(data['Setback: Non-participating residence (m)'].mode()[0])
    data['Minimum lot size (sq.m)'] = data['Minimum lot size (sq.m)'].fillna(data['Minimum lot size (sq.m)'].mode()[0])
    data['Maximum lot size (sq.m)'] = data['Maximum lot size (sq.m)'].fillna(0)
    data['Maximum lot area coverage'] = data['Maximum lot area coverage'].replace("None", 100)
    data['Maximum lot area coverage'] = data['Maximum lot area coverage'].fillna(100)
    return data