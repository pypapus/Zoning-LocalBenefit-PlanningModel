#Papa Yaw
#3/10/23

#Get import zoning database and generate scenarios to run
import pandas as pd, os, numpy as np, geopandas as gpd
from GetZoningDataParcelsRegions import *
from MapZoningtoSubdiv import *
from SetupTransmissionAndZones import importCountysubs, importPRegions, importCounty
random_seed=11

# reTypeScenario = 'Solar' #reTypeScenario = 'Solar' and 'Wind'
# Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'
# jurisdiction = 'subdivision'
# parcels = getParcels()
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# regions = getRegions(pRegionShapes, subdivShapes, counties)
# zoningData = getZoningdataSubdivs(regions) 
# scenario_key = "scenario10"


############################################################################################################################################################################
## FUNCTIONS TO APPLY LAND-USE TYPE TO EACH SUBDIVISION
############################################################################################################################################################################
def getLanduse():
    Landforms = os.path.join('Data','Parcel_data','cultiavted_minus_rural_slope.csv')
    percentage_cultivated = pd.read_csv(Landforms, usecols=['GEOID','percentage_cultivated'])
    return percentage_cultivated.set_index('GEOID')

# Functions to apply percentage of land-use type to each subdivision
# Also find percentage of other land types from subdivision rural land
def Landuse_cultivated(subdivAreas, percentage_cultivated):
        subdivAreas = subdivAreas.reset_index()
        subdivAreas = subdivAreas.set_index('GEOID').join(percentage_cultivated/100)
        subdivAreas = subdivAreas.fillna(0)
        subdivAreas['subdiv_area'] = subdivAreas['subdiv_area'] * subdivAreas['percentage_cultivated']
        return subdivAreas.drop(['percentage_cultivated'], axis=1)

#Function to get subdivision areas depending on land-use type we want to apply to model
#Options: cultivated, uncultivated, both(cultivated+uncultivated), total_cover(total area of subdivision)
def getSubdivLandcover(Land_use, subdivAreas, percentage_cultivated):
    if Land_use == 'cultivated':
        return Landuse_cultivated(subdivAreas, percentage_cultivated)


############################################################################################################################################################################
##APPLYING ZONING ORDINANCE TO PARCELS
############################################################################################################################################################################

#Function to generate subdivs by "Who has Zoning Jurisdiction" 
def getSubdivByZoning(zoningData, entry1):
    condition1 = zoningData['Who Has Zoning Jurisdiction'].isin(entry1)
    zoningData = zoningData[condition1]
    zoningData = zoningData.reset_index(drop=True)
    return zoningData

#Function to generate subdivs by "Who has Zoning Jurisdiction"  and principal-use
def getSubdivByZoningPrincipal(zoningData, reTypeScenario,entry1,entry2):
    condition1 = zoningData['Who Has Zoning Jurisdiction'].isin(entry1)
    condition2 = zoningData[reTypeScenario +': Principal-Use'].isin(entry2)
    zoningData = zoningData[condition1 & condition2].reset_index(drop=True)
    return zoningData

#Function to generate parcel areas depending on categories for principal-use/township permit (yes, no and blanks)
def getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,entry1,entry2,entry3,entry4):
    condition1 = zoningData['Who Has Zoning Jurisdiction'].isin(entry1)
    condition2 = zoningData[reTypeScenario +': Principal-Use'].isin(entry2)
    condition3 = zoningData[reTypeScenario +': Township Permit'].isin(entry3)
    condition4 = zoningData[reTypeScenario +': Ag District'].isin(entry4)
    zoningData = zoningData[condition1 & condition2 & condition3 & condition4]
    zoningData = zoningData
    return zoningData


#Split Principal-use=No into two categories: 1) Yes (allow) 2) No (not allow), based on distribtion in Principal-use=Yes
def getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank=None):   
    percent_yes = len(scenario9(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction))/len(scenario6(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction))
    percent_no = len(scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction))/len(scenario6(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction))
    subdivBlankNo,subdivBlankYes= BlankstoYesNo(subdivs,percent_yes,percent_no,random_seed=11)
    if blank == 'yes':
        return subdivBlankYes
    elif blank == 'no':
        return subdivBlankNo

#Function to generate subdiv areas depending on categories for principal-use (yes, no and blanks)
def getParcelinZoningData(subdivs, parcels):
    AllParcelDim = pd.merge(subdivs, parcels, left_on='GEOID', right_on='GEOID')
    return AllParcelDim


#Function to apply setback from roads
# 1 19% of the parcel perimeter is bounded by a road
def setbackFromRoads(AllParcelDim):
    #applying setback across  width of parcel (assuming road is on the length of the parcel)
    AllParcelDim['road_setback_area'] = AllParcelDim['road_length'] * AllParcelDim['Setback: Road (m)']
    AllParcelDim['Shape_Area'] = AllParcelDim['Shape_Area'] - AllParcelDim['road_setback_area'] 
    AllParcelDim = AllParcelDim[AllParcelDim['Shape_Area'] >= 0] #remove parcels that have negative area after subtracting the road setback area.
    return AllParcelDim


#Functions to apply setback from property line set 
#  44% of the parcel perimeter is bounded by a participating property line
def setbackFromPPL(AllParcelDim):
    AllParcelDim['ppl_area'] = AllParcelDim['PPL_length'] * AllParcelDim['Setback: Participating property line (m)']
    AllParcelDim['Shape_Area'] = AllParcelDim['Shape_Area'] - AllParcelDim['ppl_area']
    AllParcelDim = AllParcelDim[AllParcelDim['Shape_Area'] >= 0] #remove parcels that have negative area after subtracting the ppl setback area.
    return AllParcelDim

# 37% of the parcel perimeter is bounded by a non-participating property line
def setbackFromNonPPL(AllParcelDim):
    AllParcelDim['non_ppl_area'] = AllParcelDim['Non-PPL_length'] * AllParcelDim['Setback: Non-participating property line (m)']
    AllParcelDim['Shape_Area'] = AllParcelDim['Shape_Area'] - AllParcelDim['non_ppl_area']
    AllParcelDim = AllParcelDim[AllParcelDim['Shape_Area'] >= 0] #remove parcels that have negative area after subtracting the non-ppl setback area.
    return AllParcelDim

#Function to apply minimum lot size
def setbackbyMinLS(AllParcelDim):
    AllParcelDim = AllParcelDim[AllParcelDim['Shape_Area'] >= AllParcelDim['Minimum lot size (sq.m)']]
    return AllParcelDim

#Function to apply minimum lot size
def setbackbyMaxLS(AllParcelDim):
    condition = ((AllParcelDim['Maximum lot size (sq.m)'] == 0) |
                 (AllParcelDim['Shape_Area'] <= AllParcelDim['Maximum lot size (sq.m)']))
    AllParcelDim = AllParcelDim[condition]
    return AllParcelDim

# value is a percentage of the parcel area that can be covered by solar panels
def maxLotCoverage(AllParcelDim):
    AllParcelDim['Shape_Area'] = AllParcelDim['Shape_Area'] * (AllParcelDim['Maximum lot area coverage']/100)
    return AllParcelDim

#create function to sample through Principal-Use=No apply distrubution of "Yes and No" iteratively
def BlankstoYesNo(df,percent_yes,percent_no, random_seed=11):
    # initialize empty DataFrames to store the yes and no subsets
    df_no = pd.DataFrame()
    df_yes = pd.DataFrame()
    # loop until the DataFrame is empty
    while len(df) > 5:
        # calculate percentage of the remaining DataFrame
        percent_no_ = int(len(df) * percent_no)
        percent_yes_ = int(len(df) * percent_yes)

        # set the random seed if provided
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # split the remaining DataFrame into percentage and the rest
        df_no_subset = df.sample(n=percent_no_)
        df_yes_subset = df.drop(df_no_subset.index).sample(n=percent_yes_)
        df_remainder = df.drop(df_no_subset.index).drop(df_yes_subset.index).reset_index(drop=True)
        
        # append the percentage subsets to their respective DataFrames
        df_no = pd.concat([df_no, df_no_subset]).reset_index(drop=True)
        df_yes = pd.concat([df_yes, df_yes_subset]).reset_index(drop=True)
        
        # update the DataFrame to the remainder
        df = df_remainder

        # add remaining dataframe to df_no if length is at least 10
    if len(df) <= 10:
        df_no = pd.concat([df_no, df]).reset_index(drop=True)
    
    return df_no, df_yes


############################################################################################################################################################################
##FUNCTIONS TO GENERATING SCEANARIOS
############################################################################################################################################################################
#Scenario 1:
def scenario1(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    parcels = pd.merge(parcels, regions, left_on='GEOID', right_on='GEOID')
    subdivAreas = parcels.groupby(
        ['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])["Shape_Area"].sum()
    subdivAreas = subdivAreas.rename(columns={'Shape_Area':'subdiv_area'})
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    #remove negative values from rural areas
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas

#Scenario 2: 
def scenario2(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other','No Data','Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas


#Scenario 3: 
def scenario3(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 4: 
def scenario4(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    subdivs = getSubdivByZoning(zoningData,authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas


#Scenario 5: 
def scenario5(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['No Data'] 
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 6:
def scenario6(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 7:
def scenario7(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 8:
def scenario8(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = [np.nan]
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 9:
def scenario9(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 10 outright ban on solar in ag district:
def scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['No', np.nan]
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 10a all outright bans including thise in ag district:
def scenario10a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['No']
    ag_district = ['No', np.nan,'Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 11:
def scenario11(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = [np.nan]
    ag_district = [np.nan,'No','Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas


#############################################################################################################################################
#################SETBACKS WHERE SOLAR IS ALLOWED IN AG DISTRICT #############################################################################
#############################################################################################################################################
#Scenario 9a: Road setback
def scenario9a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 9b: Applying participating property line setback
def scenario9b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

# Scenario 9c: apply non-participating property line setback instead of participating property line setback
def scenario9c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 9d: Applying Setbacks - minimum lot size
def scenario9d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 9e: Applying Setbacks - maximum lot size and maximum lot coverage
def scenario9e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['Yes']
    township_permit = ['Yes']
    ag_district = ['Yes']
    subdivs = getSubdivByZoningPrincipalTownshipsAg(zoningData, reTypeScenario,authority,principal_use,township_permit,ag_district)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    AllParcelDim = setbackbyMaxLS(AllParcelDim)
    AllParcelDim = maxLotCoverage(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#############################################################################################################################################
################# SETBACKS IN SUBDIVS THAT ARE UNZONED #############################################################################
#############################################################################################################################################
#Scenario 3a: Road setback
def scenario3a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 3b: Applying participating property line setback
def scenario3b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

# Scenario 3c: apply non-participating property line setback instead of participating property line setback
def scenario3c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 3d: Applying Setbacks - minimum lot size
def scenario3d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 3e: Applying Setbacks - maximum lot size and maximum lot coverage
def scenario3e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['Unzoned']
    subdivs = getSubdivByZoning(zoningData, authority)
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    AllParcelDim = setbackbyMaxLS(AllParcelDim)
    AllParcelDim = maxLotCoverage(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas


#Scenario 12: Zone but not regulated => No, Unzoned => No, bans
def scenario12(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#not allowed in ag district 
    data2 = scenario7(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#not regulated,zoned
    data3 = scenario3(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data = pd.concat([data1,data2, data3])
    return data 

#Scenario 13: #unzoned + zoned (without blanks)
def scenario13(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario14(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned
    data = pd.concat([data1,data2])
    if jurisdiction == 'subdivision':
        data = data.rename(columns={'COUNSUB_LAT': 'Lat', 'COUNSUB_LON': 'Lon'})
        data = data.drop(columns=['CNTY_GEOID', 'CNTY_LAT', 'CNTY_LON'])
    elif jurisdiction == 'county':
        data = data.rename(columns={'subdiv_area': 'county_area'})        
        data = (
            data.groupby('CNTY_GEOID', as_index=False)['county_area'].sum()
            .merge(
                data.loc[data.groupby('CNTY_GEOID')['county_area'].idxmax()][['CNTY_GEOID', 'STATEFP', 'PCA_Code', 'CNTY_LAT', 'CNTY_LON']],
                on='CNTY_GEOID'
            )
        )
        data = data.rename(columns={'CNTY_GEOID': 'GEOID','CNTY_LAT': 'Lat', 'CNTY_LON': 'Lon'})
    return data 

#scenario 14 Get zoned and remove principal-use = blanks
def scenario14(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario4(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data2 = scenario8(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data3 = scenario11(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data = data1[~data1.index.isin(data2.index)]
    data = data[~data.index.isin(data3.index)]
    return data 

#scenario 15: remove NO DATA from zoning database
def scenario15(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario2(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data2 = scenario5(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data3 = scenario8(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data4 = scenario11(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data = data1[~data1.index.isin(data2.index)]
    data = data[~data.index.isin(data3.index)]
    data = data[~data.index.isin(data4.index)]
    return data 

#scenario 16: remove blanks from scenario 6
def scenario16(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario6(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data2 = scenario11(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)
    data = data1[~data1.index.isin(data2.index)]
    return data 

#Scenario 17: Zone but not regulated => No, Unzoned => No, bans
def scenario17(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#not allowed in ag district 
    data2 = scenario7(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#not regulated,zoned
    data = pd.concat([data1,data2])
    return data 

#Scenario 18: unzoned + yes in ag district
def scenario18(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data 

#############################################################################################################################################
################# SETBACKS IN SUBDIVS THAT ARE UNZONED + ALLOWED IN AG DIST. #############################################################################
#############################################################################################################################################
#Scenario 18a: #Unzoned + yes in ag district, Road = Yes
def scenario18a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data 

#Scenario 18b: #Unzoned + yes in ag district, Road = Yes, PPL = Yes
def scenario18b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data 

#Scenario 18c: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes
def scenario18c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data 

#Scenario 18d: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes
def scenario18d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data 

#Scenario 18e: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes
def scenario18e_(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data

#Scenario 18e: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes
def scenario18e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario3e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario9e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    if jurisdiction == 'subdivision':
        data = data.rename(columns={'COUNSUB_LAT': 'Lat', 'COUNSUB_LON': 'Lon'})
        data = data.drop(columns=['CNTY_GEOID', 'CNTY_LAT', 'CNTY_LON'])
    elif jurisdiction == 'county':
        data = data.rename(columns={'subdiv_area': 'county_area'})        
        data = (
            data.groupby('CNTY_GEOID', as_index=False)['county_area'].sum()
            .merge(
                data.loc[data.groupby('CNTY_GEOID')['county_area'].idxmax()][['CNTY_GEOID', 'STATEFP', 'PCA_Code', 'CNTY_LAT', 'CNTY_LON']],
                on='CNTY_GEOID'
            )
        )
        data = data.rename(columns={'CNTY_GEOID': 'GEOID','CNTY_LAT': 'Lat', 'CNTY_LON': 'Lon'})
    return data 

#Scenario 19: Zoned, Principal-Use=No, Split to Yes
def scenario19(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]  
    return subdivAreas

#Scenario 20: Zoned, Principal-Use=No, Split to No
def scenario20(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='no')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)] 
    return subdivAreas

#Scenario 19a: Zone, Principal-Use=No, Split to Yes, Road Setback
def scenario19a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas

#Scenario 19b: Zone, Principal-Use=No, Split to Yes, Road Setback
def scenario19b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas

#Scenario 19c: Zone, Principal-Use=No, Split to Yes, Road Setback
def scenario19c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas  

#Scenario 19d: Zone, Principal-Use=No, Split to Yes, Road Setback
def scenario19d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas 

#Scenario 19e: Zone, Principal-Use=No, Split to Yes, All Setbacks
def scenario19e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    authority = ['City', 'Township', 'Village', 'Unincorporated','County','Other']
    principal_use = ['No']
    subdivs = getSubdivByZoningPrincipal(zoningData, reTypeScenario,authority,principal_use)
    subdivs = getSubdivByBlanksYesorNO(subdivs, reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction,blank='yes')
    AllParcelDim = getParcelinZoningData(subdivs, parcels)
    AllParcelDim = setbackFromRoads(AllParcelDim)
    AllParcelDim = setbackFromPPL(AllParcelDim)
    AllParcelDim = setbackFromNonPPL(AllParcelDim)
    AllParcelDim = setbackbyMinLS(AllParcelDim)
    AllParcelDim = setbackbyMaxLS(AllParcelDim)
    AllParcelDim = maxLotCoverage(AllParcelDim)
    subdivAreas = AllParcelDim.groupby(['GEOID','CNTY_GEOID','STATEFP','PCA_Code','COUNSUB_LAT','COUNSUB_LON','CNTY_LAT','CNTY_LON'])\
        .agg(subdiv_area=('Shape_Area', 'sum'), largest_parcel_area=('Shape_Area', 'max'))
    percentage_cultivated =  getLanduse()
    subdivAreas = getSubdivLandcover(Land_use,subdivAreas,percentage_cultivated)
    subdivAreas = subdivAreas.loc[(subdivAreas['subdiv_area'] > 0)]
    return subdivAreas

#Scenario 21e: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes
def scenario21e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19e(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario18e_(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    if jurisdiction == 'subdivision':
        data = data.rename(columns={'COUNSUB_LAT': 'Lat', 'COUNSUB_LON': 'Lon'})
        data = data.drop(columns=['CNTY_GEOID', 'CNTY_LAT', 'CNTY_LON'])
    elif jurisdiction == 'county':
        data = data.rename(columns={'subdiv_area': 'county_area'})        
        data = (
            data.groupby('CNTY_GEOID', as_index=False)['county_area'].sum()
            .merge(
                data.loc[data.groupby('CNTY_GEOID')['county_area'].idxmax()][['CNTY_GEOID', 'STATEFP', 'PCA_Code', 'CNTY_LAT', 'CNTY_LON']],
                on='CNTY_GEOID'
            )
        )
        data = data.rename(columns={'CNTY_GEOID': 'GEOID','CNTY_LAT': 'Lat', 'CNTY_LON': 'Lon'})
    return data 

def scenario21a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario18a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data

def scenario21b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario18b(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data

def scenario21c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario18c(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data

def scenario21d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#unzoned
    data2 = scenario18d(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data            

#Scenario 21e: #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes
def scenario21(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario19(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned split to yes
    data2 = scenario18(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#yes in ag district
    data = pd.concat([data1,data2])
    return data    

def scenario22(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario18a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#road 18e
    data2 = scenario17(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#no in ag district
    data = pd.concat([data1,data2])
    return data

#scenario where we take only silent_bans from baseline
def scenario23(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario13(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned and unzoned
    data2 = scenario7(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#silent bans
    data = data1[~data1.index.isin(data2.index)]
    return data

#scenario where we take both silent and outright bans from baseline
def scenario24(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario13(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned and unzoned
    data2 = scenario7(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#silent
    data3 = scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#outright bans
    data = data1[~data1.index.isin(data2.index)]
    data = data[~data.index.isin(data3.index)]
    return data

#scenario where we take only outright bans from baseline
def scenario25(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario13(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned and unzoned
    data2 = scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#outright bans
    data3 = scenario10a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#outright bans including ag district
    data = data1[~data1.index.isin(data2.index)]
    data = data[~data.index.isin(data3.index)]
    return data

#scenario where we take only silentbans from progressive
def scenario26(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction):
    data1 = scenario13(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#zoned and unzoned
    data2 = scenario20(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#silent bans
    data3 = scenario10(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#outright bans - ag district
    data4 = scenario10a(reTypeScenario,Land_use, zoningData, parcels, regions, jurisdiction)#outright bans including ag district
    data = data1[~data1.index.isin(data2.index)]
    data = data[~data.index.isin(data3.index)]
    data = data[~data.index.isin(data4.index)]
    return data



scenarios = {
    "scenario1": scenario1,                 #Get all subdivisions (including those not in ordinance), get rural areas, get land cover
    "scenario2": scenario2,                 #Get subdivisions in the zoning database by generating subdiv areas for all categories of principal-use (yes, no and blanks). 
    "scenario15": scenario15,               #remove NO DATA and blanks from zoning database ie. scenario2 - scenario5 - scenario8 - scenario11
    "scenario3": scenario3,                 #Get all subdivisions in zoning database that are unzoned 
    "scenario4": scenario4,                 #Get all subdivisions in zoning database that are zoned
    "scenario14": scenario14,               #Get all subdivisions in zoning database that are zoned and remove principal-use = blanks
    "scenario5": scenario5,                 #Get all subdivisions in zoning database that have not been accessed (No Data)
    "scenario6": scenario6,                 #Zoned, Principal Use = Yes ie. (in ordinance therefore regulate)
    "scenario16": scenario16,               #Remove blanks from scenario 6 ie. scenario 6 - scenario 11
    "scenario7": scenario7,                 #Zoned, Principal Use = No ie. (not in ordinance therefore do not regulate/Silent/Dfacto bans)
    "scenario8": scenario8,                 #Zoned, Principal Use = Blank ie. database does not say/yet to be read
    "scenario9": scenario9,                 #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes
    "scenario10": scenario10,               #Zoned, Principal Use = Yes, Township Permit = No, Ag District = No
    "scenario10a": scenario10a,               #Zoned, Principal Use = Yes, Township Permit = No (all bans including ag district)
    "scenario11": scenario11,               #Zoned, Principal Use = Yes, Township Permit = Blank, Ag District = Blank

    ########## SETBACKS WHERE SOLAR IS ALLOWED IN AG DISTRICT ##########################################
    "scenario9a": scenario9a,               #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes, Road = Yes
    "scenario9b": scenario9b,               #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes, Road = Yes, PPL = Yes
    "scenario9c": scenario9c,               #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes, Road = Yes, PPL = Yes, NPPL = Yes
    "scenario9d": scenario9d,               #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes
    "scenario9e": scenario9e,               #Zoned, Principal Use = Yes, Township Permit = Yes, Ag District = Yes, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes

    ########## SETBACKS IN SUBDIVS THAT ARE UNZONED ##########################################
    "scenario3a": scenario3a,               #Unzoned, Road = Yes
    "scenario3b": scenario3b,               #Unzoned, Road = Yes, PPL = Yes
    "scenario3c": scenario3c,               #Unzoned, Road = Yes, PPL = Yes, NPPL = Yes
    "scenario3d": scenario3d,               #Unzoned, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes
    "scenario3e": scenario3e,               #Unzoned, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes

    ########## "NO" FOR ACTUAL, UNZONED, UNREGULATED ##########################################
    "scenario12": scenario12,                #Zoned, Scenario 10 + Scenario 7 (All Township No)

    ################################################################################################
    "NoZoning": scenario13,               #unzoned + zoned 
    "scenario17": scenario17,               #Zoned, Principal-Use = No + Township Permit = No
    "scenario18": scenario18,                #unzoned + yes in ag district

    ########## SETBACKS IN SUBDIVS THAT ARE UNZONED + ALLOW SOLAR ##########################################
    "scenario18a": scenario18a,               #Unzoned + yes in ag district, Road = Yes
    "scenario18b": scenario18b,               #Unzoned + yes in ag district, Road = Yes, PPL = Yes
    "scenario18c": scenario18c,               #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes
    "scenario18d": scenario18d,               #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes
    "CurrentZoning": scenario18e,               #Unzoned + yes in ag district, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes

    ########## SPLITTING PRINCIPAL-USE: NO ################################################################# 
    "scenario19": scenario19,                  #Zoned, Principal-Use = No -> Split to Yes
    "scenario20": scenario20,                  #Zoned, Principal-Use = No -> Split to No 

    "scenario19a": scenario19a,               #zoned, Road = Yes
    "scenario19b": scenario19b,               #zoned, Road = Yes, PPL = Yes
    "scenario19c": scenario19c,               #zoned, Road = Yes, PPL = Yes, NPPL = Yes
    "scenario19d": scenario19d,               #zoned, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes
    "scenario19e": scenario19e,                #zoned, Road = Yes, PPL = Yes, NPPL = Yes, MinLS = Yes, MaxLS = Yes

    "scenario21": scenario21,                #Zoned, Scenario 19 + Scenario 18  (All ordinances)
    "scenario21a": scenario21a,              #Zoned, Scenario 19a + Scenario 18a  (All ordinances)
    "scenario21b": scenario21b,              #Zoned, Scenario 19b + Scenario 18b  (All ordinances)
    "scenario21c": scenario21c,              #Zoned, Scenario 19c + Scenario 18c  (All ordinances)
    "scenario21d": scenario21d,              #Zoned, Scenario 19d + Scenario 18d  (All ordinances)
    "ExpandedZoning": scenario21e,              #Zoned, Scenario 19e + Scenario 18e  (All ordinances)
    "scenario22": scenario22,                 #Zoned, Scenario 18a + scenario17
    "scenario23": scenario23,                #scenario where we take only silent from baseline (Zoned and unzoned - silent)
    "scenario24": scenario24,                #scenario where we take only silent+bans from baseline (Zoned and unzoned - (silent + outrightBans))
    "scenario25": scenario25,                #scenario where we take only outright bans from baseline (Zoned and unzoned - outrightBans)
    "scenario26": scenario26                #scenario where we take only silent bans from progressive (Zoned and unzoned - (silentBans))
}

# call a specific scenario using the dictionary
# scenarios[scenario_key](reTypeScenario,Land_use,zoningData,parcels,regions,jurisdiction) # call the function for that scenario

# x = gpd.GeoDataFrame(x, geometry=gpd.points_from_xy(x.Lon, x.Lat))