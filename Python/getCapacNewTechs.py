import pandas as pd
from ApplyZoningOrdinanceMod import *
# deprecated
###################################################################################################
# reTypeScenario = 'Solar' #reTypeScenario = 'Solar' and 'Wind'
# scenario_key = "scenario25"
# Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'


# # # ### DESIGN OF PV SYSTEM (TO ESTIMATES MW/ACRE - (10.1109/JPHOTOV.2021.3136805))S
# sys_design = 'fixed_tilt' #'fixed_tilt' and 'tracking' corresponding 0.24 MWDC/acre and 0.35 MWDC/acre, repectively.

# parcels = getParcels()
# regions = getRegions()
# zoningData= getZoningdataSubdivs()
##################################################################################################

mechanics = {'fixed_tilt': 0.25, 
             'tracking': 0.35}


#Using MW/acre density benchmark to estimate buildable PV capacity per subdivision area (10.1109/JPHOTOV.2021.3136805)
#Power density: 0.35 MWDC/acre (0.87 MWDC/hectare) for fixed-tilt and 0.24 MWDC/acre (0.59 MWDC/hectare) for tracking plants.
def getSubdivScenarioCapacity(scenario_key,reTypeScenario,Land_use,zoningData,parcels,regions):
    #Get subdiv area and convert area from sq.m to acres
    subdivArea = scenarios[scenario_key](reTypeScenario,Land_use,zoningData,parcels,regions)
    # subdivArea['subdiv_area (acres)'] = subdivArea['subdiv_area']/4046.85642
    # subdivArea['largest_parcel_area (acres)'] = subdivArea['largest_parcel_area']/4046.85642
    #Estimate the buildable capacity for fixed tilt
    subdivArea['Capacity (MW)'] = (subdivArea['subdiv_area']*10)/1000000 #DOI 10.1088/1748-9326/aae102
    subdivArea['Parcel Capacity (MW)'] = (subdivArea['largest_parcel_area']*10)/1000000
    return subdivArea.reset_index()















