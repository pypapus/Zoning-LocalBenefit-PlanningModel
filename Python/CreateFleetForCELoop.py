#Michael Craig
#October 4, 2016
#Create fleet for current CE loop by removing retired units from fleet. 
#Determines which units retire due to age, and also accounts for past retirements
#for age and economic reasons.

import os, copy, pandas as pd

################## CREATE FLEET FOR CURRENT CE LOOP ############################
#Inputs: gen fleet (2d list), current CE year, list of units retired each year (2d list)
#Outputs: gen fleet w/ retired units removed (2d list)
def createFleetForCurrentCELoop(genFleet,currYear,retireByAge):
    if currYear > 2050: currYear = 2050
    if retireByAge: genFleet = markAndSaveRetiredUnitsFromAge(genFleet,currYear)
    genFleetForCE = getOnlineGenFleet(genFleet,currYear)
    return genFleet,genFleetForCE

def getOnlineGenFleet(genFleet,currYear):
    if currYear > 2050: currYear = 2050
    genFleetForCE = genFleet.copy()
    genFleetForCE = genFleetForCE.loc[genFleetForCE['On Line Year']<=currYear]
    genFleetForCE = genFleetForCE.loc[genFleetForCE['Retirement Year']>currYear]
    genFleetForCE = genFleetForCE.loc[genFleetForCE['Retired']==False]
    return genFleetForCE

#Marks units that retire in gen fleet and saves them in list
def markAndSaveRetiredUnitsFromAge(genFleet,currYear):
    if currYear > 2050: currYear = 2050
    lifetimes = pd.read_csv(os.path.join('Data','LifetimesExistingPlants.csv'),index_col=0)['Lifetime(yrs)'].to_dict()
    lifetimes = genFleet['PlantType'].map(lifetimes)
    retirements = (lifetimes + genFleet['On Line Year']) < currYear
    retirements = retirements.loc[genFleet['Retired']==False]
    retirements = retirements[retirements==True]
    genFleet.loc[retirements.index,'YearRetiredByAge'] = currYear
    genFleet.loc[retirements.index,'Retired'] = True
    retirements = (genFleet.loc[retirements.index,'ORIS Plant Code'].astype(str) + "+" +     
                    genFleet.loc[retirements.index,'Unit ID']).tolist()
    # capacExpRetiredUnitsByAge.append(['UnitsRetiredByAge' + str(currYear)] + retirements)
    return genFleet
################################################################################
