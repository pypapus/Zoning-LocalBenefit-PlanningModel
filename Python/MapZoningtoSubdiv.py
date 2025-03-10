
#Papa Yaw
#3/10/23

#Get import zoning database and generate scenarios to run
import pandas as pd, os, numpy as np, geopandas as gpd
from scipy.spatial import cKDTree
from GetZoningDataParcelsRegions import getZoningdata, fillBlanks

# from GetZoningDataParcelsRegions import *
# from SetupTransmissionAndZones import importPRegions, importCountysubs, importCounty
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# pregions = getRegions(pRegionShapes, subdivShapes, counties)
# subdivs = pregions

###########################################################################################################################################################################
# Map the zoning data to the sundivisions/resource points (Not all resource points would be in the zoning database)
###########################################################################################################################################################################

def getZoningdataSubdivs(subdivs):
    # zoningData, townshipsWithRules = getZoningdata()
    zoningData = getZoningdata()
    # NOTES FROM EMAIL WITH MADELEINE
    # For townships in a county, some may be county zoned and others may not be. We identify those that are not county zoned.
    # We apply county zoning rules to all townships
    # Subsequently, where a rule has been applied to a township, but the township has its own rule, we replace the county rule with the township rule
    #ACTION: Isolate all townships in the county that are not county zoned. These are the ones that have their own rules.
    #merge regions with zoning data on township ID to find townships. These include townships that are county zoned
    townships_with_rules  = pd.merge(subdivs, zoningData, left_on='GEOID', right_on='Jurisdiction 10-digit FIPS')
    townships_with_rules_list = townships_with_rules['GEOID'].to_list()
    #merge regions with zoning data on county ID to find townships that are county zoned only
    county_zoned  = pd.merge(subdivs, zoningData, left_on='CNTY_GEOID', right_on='Jurisdiction 10-digit FIPS')
    #find townships that are county zoned and taked them out of the townships list
    townships_without_rules = county_zoned[~county_zoned['GEOID'].isin(townships_with_rules_list)]
    # Add county rules to townships that are not county zoned
    subdivs = pd.concat([townships_with_rules, townships_without_rules]).reset_index(drop=True)

    subdivs = subdivs.astype({'Setback: Road (feet)':'float64',
                        'Setback: Participating property line (feet)':'float64',
                        'Setback: Non-participating property line (feet)':'float64',
                        'Setback: Participating residence (feet)':'float64',
                        'Setback: Non-participating residence (feet)':'float64',
                        'Maximum lot size (acres)':'float64',
                        'Minimum lot size (acres)':'float64',
                        }) 
    
    #change columns in feet to meters
    subdivs['Setback: Road (m)'] = subdivs['Setback: Road (feet)']*0.3048
    subdivs['Setback: Participating property line (m)'] = subdivs['Setback: Participating property line (feet)']*0.3048
    subdivs['Setback: Non-participating property line (m)'] = subdivs['Setback: Non-participating property line (feet)']*0.3048
    subdivs['Setback: Participating residence (m)'] = subdivs['Setback: Participating residence (feet)']*0.3048 
    subdivs['Setback: Non-participating residence (m)'] = subdivs['Setback: Non-participating residence (feet)']*0.3048

    #change columns in acres to sq.m
    subdivs['Maximum lot size (sq.m)'] = subdivs['Maximum lot size (acres)']*4046.85642
    subdivs['Minimum lot size (sq.m)'] = subdivs['Minimum lot size (acres)']*4046.85642
   
    #remove columns that have been updated
    subdivs.drop(['Setback: Road (feet)',
                'Setback: Participating property line (feet)',
                'Setback: Non-participating property line (feet)',
                'Setback: Participating residence (feet)',
                'Setback: Non-participating residence (feet)',
                'Maximum lot size (acres)',
                'Minimum lot size (acres)',
                'Jurisdiction 10-digit FIPS'], axis=1, inplace=True)
    
    #rename specific attributes that would be used in the analysis
    subdivs = subdivs.rename(columns={'Is solar allowed at all in jurisdiction?':'Solar: Township Permit',
                                'Is principal-use solar allowed (by any process) in dominant ag district?': 'Solar: Ag District'
                                })
    #solves issue with Cheboygan (City), MI
    # subdivs = subdivs[~(subdivs['GEOID'].isin([2603115000]) & subdivs['Jurisdiction Type'].isin(['City']))]
    
    # Fill in missing values in Blanks for road, PPL, Non-PPL and MLS with the mode of the column
    subdivs = fillBlanks(subdivs)
    subdivs = subdivs.astype({'Maximum lot area coverage':'float64'})
    return subdivs