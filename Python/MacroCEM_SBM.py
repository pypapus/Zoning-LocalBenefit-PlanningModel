# FUTURE POSSIBLE ADDITIONS:
# (8/17/22) Geothermal fuel not in PHORUM for UC parameters (WECC) - coudl add geothermal-specific values
# Add time-varying limits on quantify of new techs to add
# Add contingency reserves into greenfield run
# Allow wind & solar to provide all reserves - add constriants to GAMS limiting their generation
    # in CESharedFeatures
# Make solar reserve calculation efficient

import sys, os, csv, operator, copy, time, random, warnings, numpy as np, datetime as dt, pandas as pd
from os import path; from netCDF4 import Dataset; from gams import *
os.environ['USE_PYGEOS'] = '0'
import geopandas
from GAMSAuxFuncs import *
from SetupGeneratorFleet import *
from ProcessHydro import processHydro
from ImportERCOTDemand import importHourlyERCOTDemand
from UpdateFuelPriceFuncs import *
from DemandFuncs import *
from DemandFuncsCE import *
from IsolateDataForCE import isolateDataInCEHours,isolateDataInCEBlocks
from SetInitCondsUC import *
from ImportNewTechs import getNewTechs
from RetireUnitsCFPriorCE import retireUnitsCFPriorCE
from CreateFleetForCELoop import *
from GetRenewableCFs import getREGen
from GetNewRenewableCFs import *
from AddWSSitesToNewTechs import addWSSitesToNewTechs
from ProcessCEResults import *
from ScaleRegResForAddedWind import scaleRegResForAddedWind
from CombinePlants import combineWindSolarStoPlants
from GAMSAddSetToDatabaseFuncsSBM import *
from GAMSAddParamToDatabaseFuncsSBM import *
from ConvertCO2CapToPrice import convertCo2CapToPrice
from SaveDispatchResults import saveDispatchResults, writeDispatchResults
from InitializeOnOffExistingGensCE import initializeOnOffExistingGens
from ReservesWWSIS import calcWWSISReserves
from GetIncResForAddedRE import getIncResForAddedRE
from SaveCEOperationalResults import saveCapacExpOperationalData
from WriteTimeDependentConstraints import writeTimeDependentConstraints
from WriteBuildVariable import writeBuildVariable
from CreateEmptyReserveDfs import createEmptyReserveDfs
from SetupTransmissionAndZones import setupTransmissionAndZones, defineTransmissionRegions, importCountysubs, importPRegions, importCounty
from GetZoningDataParcelsRegions import *
from MapZoningtoSubdiv import *
from CombineOnlyWS import *
from ApplyZoningOrdinanceMod import *
from DiscountCost import discountCapexForState


# SET OPTIONS
warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 10)

# SCALARS
mwToGW = 1000
lbToShortTon = 2000

# ###################################################################4############
# ##### UNIVERSAL PARAMETERS ####################################################
# ###############################################################################
def setKeyParameters(interconn, timesteps):
    # ### RUNNING ON SC OR LOCAL
    runOnSC = False                                     # whether running on supercomputer

    #### STUDY AREA AND METEOROLOGICAL-DEPENDENT DATA
    metYear = 2012 #year of meteorological data used for demand and renewables

    electrifiedDemand = True                            # whether to import electrified demand futures from NREL's EFS
    elecDemandScen = 'REFERENCE'                        # 'REFERENCE','HIGH','MEDIUM' (ref is lower than med)
    annualDemandGrowth = 0                              # fraction demand growth per year - ignored if use EFS data (electrifieDemand=True)
    metYear = 2012 if electrifiedDemand else metYear    # EFS data is for 2012; ensure met year is 2012
    
    reSourceMERRA = False                                # == True: use MERRA as renewable data source, == False: use NSDB and Wind Toolkit
    reDownFactor = 1 #1000                                 # downscaling factor for W&S new CFs; 1 means full resolution, 2 means half resolution, 3 is 1/3 resolution, etc

    interconn = 'EI'                                    # which interconnection to run - ERCOT, WECC, EI or census region to run - ENC (East North Central)
    balAuths = 'subset'                                   # full: run for all BAs in interconn. Modified to run "subset": representing a subset if BAs
    states =['MI']# ['MI','MN', 'WI', 'IL', 'IN', 'OH']         #subset of states within with BA
    jurisdiction = 'county'                            # 'county' or 'subdivision' for aggregation of total available capacity. Defaults to subdivision

    #### SPECIFIES ZONINIG ORDINANCE FOR RE TYPE UNDER SCENARIOS
    reTypeScenario = 'Solar' #What tech zoning ordinances is applied 'Solar' and 'Wind'
    Land_use = 'cultivated' #Land_use = 'cultivated','uncultivated','both','total_cover'

    #POWER DENSITY USED FOR CALCULATING MAX CAPACITY OF SOLAR AND WIND
    power_density = {
        'wind': 0.5,
        'solar': 5.5
    }
                                           #https://iopscience.iop.org/article/10.1088/1748-9326/aae102
    
    tracking  = 1                                # whether to include tracking in solar capacity calculations (0: fixed tilt, 1: one-axis tracking)

    #REDUCE THE SIZE OF DATA BY FILTERING OUT A PERCENTILE
    siteLeastCap = 5                                # minimum capacity of subdivision (MW)
    sitestoFilter = 5                             # percentile of sites to consider


    allSolarMaxBuild = {                    # maximum solar build in each model run (GW)
        2020: 1000000, 
        2025: 1000000,
        2030: 1000000,
        2035: 1000000,
        2040: 1000000
    } 

    #################STATE PARAMETERS########################################################

    #NESTED DICTIONARY OF MAX SOLAR BUILD PER STATE FOR EACH YEAR}
    stateCap = {
    "IL": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000},
    "IN": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000},
    "MI": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000},
    "MN": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000},
    "OH": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000},
    "WI": {2020: 1000000, 2025: 1000000, 2030: 1000000, 2035: 1000000, 2040: 1000000}
    }

    #MINIMUM SOLAR GENERATION AS FRACTION OF DEMAND BY STATE IN FINAL YEAR (set all these to 0 when running a max solar build scenario, since conflicting constraints will result in an infeasible model)
    stateSolarGenFracOfDemand = {
        "MI": 0,
        "IL": 0,
        "MN": 0,
        "IN": 0,
        "OH": 0,
        "WI": 0
    }

    initialstateSolarGenFracOfDemand = {
        "MI": 0,
        "IL": 0,
        "MN": 0,
        "IN": 0,
        "OH": 0,
        "WI": 0
    }

    ##### MINIMUM AND MAXIMUM BOUND ON SOLAR AND WIND CAPACITY (GW) AT EACH LOCATION (COUNTY OR SUBDIVISION)
    solarMaxBuildLoc = 10000                    # maximum solar that can be built at each location ie. county or subdivision 
    solarMinBuildLoc = 0
    windMinBuildLoc = 0
    
    # ### WHETHER TO INCLUDE IRA
    ira = True

    # ### STATE TO DISCOUNT COST OF SOLAR AND WIND
    statesToDiscountCost = [''] #states to discount cost of solar and wind, Leave empty if no discount

    # ### BUILD SCENARIO
    buildLimitsCase = 1                                 # 1 = reference case,
                                                        # 2 = limited nuclear,
                                                        # 3 = limited CCS and nuclear,
                                                        # 4 = limited hydrogen storage,
                                                        # 5 = limited transmission
                                                        # 6 = No Combined Cycle

    # ### START YEAR, END YEAR, AND STEPS FOR CE
    if timesteps == 2030:
        startYear, endYear, yearStepCE = 2020, 2031, 5     # start year, end year, and year step for 
    elif timesteps == 2035:
        startYear, endYear, yearStepCE = 2020, 2036, 5
    elif timesteps == 2040:
        startYear, endYear, yearStepCE = 2020, 2041, 5
    
    # ### CO2 EMISSION CAPS AND DACS TREATMENT [https://www.eia.gov/environment/emissions/state/, table 3]
    if interconn == 'ERCOT': co2EmsInitial =  130594820     #METRIC TONS. Initial emission for ERCOT: 130594820.
    elif interconn == 'EI': co2EmsInitial = 202800000 #Full= 202800000 #80% reduction = 162240000         (modified for states in EI) #final year emissions for EI: 40560000 (80% CO2 reduction)
    elif interconn == 'WECC': co2EmsInitial =  248800000    #2019. METRIC TONS. wa,or,ca,nm,az,nv,ut,co,wy,id,mt

    yearIncDACS = 2050                                  #year to include DACS - set beyond end period if don't want DACS

    # ### CE AND UCED/ED OPTIONS
    compressFleet = True                                                # whether to compress fleet
    tzAnalysis = {'ERCOT':'CST','EI':'EST','WECC':'PST'}[interconn]     # timezone for analysis
    fuelPrices = importFuelPrices('Reference case')                     # import fuel price time series
    transmissionEff = 0.95                                              # efficiency of transmission between zones (https://ars.els-cdn.com/content/image/1-s2.0-S2542435120305572-mmc1.pdf)

    # ### CE OPTIONS
    runCE, ceOps = True, 'ED'                           # ops are 'ED' or 'UC' (econ disp or unit comm constraints)
    numBlocks, daysPerBlock, daysPerPeak = 4, 7, 1                              # num rep time blocks, days per rep block, and days per peak block in CE
    fullYearCE = True if (numBlocks == 1 and daysPerBlock > 300) else False     # whether running full year in CE
    removeHydro = False                                  #whether to remove hydropower from fleet & subtract generation from demand, or to include hydro as dispatchable in CE w/ gen limit
    greenField = False                                  # whether to run greenField (set to True) or brownfield (False)
    includeRes = False                                  # whether to include reserves in CE & dispatch models (if False, multiplies reserve timeseries by 0)
    stoInCE, seasStoInCE = True,False                    # whether to allow new storage,new seasonal storage in CE model
    retireByAge = False                                  # whether to retire by age or not
    planningReserveMargin = 0.1375                      # fraction of peak demand; ERCOT targeted planning margin # chnage to use MISO PRM ICAP: 0.179
    retirementCFCutoff = 0.5                            # retire units w/ CF lower than given value
    ptEligRetCF = ['Coal Steam']                         # which plant types retire based on capacity factor (economics)
    discountRate = 0.07 
    incNuc = True                                      # include nuclear as new investment option or not

    # ### ED/UCED OPTIONS
    runFirstYear = False                                # whether to run first year of dispatch
    ucOrED = 'None'                                     # STRING that is either: ED, UC, None
    useCO2Price = False                                 # whether to calc & inc CO2 price in operations run

    # ### STORAGE OPTIONS
    stoMkts = 'energy'                            # energy,res,energyAndRes - whether storage participates in energy, reserve, or energy and reserve markets
    stoFTLabels = ['Energy Storage','Pumped Storage']
    stoDuration = {'Energy Storage':'st','Hydrogen':'lt','Battery Storage':'st','Flywheels':'st','Batteries':'st','Pumped Storage':'st'} # mapping plant types to short-term (st) or long-term (lt) storage
    stoPTLabels = [pt for pt in stoDuration ]
    initSOCFraction = {pt:{'st':.1,'lt':.05}[dur] for pt,dur in stoDuration.items()} # get initial SOC fraction per st or lt storage
    stoMinSOC = 0     #min SOC

    # ### GENERIC DEMAND FLEXIBILITY PARAMETERS
    demandShifter = 0                                   # Percentage of hourly demand that can be shifted
    demandShiftingBlock = 4                            # moving shifting demand window (hours)

    # ### MINIMUM
    #  BOUND ON SOLAR AND WIND GENERATION (AS FRACTION OF DEMAND EACH YEAR) #SET INITIAL VALUES
    initialReFracOfDemand = 0                    
    initialCleanFracOfDemand = 0   

    # ### LIMITS ON TECHNOLOGY DEPLOYMENT (max added MW per CE run (W&S by cell))
    maxCapPerTech = {'Thermal': 999999, 'Combined Cycle': 50000,
                     'Storage': 100000, 'Dac': -9999999, 'CCS': 999999, 'Nuclear': 999999, 'Battery Storage': 10000,
                     'Hydrogen': 10000, 'Transmission': 1000}     
    if buildLimitsCase == 2: maxCapPerTech['Nuclear'] = 9000 
    elif buildLimitsCase == 3: maxCapPerTech['CCS'],maxCapPerTech['Nuclear'] = 1500,9000
    elif buildLimitsCase == 4: maxCapPerTech['Hydrogen'] = 0
    elif buildLimitsCase == 5: maxCapPerTech['Transmission'] = 10
    
    # ### WARNINGS OR ERRORS
    if ceOps == 'UC': sys.exit('CEwithUC.gms needs to be updated for DACS operations - add DACS constraints and include gentechs set')
    if ucOrED != 'None': sys.exit('ED and UC.gms need to be checked for DACS constraints')

    return (buildLimitsCase, greenField, includeRes, useCO2Price, runCE, ceOps, stoInCE, seasStoInCE, ucOrED, numBlocks,
            daysPerBlock, daysPerPeak, fullYearCE, incNuc, compressFleet, fuelPrices, co2EmsInitial,
            startYear, endYear, yearStepCE, retirementCFCutoff, retireByAge, planningReserveMargin,
            discountRate, annualDemandGrowth, stoMkts, stoFTLabels, stoPTLabels, initSOCFraction, tzAnalysis, 
            initialReFracOfDemand, initialCleanFracOfDemand, solarMinBuildLoc, windMinBuildLoc, maxCapPerTech,
            runCE, runFirstYear, metYear, ptEligRetCF, stoMinSOC, reDownFactor, demandShifter, demandShiftingBlock,
            runOnSC, yearIncDACS, electrifiedDemand, elecDemandScen, balAuths, states, jurisdiction, reTypeScenario, 
            Land_use, power_density, tracking, reSourceMERRA, transmissionEff, removeHydro, sitestoFilter, siteLeastCap, ira, 
            allSolarMaxBuild, solarMaxBuildLoc, stateCap, stateSolarGenFracOfDemand, initialstateSolarGenFracOfDemand, statesToDiscountCost) 

#################################################
def importParcelsRegionZoning():
    parcels = getParcels()
    pRegionShapes = importPRegions()
    subdivShapes = importCountysubs()
    countyShapes = importCounty()
    regions = getRegions(pRegionShapes, subdivShapes, countyShapes)
    zoningData = getZoningdataSubdivs(regions)
    return parcels,regions, zoningData
##################################################

def importFuelPrices(fuelPriceScenario):
    fuelPrices = pd.read_csv(os.path.join('Data', 'Energy_Prices_Electric_Power.csv'), skiprows=4, index_col=0)
    fuelPrices = fuelPrices[[col for col in fuelPrices if fuelPriceScenario in col]]
    fuelPrices.columns = [col.split(':')[0] for col in fuelPrices.columns]
    return fuelPrices    

# Define reserve parameters for UC & CE w/ UC constraints models
def defineReserveParameters(stoMkts,stoFTLabels):
    # Regulation eligibility
    regElig = ['Steam', 'Combined Cycle', 'Geothermal'] + (stoFTLabels if 'res' in stoMkts.lower() else [])
    contFlexInelig = ['Wind','Solar','DAC'] #fuel types that are ineligible to provide flex or cont reserves

    # Regulation provision cost as fraction of operating cost
    regCostFrac = 0  # 0.1

    # Requirement parameters - based on WWSIS Phase 2
    regLoadFrac = .01                                   # frac of hourly load in reg up & down
    contLoadFrac = .03                                  # frac of hourly load in contingency
    regErrorPercentile = 40                             # ptl of hourly W&S forecast errors for reg reserves; in WWSIS, 95th ptl of 10-m wind & 5-m solar forecast errors
    flexErrorPercentile = 70                            # ptl of hourly W&S forecast errors used in flex reserves

    # Timeframes
    regReserveMinutes = 5               # reg res must be provided w/in 5 minutes
    flexReserveMinutes = 10             # spin reserves must be provided w/in 10 minutes
    contingencyReserveMinutes = 30      # contingency res must be provided w/in 30 minutes
    minutesPerHour = 60
    rampRateToRegReserveScalar = regReserveMinutes/minutesPerHour               # ramp rate in MW/hr
    rampRateToFlexReserveScalar = flexReserveMinutes/minutesPerHour             # ramp rate in MW/hr
    rampRateToContReserveScalar = contingencyReserveMinutes/minutesPerHour

    return (regLoadFrac, contLoadFrac, regErrorPercentile, flexErrorPercentile,
        regElig, contFlexInelig, regCostFrac, rampRateToRegReserveScalar, rampRateToFlexReserveScalar,
        rampRateToContReserveScalar)

# ###############################################################################
# ###############################################################################
# ###############################################################################

# ###############################################################################
# ##### MASTER FUNCTION #########################################################
# ###############################################################################
#Main function to call. 
#Inputs: interconnection (EI, WECC, ERCOT); CO2 emissions in final year as fraction
#of initial CO2 emissions.
def runMacroCEM(interconn,timesteps,co2EmsInFinalYear,reGenFracOfDemand,cleanGenFracOfDemand,scenario_key, scope, tx_distance, capex_discount_rate, costWgt=None):
    # Import key parameters
    (buildLimitsCase, greenField, includeRes, useCO2Price, runCE, ceOps, stoInCE, seasStoInCE, ucOrED, numBlocks,
    daysPerBlock, daysPerPeak, fullYearCE, incNuc, compressFleet, fuelPrices, co2EmsInitial,
    startYear, endYear, yearStepCE, retirementCFCutoff, retireByAge, planningReserveMargin,
    discountRate, annualDemandGrowth, stoMkts, stoFTLabels, stoPTLabels, initSOCFraction, tzAnalysis, 
    initialReFracOfDemand, initialCleanFracOfDemand, solarMinBuildLoc, windMinBuildLoc, maxCapPerTech,
    runCE, runFirstYear, metYear, ptEligRetCF, stoMinSOC, reDownFactor, demandShifter, demandShiftingBlock,
    runOnSC, yearIncDACS, electrifiedDemand, elecDemandScen, balAuths, states, jurisdiction, reTypeScenario, 
    Land_use, power_density, tracking, reSourceMERRA, transmissionEff, removeHydro, sitestoFilter, siteLeastCap, 
    ira, allSolarMaxBuild, solarMaxBuildLoc, stateCap, stateSolarGenFracOfDemand,initialstateSolarGenFracOfDemand,statesToDiscountCost) = setKeyParameters(interconn, timesteps)

    (regLoadFrac, contLoadFrac, regErrorPercentile, flexErrorPercentile, regElig, contFlexInelig, regCostFrac,
        rrToRegTime, rrToFlexTime, rrToContTime) = defineReserveParameters(stoMkts, stoFTLabels)
    parcels, regions, zoningData = importParcelsRegionZoning()
    
    # Create results directory
    buildScen = {1:'Ref', 2:'Nuc',3: 'NucCCS', 4: 'H2', 5: 'Trans'}[buildLimitsCase]
    if costWgt == None:
        costWgt = 1

    resultsDirAll = (
    f"Results_{scenario_key}_reGenFrac{int(reGenFracOfDemand)}"
    f"_cleanGenFrac{int(cleanGenFracOfDemand)}_{interconn}_{int(timesteps)}_CO2Final_{int(co2EmsInFinalYear)}"
    f"_{scope}_{tx_distance}_CAPEX_{float(capex_discount_rate)}"
    f"_costWgt_{float(costWgt)}"
    ) 
    if not os.path.exists(resultsDirAll): os.makedirs(resultsDirAll)
    pd.Series(co2EmsInitial).to_csv(os.path.join(resultsDirAll,'initialCO2Ems.csv'))

    # Setup initial fleet and demand
    (genFleet, demandProfile, transRegions, lineLimits, lineDists, lineCosts, pRegionShapes, 
     subdivShapes, countyShapes) = getInitialFleetDemandTransmission(startYear, fuelPrices, electrifiedDemand,
                                                       elecDemandScen, compressFleet, resultsDirAll,
                                                       regElig, regCostFrac, metYear, stoMinSOC, greenField,
                                                       interconn, balAuths, states, jurisdiction, contFlexInelig, stoFTLabels, stoPTLabels)

    # Run CE and/or ED/UCED
    for currYear in range(startYear, endYear, yearStepCE):
        # Set CO2 cap
        currCo2Cap = co2EmsInitial + ((co2EmsInFinalYear - co2EmsInitial) / ((endYear - 1) - startYear) * (currYear - startYear))
       
        # Set minimum bound on solar and wind generation as fraction of demand
        currReGenFracOfDemand = initialReFracOfDemand + reGenFracOfDemand/(endYear-1 - startYear) * (currYear - startYear)
        currCleanGenFracOfDemand = initialCleanFracOfDemand + cleanGenFracOfDemand/(endYear-1 - startYear) * (currYear - startYear)

        # Set minimum bound on solar and wind generation as fraction of demand for each state
        currMISolarGenFracOfDemand = initialstateSolarGenFracOfDemand['MI'] + stateSolarGenFracOfDemand['MI']/(endYear-1 - startYear) * (currYear - startYear)
        currILSolarGenFracOfDemand = initialstateSolarGenFracOfDemand['IL'] + stateSolarGenFracOfDemand['IL']/(endYear-1 - startYear) * (currYear - startYear)
        currMNSolarGenFracOfDemand = initialstateSolarGenFracOfDemand['MN'] + stateSolarGenFracOfDemand['MN']/(endYear-1 - startYear) * (currYear - startYear)
        currINSolarGenFracOfDemand = initialstateSolarGenFracOfDemand['IN'] + stateSolarGenFracOfDemand['IN']/(endYear-1 - startYear) * (currYear - startYear)
        currOHSolarGenFracOfDemand = initialstateSolarGenFracOfDemand['OH'] + stateSolarGenFracOfDemand['OH']/(endYear-1 - startYear) * (currYear - startYear)
        currWISolarGenFracOfDemand = initialstateSolarGenFracOfDemand['WI'] + stateSolarGenFracOfDemand['WI']/(endYear-1 - startYear) * (currYear - startYear)

        # Set maxmimum bound on solar and wind capacity for the current year
        allSolarMax = allSolarMaxBuild[currYear]

        # Set the maximum bound of solar capacity for each state and current year
        MI_cap = stateCap['MI'][currYear]
        IL_cap = stateCap['IL'][currYear]
        MN_cap = stateCap['MN'][currYear]
        IN_cap = stateCap['IN'][currYear]
        OH_cap = stateCap['OH'][currYear]
        WI_cap = stateCap['WI'][currYear]


        print('Entering year ', currYear, ' with CO2 cap (million tons):', round(currCo2Cap/1e6),'\t and renewable & clean generation requirement (%):',round(currReGenFracOfDemand),round(currCleanGenFracOfDemand))

        # Create results directory
        resultsDir = os.path.join(resultsDirAll, str(currYear) + 'CO2Cap' + str(int(currCo2Cap/1e6)))
        if not os.path.exists(resultsDir): os.makedirs(resultsDir)
        
        # Scale up demand profile if needed
        demandProfile = getDemandForFutureYear(demandProfile, annualDemandGrowth, metYear, currYear,
                                               electrifiedDemand, transRegions, elecDemandScen)
        demandProfile.to_csv(os.path.join(resultsDir,'demandPreProcessing'+str(currYear)+'.csv'))

        # Run CE
        if currYear > startYear and runCE:
            print('Starting CE')
            #Initialize results & inputs
            if currYear == startYear + yearStepCE: priorCEModel, priorHoursCE, genFleetPriorCE = None, None, None

            (genFleet, genFleetPriorCE, lineLimits,
             priorCEModel, priorHoursCE) = runCapacityExpansion(genFleet, demandProfile, startYear, endYear, yearStepCE, currYear, planningReserveMargin,
                                                                discountRate, fuelPrices, currCo2Cap,currReGenFracOfDemand,
                                                                currCleanGenFracOfDemand, solarMinBuildLoc, windMinBuildLoc, numBlocks, daysPerBlock, daysPerPeak,
                                                                fullYearCE, retirementCFCutoff, retireByAge, tzAnalysis, resultsDir,
                                                                maxCapPerTech, regLoadFrac, contLoadFrac, regErrorPercentile, flexErrorPercentile,
                                                                rrToRegTime, rrToFlexTime, rrToContTime, regElig, regCostFrac, ptEligRetCF,
                                                                genFleetPriorCE, priorCEModel, priorHoursCE, metYear, stoInCE, seasStoInCE,
                                                                ceOps, stoMkts, initSOCFraction, includeRes, reDownFactor, incNuc, demandShifter,
                                                                demandShiftingBlock, runOnSC, interconn, yearIncDACS, transRegions,
                                                                reTypeScenario, scenario_key, Land_use, zoningData, parcels, regions, power_density,jurisdiction,tracking, 
                                                                lineLimits, lineDists, lineCosts, contFlexInelig, ira, buildLimitsCase, 
                                                                electrifiedDemand, elecDemandScen, reSourceMERRA, stoFTLabels, transmissionEff, 
                                                                removeHydro,sitestoFilter, siteLeastCap,pRegionShapes,subdivShapes, countyShapes, states, 
                                                                costWgt, tx_distance, allSolarMax, solarMaxBuildLoc, MI_cap, IL_cap, MN_cap, IN_cap, OH_cap, WI_cap, scope, 
                                                                currMISolarGenFracOfDemand, currILSolarGenFracOfDemand, currMNSolarGenFracOfDemand, currINSolarGenFracOfDemand, 
                                                                currOHSolarGenFracOfDemand, currWISolarGenFracOfDemand, statesToDiscountCost, capex_discount_rate)

        # Run dispatch
        if (ucOrED != 'None') and ((currYear == startYear and runFirstYear) or (currYear > startYear)):
            print('Starting dispatch')
            runDispatch(genFleet, demandProfile, currYear, demandShifter, demandShiftingBlock, fuelPrices, currCo2Cap, useCO2Price,
                        tzAnalysis, resultsDir, stoMkts, metYear, regLoadFrac, contLoadFrac, interconn, regErrorPercentile, reSourceMERRA,
                        flexErrorPercentile, includeRes, rrToRegTime, rrToFlexTime, rrToContTime, regCostFrac,
                        ucOrED, initSOCFraction, includeRes)

# ###############################################################################
# ###############################################################################
# ###############################################################################

# ###############################################################################
# ###### SET UP INITIAL FLEET AND DEMAND ########################################
# ###############################################################################
def getInitialFleetDemandTransmission(startYear, fuelPrices, electrifiedDemand, elecDemandScen, compressFleet, 
        resultsDir, regElig, regCostFrac, metYear, stoMinSOC, greenField, interconn, balAuths, states,jurisdiction, contFlexInelig, 
        stoFTLabels, stoPTLabels, stoEff=0.81):

    # GENERATORS
    genFleet = setupGeneratorFleet(interconn, startYear, fuelPrices, stoEff, stoMinSOC, stoFTLabels)

    # DEFINE TRANSMISSION REGIONS
    transRegions = defineTransmissionRegions(interconn, balAuths, states)

    # DEMAND
    if electrifiedDemand: demand = importHourlyEFSDemand(startYear, transRegions, elecDemandScen) 
    else: sys.exit('If import non-EFS, need to map p-regions to demand region(s), & reflect in defineTransmissionRegions') #outdated function: importHourlyERCOTDemand(metYear)
    demand.to_csv(os.path.join(resultsDir, 'demandInitial.csv'))

    # TRANSMISSION
    genFleet, transRegions, limits, dists, costs, pRegionShapes, subdivShapes, countyShapes = setupTransmissionAndZones(genFleet, transRegions, interconn, balAuths, jurisdiction)
    for df, l in zip([limits, dists, costs],['Limits', 'Dists', 'Costs']): df.to_csv(os.path.join(resultsDir, 'transmission' + l + 'Initial.csv'))
    genFleet.to_csv(os.path.join(resultsDir, 'genFleetInitialPreCompression.csv'))

    # FINISH PROCESSING GENFLEET
    # Compress generators and add size dependent params (cost, reg offers, UC params)
    genFleet = compressAndAddSizeDependentParams(genFleet, compressFleet, regElig, contFlexInelig, regCostFrac, stoFTLabels, stoPTLabels)
    # If greenfield, elim existing generator fleet except tiny NG, wind, & solar plant (to avoid crash).
    # If not greenfield, extract hydropower units to factor out their generation from demand later. 
    if greenField: genFleet = stripDownGenFleet(genFleet, greenField)

    genFleet.to_csv(os.path.join(resultsDir,'genFleetInitial.csv'))

    return (genFleet, demand, transRegions, limits, dists, costs,pRegionShapes, subdivShapes, countyShapes)


# ###############################################################################
# ###############################################################################
# ###############################################################################

# ###############################################################################
# ###### RUN CAPACITY EXPANSION #################################################
# ###############################################################################

def runCapacityExpansion(genFleet, demand, startYear, endYear, yearStepCE, currYear, planningReserveMargin, discountRate, fuelPrices, 
                         currCo2Cap,currReGenFracOfDemand,currCleanGenFracOfDemand, solarMinBuildLoc, windMinBuildLoc, numBlocks,
                         daysPerBlock, daysPerPeak, fullYearCE, retirementCFCutoff, retireByAge, tzAnalysis, resultsDirOrig, maxCapPerTech,
                         regLoadFrac,contLoadFrac, regErrorPercentile, flexErrorPercentile, rrToRegTime, rrToFlexTime,  rrToContTime,
                         regElig, regCostFrac, ptEligRetCF, genFleetPriorCE, priorCEModel, priorHoursCE, metYear, stoInCE, seasStoInCE,
                         ceOps, stoMkts, initSOCFraction, includeRes, reDownFactor, incNuc, demandShifter, demandShiftingBlock, runOnSC,
                         interconn, yearIncDACS, transRegions, reTypeScenario,scenario_key, Land_use, zoningData, parcels, regions, 
                         power_density, jurisdiction, tracking, lineLimits, lineDists, lineCosts, contFlexInelig, ira, buildLimitsCase, 
                         electrifiedDemand, elecDemandScen, reSourceMERRA, stoFTLabels, transmissionEff, removeHydro, sitestoFilter, 
                         siteLeastCap,pRegionShapes,subdivShapes, countyShapes, states, costWgt, tx_distance, allSolarMax, solarMaxBuildLoc,
                         MI_cap, IL_cap, MN_cap, IN_cap, OH_cap, WI_cap, scope, currMISolarGenFracOfDemand, currILSolarGenFracOfDemand, currMNSolarGenFracOfDemand, 
                         currINSolarGenFracOfDemand, currOHSolarGenFracOfDemand, currWISolarGenFracOfDemand, statesToDiscountCost, capex_discount_rate):
    # Create results directory and save initial inputs
    resultsDir = os.path.join(resultsDirOrig, 'CE')
    if not os.path.exists(resultsDir): os.makedirs(resultsDir)
    print('Entering CE loop for year ' + str(currYear))
    lineLimits.to_csv(os.path.join(resultsDir,'lineLimitsForCE' + str(currYear) + '.csv'))
    pd.Series(maxCapPerTech).to_csv(os.path.join(resultsDir,'buildLimitsForCE' + str(currYear) + '.csv'))
    pd.Series(currCo2Cap).to_csv(os.path.join(resultsDir,'co2CapCE' + str(currYear) + '.csv'))
    pd.Series(currReGenFracOfDemand).to_csv(os.path.join(resultsDir,'solarMinGenCE' + str(currYear) + '.csv'))
    pd.Series(currCleanGenFracOfDemand).to_csv(os.path.join(resultsDir,'windMinGenCE' + str(currYear) + '.csv'))
    pd.Series(
    {
        'MI': currMISolarGenFracOfDemand,
        'IL': currILSolarGenFracOfDemand,
        'MN': currMNSolarGenFracOfDemand,
        'IN': currINSolarGenFracOfDemand,
        'OH': currOHSolarGenFracOfDemand,
        'WI': currWISolarGenFracOfDemand
    }).to_csv(os.path.join(resultsDir,'solarMinStateGenCE' + str(currYear) + '.csv'))
      
 

    # Update new technology and fuel price data    
    newTechsCE = getNewTechs(regElig, regCostFrac, currYear, stoInCE, seasStoInCE,
                             fuelPrices, yearIncDACS, incNuc, transRegions, contFlexInelig, ira, lbToShortTon)

    genFleet = updateFuelPricesAndCosts(genFleet, currYear, fuelPrices, regCostFrac)

    # Retire units and create fleet for current CE loop
    if priorCEModel != None:                    # if not in first CE loop
        genFleet = retireUnitsCFPriorCE(genFleet, genFleetPriorCE, retirementCFCutoff,
            priorCEModel, priorHoursCE, ptEligRetCF, currYear)
    genFleet, genFleetForCE = createFleetForCurrentCELoop(genFleet, currYear, retireByAge)
    genFleetForCE.to_csv(os.path.join(resultsDir, 'genFleetForCEPreRECombine' + str(currYear) + '.csv'))
    
    # # Combine wind and solar by subdivision and storage plants by region
    genFleetForCE = combineWindSolarStoPlants(genFleetForCE)
    genFleetForCE = combineOnlyWS(genFleetForCE)

    # Get renewable CFs from MERRA or non-MERRA data by plant and region and calculate net demand by region
    print('Loading RE data')

    windGen, solarGen, windGenRegion, solarGenRegion = getREGen(genFleet, tzAnalysis, metYear, currYear, reSourceMERRA, jurisdiction, tracking, pRegionShapes)
    netDemand = demand - windGenRegion - solarGenRegion
    

    # Remove hydropower generation from demand using net-demand-based heuristic
    genFleetForCE,hydroGen,demand = processHydro(genFleetForCE, demand, netDemand, metYear, removeHydro) # If running greenfield, skip step where get rid of hydro (since none in fleet).
    genFleetForCE.to_csv(os.path.join(resultsDir, 'genFleetForCE' + str(currYear) + '.csv'))

    # Get hours included in CE model (representative + special blocks)
    (hoursForCE, planningReserve, blockWeights, socScalars, peakDemandHour, blockNamesChronoList, 
        lastRepBlockNames, specialBlocksPrior) = getHoursForCE(demand, netDemand, daysPerBlock, daysPerPeak, fullYearCE, 
                                                               currYear, resultsDir, numBlocks, planningReserveMargin)
    
    # Get CFs for new wind and solar sites and add wind & solar sites to newTechs
    newCfs, maxCapWind, maxCapSolar = getNewRenewableCFs(genFleet, tzAnalysis, metYear, currYear, reDownFactor, 
                                reSourceMERRA, scenario_key, reTypeScenario, Land_use, zoningData, parcels, regions,
                                power_density, sitestoFilter, siteLeastCap, jurisdiction, tracking, pRegionShapes,states, tx_distance, startYear, endYear, yearStepCE)

    newTechsCE, newCfs,sitesDf = addWSSitesToNewTechs(newCfs,maxCapWind, maxCapSolar, newTechsCE, pRegionShapes,subdivShapes, countyShapes, reTypeScenario, currYear, jurisdiction)

    # Discount cost for Specific States
    # newTechsCE = discountCapexForState(newTechsCE, statesToDiscountCost, currYear, capex_discount_rate)

    maxCapWind.to_csv(os.path.join(resultsDir,'buildWindLimitsForCE' + str(currYear) + '.csv'))
    maxCapSolar.to_csv(os.path.join(resultsDir,'buildSolarLimitsForCE' + str(currYear) + '.csv'))

    # Initialize which generators are on or off at start of each block of hours (useful if CE has UC constraints)
    onOffInitialEachPeriod = initializeOnOffExistingGens(genFleetForCE, hoursForCE, netDemand)

    # Set reserves for existing and incremental reserves for new generators
    print('Calculating reserves')
    if includeRes:
        cont, regUp, flex, regDemand, regUpSolar, regUpWind, flexSolar, flexWind = calcWWSISReserves(windGenRegion, solarGenRegion, demand, regLoadFrac,
                                                                                                     contLoadFrac, regErrorPercentile, flexErrorPercentile)
        regUpInc, flexInc = getIncResForAddedRE(newCfs, regErrorPercentile, flexErrorPercentile)
    else:
        cont, regUp, flex, regDemand, regUpSolar, regUpWind, flexSolar, flexWind, regUpInc, flexInc = createEmptyReserveDfs(windGenRegion, newCfs)

    # Get timeseries hours for CE (demand, wind, solar, new wind, new solar, reserves) & save dfs
    (demandCE, windGenCE, solarGenCE, newCfsCE, contCE, regUpCE, flexCE, regUpIncCE, 
        flexIncCE) = isolateDataInCEHours(hoursForCE, demand, windGenRegion, solarGenRegion,
                                        newCfs, cont, regUp, flex, regUpInc, flexInc)
    # Get total hydropower generation potential by block for CE
    [hydroGenCE] = isolateDataInCEBlocks(hoursForCE,hydroGen)

    # Save CE inputs
    for df, n in zip([windGen, solarGen, windGenRegion, solarGenRegion, newCfs, demand, netDemand, cont, regUp,
                      flex, regUpInc, flexInc, regDemand, regUpSolar, regUpWind, flexSolar, flexWind, hydroGen],
                     ['windGen','solarGen','windGenRegion','solarGenRegion','windSolarNewCFs','demand','netDemand',
                      'contRes','regUpRes','flexRes','regUpInc','flexInc','regUpDemComp','regUpSolComp',
                      'regUpWinComp','flexSolComp','flexWinComp','hydroGen']):
        df.to_csv(os.path.join(resultsDir, n + 'FullYr' + str(currYear) + '.csv'))
    for df, n in zip([demandCE, windGenCE, solarGenCE, newCfsCE, newTechsCE, contCE, regUpCE, flexCE, regUpIncCE, flexIncCE,hydroGenCE],
                     ['demand', 'windGen', 'solarGen','windAndSolarNewCFs','newTechs','contRes','regUpRes','flexRes', 'regUpInc', 'flexInc', 'hydroGen']):
        df.to_csv(os.path.join(resultsDir, n + 'CE' + str(currYear) + '.csv'))
    hoursForCE.to_csv(os.path.join(resultsDir, 'hoursCEByBlock' + str(currYear) + '.csv'))
    pd.Series(planningReserve).to_csv(os.path.join(resultsDir,'planningReserveCE' + str(currYear) + '.csv'))
    pd.DataFrame([[k, v] for k, v in socScalars.items()],columns=['block','scalar']).to_csv(os.path.join(resultsDir,'socScalarsCE' + str(currYear) + '.csv'))

    # ######### RUN CAPACITY EXPANSION
    print('Running CE for ' + str(currYear))
    ws, db, gamsFileDir = createGAMSWorkspaceAndDatabase(runOnSC)
    writeTimeDependentConstraints(blockNamesChronoList, stoInCE, seasStoInCE, gamsFileDir, ceOps, lastRepBlockNames, specialBlocksPrior, removeHydro)
    writeBuildVariable(ceOps, gamsFileDir)
    genSet, hourSet, hourSymbols, zoneOrder, lineSet, zoneSet = edAndUCSharedFeatures(db, genFleetForCE, hoursForCE, demandCE, contCE,regUpCE,flexCE,
                                                                             demandShifter, demandShiftingBlock, rrToRegTime, rrToFlexTime, rrToContTime,
                                                                             solarGenCE, windGenCE, transRegions, lineLimits, transmissionEff)  
    stoGenSet, stoGenSymbols = storageSetsParamsVariables(db, genFleetForCE, stoMkts, stoFTLabels)
    stoTechSet, stoTechSymbols = ceSharedFeatures(db, peakDemandHour, genFleetForCE, newTechsCE, planningReserve, discountRate, currCo2Cap,
                                                  currReGenFracOfDemand, currCleanGenFracOfDemand,solarMinBuildLoc, windMinBuildLoc, hourSet, hourSymbols, newCfsCE, maxCapPerTech, 
                                                  regUpIncCE, flexIncCE, stoMkts, lineDists, lineCosts, lineSet, zoneOrder, ceOps, interconn, 
                                                  buildLimitsCase, stoFTLabels, costWgt, allSolarMax, solarMaxBuildLoc, MI_cap, IL_cap, MN_cap, IN_cap, OH_cap, WI_cap, 
                                                  currMISolarGenFracOfDemand, currILSolarGenFracOfDemand, currMNSolarGenFracOfDemand, 
                                                  currINSolarGenFracOfDemand, currOHSolarGenFracOfDemand, currWISolarGenFracOfDemand)
    if ceOps == 'UC': ucFeatures(db, genFleetForCE, genSet),
    ceTimeDependentConstraints(db, hoursForCE, blockWeights, socScalars, ceOps, onOffInitialEachPeriod, 
                genSet, genFleetForCE, stoGenSet,stoGenSymbols, newTechsCE, stoTechSet, stoTechSymbols, initSOCFraction,
                hydroGenCE, zoneSet)

    if scope == "RE_Clean":
        capacExpModel, ms, ss = runGAMS('Clean_CEWith{o}.gms'.format(o=ceOps), ws, db)

    # ########## SAVE AND PROCESS CE RESULTS
    pd.Series([ms,ss],index=['ms','ss']).to_csv(os.path.join(resultsDir, 'msAndSsCE' + str(currYear) + '.csv'))
    saveCapacExpOperationalData(capacExpModel, genFleetForCE, newTechsCE, hoursForCE, transRegions, lineLimits, resultsDir, 'CE', currYear)
    newGens,newStoECap,newStoPCap,newLines = saveCEBuilds(capacExpModel, resultsDir, currYear)

    
    genFleet = addNewGensToFleet(genFleet, newGens, newStoECap, newStoPCap, newTechsCE, currYear)
    lineLimits = addNewLineCapToLimits(lineLimits, newLines)
    genFleet.to_csv(os.path.join(resultsDir, 'genFleetAfterCE' + str(currYear) + '.csv'))
    lineLimits.to_csv(os.path.join(resultsDir, 'lineLimitsAfterCE' + str(currYear) + '.csv'))

    return (genFleet, genFleetForCE, lineLimits, capacExpModel, hoursForCE)

# ###############################################################################
# ###############################################################################
# ###############################################################################

# ###############################################################################
# ################## GAMS FUNCTIONS #############################################
# ###############################################################################
def createGAMSWorkspaceAndDatabase(runOnSC):
    # currDir = os.getcwd()
    if runOnSC:
        gamsFileDir = 'GAMS'
        gamsSysDir = '/home/owusup/gams40_4'
    else:
        gamsFileDir = 'C:\\Users\\owusup\Desktop\\Model\\MacroCEM_EIM\\GAMS'
        gamsSysDir = 'C:\\GAMS\\40'
    ws = GamsWorkspace(working_directory=gamsFileDir, system_directory=gamsSysDir)
    db = ws.add_database()
    return ws, db, gamsFileDir

def runGAMS(gamsFilename, ws, db):
    t0 = time.time()
    model = ws.add_job_from_file(gamsFilename)
    opts = GamsOptions(ws)
    opts.defines['gdxincname'] = db.name
    model.run(opts, databases=db)
    ms, ss = model.out_db['pModelstat'].find_record().value, model.out_db['pSolvestat'].find_record().value
    if (int(ms) != 8 and int(ms) != 1) or int(ss) != 1: print('*********Modelstat & solvestat:', ms, ' & ', ss, ' (ms1 global opt, ms8 int soln, ss1 normal)')
    print('Time (mins) for GAMS run: ' + str(round((time.time()-t0)/60)))
    return model, ms, ss

def edAndUCSharedFeatures(db, genFleet, hours, demand, contRes, regUpRes, flexRes, demandShifter, demandShiftingBlock, rrToRegTime, rrToFlexTime,
                          rrToContTime, hourlySolarGen, hourlyWindGen, transRegions, lineLimits, transmissionEff, cnse=10000, co2Price=0):
    # SETS
    genSet = addGeneratorSets(db, genFleet)
    hourSet, hourSymbols = addHourSet(db, hours)
    zoneSet,zoneSymbols,zoneOrder = addZoneSet(db, transRegions)

    lineSet,lineSymbols = addLineSet(db, lineLimits)

    # PARAMETERS
    # Demand and reserves
    addDemandParam(db, demand, hourSet, zoneSet, demandShifter, demandShiftingBlock, mwToGW)
    addReserveParameters(db, contRes, regUpRes, flexRes, rrToRegTime, rrToFlexTime, rrToContTime, hourSet, zoneSet, mwToGW)

    # CO2 cap or price
    addCo2Price(db, co2Price)

    # Generators
    addGenParams(db, genFleet, genSet, mwToGW, lbToShortTon, zoneOrder)
    addExistingRenewableMaxGenParams(db, hourSet, zoneSet, hourlySolarGen, hourlyWindGen, mwToGW)
    addSpinReserveEligibility(db, genFleet, genSet)
    addCostNonservedEnergy(db, cnse)

    # Transmission lines
    addLineParams(db,lineLimits, transmissionEff, lineSet, zoneOrder, mwToGW)
    return genSet, hourSet, hourSymbols, zoneOrder, lineSet, zoneSet

def storageSetsParamsVariables(db, genFleet, stoMkts, stoFTLabels):
    (stoGenSet, stoGenSymbols) = addStoGenSets(db, genFleet, stoFTLabels)
    addStorageParams(db, genFleet, stoGenSet, stoGenSymbols, mwToGW, stoMkts)
    return stoGenSet, stoGenSymbols

def ed(db, socInitial, stoGenSet):
    addStorageInitSOC(db, socInitial, stoGenSet, mwToGW)

def ucFeatures(db, genFleet, genSet):
    addGenUCParams(db, genFleet, genSet, mwToGW)
    
def uc(db, stoGenSet, genSet, socInitial, onOffInitial, genAboveMinInitial, mdtCarriedInitial):
    addStorageInitSOC(db, socInitial, stoGenSet, mwToGW)
    addEguInitialConditions(db, genSet, onOffInitial, genAboveMinInitial, mdtCarriedInitial, mwToGW)

def ceSharedFeatures(db, peakDemandHour, genFleet, newTechs, planningReserve, discountRate,
        co2Cap,currReGenFracOfDemand,currCleanGenFracOfDemand, solarMinBuildLoc, windMinBuildLoc, hourSet, hourSymbols, newCfs, maxCapPerTech, regUpInc, flexInc, stoMkts, 
        lineDists, lineCosts, lineSet, zoneOrder, ceOps, interconn, buildLimitsCase, stoFTLabels,costWgt, allSolarMax, solarMaxBuildLoc, 
        MI_cap, IL_cap, MN_cap, IN_cap, OH_cap, WI_cap, currMISolarGenFracOfDemand, currILSolarGenFracOfDemand, currMNSolarGenFracOfDemand,
        currINSolarGenFracOfDemand, currOHSolarGenFracOfDemand, currWISolarGenFracOfDemand):
    # Sets
    addPeakHourSubset(db, peakDemandHour)
    addStorageSubsets(db, genFleet, stoFTLabels)
    (techSet, renewTechSet, windTechSet, solarTechSet, stoTechSet, stoTechSymbols, thermalSet, dacsSet, CCSSet) = addNewTechsSets(db, newTechs)

    # Long-term planning parameters
    addPlanningReserveParam(db, planningReserve, mwToGW)
    addDiscountRateParam(db, discountRate)
    addCO2Cap(db, co2Cap)

    # Add minimum bound on renewable generation
    addREMinGen(db, currReGenFracOfDemand)
    addCleanMinGen(db, currCleanGenFracOfDemand)

    # Add minimum bound on renewable generation for each state
    # addStateSolarMinGen(db, currMISolarGenFracOfDemand, currILSolarGenFracOfDemand, currMNSolarGenFracOfDemand, currINSolarGenFracOfDemand, 
    #                     currOHSolarGenFracOfDemand, currWISolarGenFracOfDemand)

    # include the params for objective weights
    if costWgt == None:
        costWgt = 1
    bnftWgt = 1 - costWgt
    addObjWeightsParams(db, costWgt, bnftWgt)

    # Add max and min solar and wind capacity that can be built for each jurisdiction
    addSolarMaxBuildParams(db, solarMaxBuildLoc)
    addSolarMinCap(db, solarMinBuildLoc)
    addWindMinCap(db, windMinBuildLoc)

    # Add max solar build for all jurisdictions
    addAllSolarMaxBuildParams(db, allSolarMax)

    # Add maximum solar build for each state
    # addStateSolarMaxBuildParams(db, MI_cap, IL_cap, MN_cap, IN_cap, OH_cap, WI_cap)

    # Add transmission cost for new solar and wind sites
    addNewRenewTxCostParams(db,newTechs,renewTechSet,mwToGW)

    # Add solar local economic impacts
    addEconomicImpactParams(db,newTechs,solarTechSet,mwToGW)

    # New tech parameters
    addGenParams(db, newTechs, techSet, mwToGW, lbToShortTon, zoneOrder, True)
    addTechCostParams(db, newTechs, techSet, stoTechSet, mwToGW)
    addRenewTechCFParams(db, renewTechSet, hourSet, newCfs)
    addMaxNewBuilds(db, newTechs, windTechSet, solarTechSet, thermalSet, stoTechSet, dacsSet, CCSSet, maxCapPerTech, mwToGW)

    if ceOps == 'UC': addGenUCParams(db, newTechs, techSet, mwToGW, True)
    addResIncParams(db, regUpInc, flexInc, renewTechSet, hourSet)
    addSpinReserveEligibility(db, newTechs, techSet, True)
    addStorageParams(db, newTechs, stoTechSet, stoTechSymbols, mwToGW, stoMkts, True)
    addNewLineParams(db, lineDists, lineCosts, lineSet, maxCapPerTech, buildLimitsCase, zoneOrder, interconn, mwToGW)
    return stoTechSet, stoTechSymbols

def ceTimeDependentConstraints(db, hoursForCE, blockWeights, socScalars, ceOps, onOffInitialEachPeriod,
        genSet, genFleet, stoGenSet, stoGenSymbols, newTechs, stoTechSet, stoTechSymbols, 
        initSOCFraction, hydroGenCE, zoneSet):
    addHourSubsets(db, hoursForCE)
    addSeasonDemandWeights(db, blockWeights)
    addBlockSOCScalars(db, socScalars)
    if ceOps == 'UC': addInitialOnOffForEachBlock(db, onOffInitialEachPeriod, genSet)
    addStoInitSOCCE(db, genFleet, stoGenSet, stoGenSymbols, mwToGW, initSOCFraction)
    addStoInitSOCCE(db, newTechs, stoTechSet, stoTechSymbols, mwToGW, initSOCFraction, True)
    addHydroGenLimits(db, hydroGenCE, zoneSet, mwToGW)
############################################################################################################