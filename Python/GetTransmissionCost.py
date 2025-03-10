import pandas as pd
import os
#Functions to:
#1. Get transmission costs 
#2. Get least cost option for each subdiv for current year


# currYear = 2020
# jurisdiction = 'county'

#Get transmission cost for current year
def getTransCost(currYear, jurisdiction):
    if currYear > 2050: currYear = 2050
    AllTransCost = getLeastTransCost()
    AllTransCost['Tx_Cost ($/MW-yr)'] = AllTransCost[f'{currYear}' + '_Tx_Cost ($/MW-yr)']
    if jurisdiction == 'county':
        TransCostCounty = AllTransCost[['GEOID', 'Tx_Cost ($/MW-yr)', 'Line distance(miles)']]
        TransCostCounty['GEOID'] = TransCostCounty['GEOID'].astype(str).str[:5].astype(int)  
        TransCostCounty = TransCostCounty.groupby('GEOID').agg({ 'Tx_Cost ($/MW-yr)': 'mean',
                                                                'Line distance(miles)': 'mean'
                                                                 }).reset_index()
        return TransCostCounty
    else:
        return AllTransCost[['GEOID','Tx_Cost ($/MW-yr)','line rating(kV)','Line distance(miles)']]

#get the least cost of transmission for each resource point
def getLeastTransCost():
    AllTransCost = importTxData()
    AllTransCost['2020_Tx_Cost ($/MW-yr)'] = AllTransCost['Line cost($/MW)']
    AllTransCost.drop(columns = ['Line cost($/MW)'], inplace = True)
    # Project transmission cost based on percentage change in CPI between 2012 to 2020, value estimated at 0.15% 
    # https://www.in2013dollars.com/us/inflation/2012?amount=1
    for year in range(2021,2051):
        prev_year = year - 1
        AllTransCost[f'{year}' + '_Tx_Cost ($/MW-yr)'] = AllTransCost[f'{prev_year}' + '_Tx_Cost ($/MW-yr)'] * 1.015
    return AllTransCost   

#read input coefficients for LCOE
def importTxData():
    transCosts = pd.read_csv(os.path.join('Data','Transmission_cost','Final',
                                            'least_cost_distance_rating_tx.csv'))
    return transCosts










########################################### OLD CODE #########################################################

# #Get transmission cost for current year
# def getTransCost(currYear, jurisdiction):
#     if currYear > 2050: currYear = 2050
#     AllTransCost = getLeastTransCost()
#     AllTransCost['Tx_Cost ($/MW-yr)'] = AllTransCost[f'{currYear}' + '_Tx_Cost ($/MW-yr)']
#     if jurisdiction == 'county':
#         TransCostCounty = AllTransCost[['GEOID', 'Tx_Cost ($/MW-yr)']]
#         TransCostCounty['GEOID'] = TransCostCounty['GEOID'].astype(str).str[:5].astype(int)  
#         TransCostCounty = TransCostCounty.groupby('GEOID')['Tx_Cost ($/MW-yr)'].mean().reset_index()
#         return TransCostCounty
#     else:
#         return AllTransCost[['GEOID','Tx_Cost ($/MW-yr)']]

# #get the least cost of transmission for each resource point
# def getLeastTransCost():
#     AllTransCost = importTxData()
#     AllTransCost['2020_Tx_Cost ($/MW-yr)'] = AllTransCost.apply(find_min_cost, axis=1)
#     # Project transmission cost based on percentage change in CPI between 2012 to 2020, value estimated at 0.15% 
#     # https://www.in2013dollars.com/us/inflation/2012?amount=1
#     for year in range(2021,2051):
#         prev_year = year - 1
#         AllTransCost[f'{year}' + '_Tx_Cost ($/MW-yr)'] = AllTransCost[f'{prev_year}' + '_Tx_Cost ($/MW-yr)'] * 1.015
#     return AllTransCost   

# #read input coefficients for LCOE
# def importTxData():
#     transCosts = pd.read_csv(os.path.join('Data','Transmission_cost','Final',
#                                             'Subdiv_Transmission_Cost.csv'), index_col=0)
#     return transCosts

# #read least transmission cost for each subdiv
# def find_min_cost(row):
#     costs = [row['<100'], row['100-161'], row['220-287'], row['345'], row['>500']]
#     return min(costs)


