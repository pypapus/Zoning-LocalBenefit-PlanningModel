# NOT USED

import pandas as pd, numpy as np, os
from getZoningData import getZoningdata

np.random.seed(seed=0)

def runAnalysis():
    stateFIPS = {'MN':27,'MI':26,'IN':18,'OH':39,'WI':55, 'IL':17}
    subdivs = pd.read_csv(os.path.join('Data','Parcel_Data','countsubs.csv'),header=0,index_col=0) #units for area in square meter
    
    #zoning_Data = call function to import zoning data. Database will be imported as a nested dictionary of geoids(representing subdivs) and values

    for state,fip in stateFIPS.items():
        print(state)
        generateParcels(state,subdivs.loc[subdivs['STATEFP']==fip]) #include arguments: zoning_data


#Scenario 1: generate parcels and land area in each geoid for all principal-use (Yes) and township permit(Yes)
def generateParcels(state,stateSubdivs): #include argument for: zoning_data
    parcels = pd.read_excel(os.path.join('Data','Parcel_Data','parcel area summary_v2.xlsx'),sheet_name=state,header=0,index_col=0)

    #1. read "subdivision Length" data 
    # (where for each subdiv I have parcel length grouped under percentiles, and another column with the total length of each subdiv)
    # subdivLength = pd.read_csv('subdivLength.csv')

    for subdiv in stateSubdivs['GEOID'].values:

        #here i can generated different scenarios based on whether i want to run all subdivs in zoning database, only subdivs that allow solar,etc.
        #pseudocode:
        #scenario1_list = call(function that that provides a list of subdivs from the zoning database based on a criteria)
        #if subdivs in scenario1_list: 

            subdivArea = stateSubdivs.loc[stateSubdivs['GEOID']==subdiv,'ALAND'].values[0]

            #In addition to obtaining the area of each subdivision, i will also obtain the length
            #subdivLength = subdivLength.loc[subdivLength['GEOID']==subdiv,'length'].values[0]

            if subdiv in parcels.index:
                subdivParcels = parcels.loc[subdiv]

                #I will also select the "subdiv" in my subdivLength data
                #subdivLength = subdivLength.loc[subdiv]

                subdivParcels = getSubdivParcels(subdiv,subdivArea,subdivParcels) #I will include two arguments: 1. subdivLenght 2. ZoningData

                #sum parcels for county subd.

        
            else:
                print(str(subdiv) + ' not in parcel data!')


def getSubdivParcels(subdiv,subdivArea,subdivParcels,errorMargin=.05):  #I will include two arguments: 1. subdivLenght 2. ZoningData
    parcelAreas,parcels,ctr = 0,list(),0
    subdivParcels,numParcels = subdivParcels[['p1','p5','p10','p25','p50','p75','p90','p95','p99']],subdivParcels['N']
   
    #here i will include code to get three key imputs:
    #1. percentiles of subdivs parcel lengths
    #2. actual subdiv length

    #code:
    #percentile_length = get lengths under percentiles [['p1','p5','p10','p25','p50',..., p99]]
    #actual_subdiv_length = get length for a single subdivision

    #If just 1 parcel, set parcel size to be subdivision area
    if numParcels == 1:
        parcels = [subdivArea]
        #here I will include code to: 
        # 1. Calculate setback area using setback distance and length of subdivision
        # 2. Subtract setback of area from area of parcel
        #code:
        #setback area = actual_subdiv_length * zoning_Data[subdiv]["setback_distance"] 
        #parcel_minus_setback = parcels - setback area
        #parcels = parcel_minus_setback

    #If more than 1 parcel, iteratively add parcels until fill county subdivision land area (with a certain margain of error)
    else:
        while parcelAreas < subdivArea*(1-errorMargin):
            uni = np.random.uniform()
            if uni < .01: 
                parcel = subdivParcels['p1']

                #here I will include code to: 1. get length under 10 percentile 2. calculate setback area and subtract from parcel area
                #code:
                #parcel_length = percentile_length['p1']
                #setback area = parcel_length * zoning_Data[subdiv]["setback_distance"] 
                #parcel_minus_setback = parcels - setback area
                #parcel = parcel_minus_setback
                           
            elif uni < .05: 
                parcel = subdivParcels['p5']

                #here I will include code to: 1. get length under 10 percentile 2. calculate setback area and subtract from parcel area
                #code:
                #parcel_length = percentile_length['p5']
                #setback area = parcel_length * zoning_Data[subdiv]["setback_distance"] 
                #parcel_minus_setback = parcels - setback area
                #parcel = parcel_minus_setback

            elif uni < .1:
                parcel = subdivParcels['p10']
                #i will repeat code above gor 'p10'
            if uni < .25: 
                parcel = subdivParcels['p25']
                #i will repeat code above for 'p125'
            elif uni < .5:
                parcel = subdivParcels['p50']
                #i will repeat code above for 'p50'                
            if uni < .75: 
                parcel = subdivParcels['p75']
                #i will repeat code above for 'p75'                
            elif uni < .9:
                parcel = subdivParcels['p90']
                #i will repeat code above for 'p90'                
            if uni < .95: 
                parcel = subdivParcels['p95']
                #i will repeat code above for 'p95'
            else:
                parcel = subdivParcels['p99']
                #i will repeat code above for 'p99'

            if parcelAreas + parcel < (1+errorMargin)*subdivArea:
                parcels.append(parcel)
                parcelAreas += parcel
            #For subdivisions with very small # parcels (like 2 or 3), can get stuck in while loop. If iterate 10X times # of parcels in subdivision, just give up
            if ctr == numParcels*10: break
            ctr += 1
        parcels = [p * subdivArea/parcelAreas for p in parcels]
    return parcels

runAnalysis() #analysis to be run for various scenarios
