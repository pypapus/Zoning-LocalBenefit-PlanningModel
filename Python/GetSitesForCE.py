import pandas as pd
import os
from ApplyZoningOrdinanceMod import *
from GetZoningDataParcelsRegions import *
from SetupTransmissionAndZones import importPRegions, importCountysubs, importCounty


# scenario_key = "CurrentZoning" #scenario_key = "scenario13" and "scenario18e" and "scenario21e"
# re = 'solar' #re = 'solar' and 'wind'
# windPowerDensity = 0.5
# solarPowerDensity = 5
# reTypeScenario = 'Solar' #reTypeScenario = 'Solar' and 'Wind'
# Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'
# jurisdiction = 'county' #jurisdiction = 'subdivision' and 'county'
# parcels = getParcels()
# pRegionShapes = importPRegions()
# subdivShapes = importCountysubs()
# counties = importCounty()
# regions = getRegions(pRegionShapes, subdivShapes, counties)
# zoningData = getZoningdataSubdivs(regions)
# siteLeastCap = 5 

# power_densities = {
#     'wind': 0.5,
#     'solar': 5}
# states = ['MN', 'WI', 'IL', 'MI', 'IN', 'OH']

# sitestoFilter = 100
# tx_distance = 'all'


#Define functions for getting zoning sites and LCOE
def scenariosites(reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction, scenario_key, 
                  re, siteLeastCap, power_densities, sitestoFilter, states, tx_distance):
    statefp = {'MN': 27, 'WI': 55, 'IL': 17, 'MI': 26, 'IN': 18, 'OH': 39}
    lcoe = getLCOE(re,jurisdiction)
    distance_to_transmission = getDistancetoTransmission(tx_distance)
    scenario_sites = scenarios[scenario_key](reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction).reset_index()
    #get state names and capacity, LCOE and distance to tx. of sites
    scenario_sites = stateNames(statefp, states, scenario_sites)
    scenario_sites = capacitySites(scenario_sites, jurisdiction, re, power_densities, lcoe, distance_to_transmission)
    # select sites with capacity greater than siteLeastCap
    scenario_sites = scenario_sites[scenario_sites['Capacity (MW)'] >= siteLeastCap]
    allSites = scenarios["NoZoning"](reTypeScenario, Land_use, zoningData, parcels, regions, jurisdiction).reset_index()
    #select specific states
    allSites = stateNames(statefp, states, allSites)
    allSites = capacitySites(allSites, jurisdiction, re, power_densities, lcoe, distance_to_transmission)
    allSites = allSites[allSites['Capacity (MW)'] >= siteLeastCap]
    sitesForCE = downscalingSites(allSites, sitestoFilter, scenario_sites, re)
    return sitesForCE
    
 
def getDistancetoTransmission(tx_distance):
    distance_to_transmission = pd.read_csv(os.path.join('Data', 'Transmission_cost','Final','least_distance_rating_tx.csv'), index_col=0)
    if tx_distance =='tx2mi':
        #filter by 2mi distance to transmission
        distance_to_transmission = distance_to_transmission[distance_to_transmission['Least Distance(miles)'] <= 2]
    else :
        distance_to_transmission = distance_to_transmission
    return distance_to_transmission.reset_index()


def getLCOE(re,jurisdiction):
    if jurisdiction == 'county':
        lcoe = pd.read_csv(os.path.join('Data', 'LCOE_Data', 'LCOE_county_sites.csv'), index_col=0)
    else:
        lcoe = pd.read_csv(os.path.join('Data', 'LCOE_Data', 'LCOE_subdiv_sites.csv'), index_col=0)
    lcoe = lcoe[lcoe['Tech'] == re]
    return lcoe.reset_index()
        
# Function to calculate the capacity of sites based on jurisdiction
def capacitySites(scenario_sites, jurisdiction, re, power_densities, lcoe, distance_to_transmission):
    if jurisdiction not in ['county']: # corrected the check for 'county'
        scenario_sites['Capacity (MW)'] = (scenario_sites['subdiv_area'] * power_densities[re]) / 1_000_000 #power density is in W/m^2
        scenario_sites = pd.merge(scenario_sites, distance_to_transmission, on='GEOID', how='inner')
    else:
        scenario_sites['Capacity (MW)'] = (scenario_sites['county_area'] * power_densities[re]) / 1_000_000
    scenario_sites = pd.merge(scenario_sites, lcoe, on='GEOID', how='inner').drop(columns='Tech')
    return scenario_sites

# Function to filter by state names based on FIPS code
def stateNames(statefp, states, scenario_sites):
    scenario_sites_ = []  # Initialize an empty list to collect matching sites
    for state_name, fips_code in statefp.items():
        if state_name in states:  # Check if the state name is in the list of states
            matching_sites = scenario_sites[scenario_sites['STATEFP'] == fips_code]
            scenario_sites_.append(matching_sites)  # Append the matching rows
    if scenario_sites_:  # Check if the list has any data to concatenate
        scenario_sites = pd.concat(scenario_sites_, ignore_index=True)  # Concatenate the list of DataFrames
    else:
        scenario_sites = pd.DataFrame()  # Return an empty DataFrame if no matches
    return scenario_sites


#filter scenario_sites to use in the CE model. We do this to ensure that the sites used in the CE model are the same for all scenarios
def downscalingSites(allSites, sitestoFilter, scenario_sites, re):
        filtered_sites = []
        for state_code in allSites['STATEFP'].unique():
            # Calculate the percentile value for the given state
            percentile_value = allSites[allSites['STATEFP'] == state_code]['Total LCOE ($/MWh)'].quantile(sitestoFilter / 100)
            
            # Filter sites in the state that have LCOE less than or equal to the percentile value
            filtered_sites.append(allSites[
                (allSites['STATEFP'] == state_code) & 
                (allSites['Total LCOE ($/MWh)'] <= percentile_value)
            ])
        
        # Concatenate all filtered sites into a single DataFrame
        downscaled_sites = pd.concat(filtered_sites).reset_index(drop=True)

        #now select sites for the scenario
        # if wind do nothing
        if re == 'wind':
            return downscaled_sites
        else:
            capacity_map = scenario_sites.set_index('GEOID')['Capacity (MW)']
            downscaled_sites['Capacity (MW)'] = downscaled_sites['GEOID'].map(capacity_map).fillna(0)
            return downscaled_sites