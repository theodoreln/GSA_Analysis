import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import gams.transfer as gt
import pybalmorel as pyb
import gams
import os
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from io import StringIO

#### Useful dictionnaries #####

RRR_to_CCC = {
    'DK1': 'DENMARK','DK2': 'DENMARK','FIN': 'FINLAND','NO1': 'NORWAY','NO2': 'NORWAY','NO3': 'NORWAY','NO4': 'NORWAY','NO5': 'NORWAY','SE1': 'SWEDEN',
    'SE2': 'SWEDEN', 'SE3': 'SWEDEN','SE4': 'SWEDEN','UK': 'UNITED_KINGDOM','EE': 'ESTONIA','LV': 'LATVIA','LT': 'LITHUANIA','PL': 'POLAND','BE': 'BELGIUM',
    'NL': 'NETHERLANDS','DE4-E': 'GERMANY','DE4-N': 'GERMANY','DE4-S': 'GERMANY','DE4-W': 'GERMANY','FR': 'FRANCE','IT': 'ITALY','CH': 'SWITZERLAND',
    'AT': 'AUSTRIA','CZ': 'CZECH_REPUBLIC','ES': 'SPAIN','PT': 'PORTUGAL','SK': 'SLOVAKIA','HU': 'HUNGARY','SI': 'SLOVENIA','HR': 'CROATIA','RO': 'ROMANIA',
    'BG': 'BULGARIA','GR': 'GREECE','IE': 'IRELAND','LU': 'LUXEMBOURG','AL': 'ALBANIA','ME': 'MONTENEGRO', 'MK': 'NORTH_MACEDONIA',
    'BA': 'BOSNIA_AND_HERZEGOVINA','RS': 'SERBIA','TR': 'TURKEY','MT': 'MALTA','CY': 'CYPRUS'
}

TECHT_to_TECHG = {
    'WIND-ON': 'WINDTURBINE_ONSHORE', 'WIND-OFF' : 'WINDTURBINE_OFFSHORE', 'SOLAR-PV' : 'SOLARPV'
}

Regions_name = {
    ('DENMARK', 'NORWAY', 'SWEDEN', 'FINLAND', 'ESTONIA', 'LATVIA', 'LITHUANIA') : 'Northern Europe',
    ('FRANCE', 'GERMANY', 'NETHERLANDS', 'UNITED-KINGDOM', 'BELGIUM', 'LUXEMBOURG', 'AUSTRIA', 'SWITZERLAND', 'IRELAND') : 'Western Europe',
    ('POLAND', 'CZECH_REPUBLIC', 'SLOVAKIA', 'ROMANIA', 'BULGARIA', 'HUNGARY') : 'Eastern Europe',
    ('ITALY', 'SPAIN', 'PORTUGAL', 'SLOVENIA', 'CROATIA', 'ALBANIA', 'MALTA', 'CYPRUS', 'BOSNIA_AND_HERZEGOVINA', 'MONTENEGRO', 'NORTH_MACEDONIA', 'SERBIA', 'GREECE') : 'Southern Europe'
}

#### Input Data functions ####

# Function to import the table from the input data file
def Import_Data(file_path) :
    
    df_merged = gt.Container(file_path)
    df_SUBTECH    = pd.DataFrame(df_merged.data["SUBTECHGROUPKPOT"].records)
    SUBTECH_headers        = ['scenarios', 'CCCRRRAAA', 'TECH_GROUP', 'SUBTECHGROUP', 'value']
    df_SUBTECH.columns       = SUBTECH_headers
    df_SUBTECH = df_SUBTECH.dropna()
    df_SUBTECH['scenarios'] = df_SUBTECH['scenarios'].str.extract(r'(\d+)').astype(int)

    return df_SUBTECH

def LIM_RE_CAP_scen(df_SUBTECH) :
    
    df_SUBTECH['C'] = df_SUBTECH['CCCRRRAAA'].map(RRR_to_CCC)
    df_RE_SUBTECH = df_SUBTECH.groupby(['scenarios','C','TECH_GROUP'])['value'].sum().reset_index()
    df_RE_SUBTECH['value'] = df_RE_SUBTECH['value']/1000
    
    return df_RE_SUBTECH


#### Main Results functions ####

# Function to import the table from the MainResults file
def Import_MainResults(file_path) :
    
    df = gt.Container(file_path)
    df_PRO = pd.DataFrame(df.data["PRO_YCRAGF"].records)
    df_CAP = pd.DataFrame(df.data["G_CAP_YCRAF"].records)
    df_XH2_CAP = pd.DataFrame(df.data["XH2_CAP_YCR"].records)
    df_XH2_FLOW = pd.DataFrame(df.data["XH2_FLOW_YCR"].records)
    df_PRO_STO = pd.DataFrame(df.data["G_STO_YCRAF"].records)
    
    return df_PRO, df_CAP, df_XH2_CAP, df_XH2_FLOW, df_PRO_STO

# Function to import the CCS table from the MainResults file
def Import_CCS(file_path, YEAR) :
   
    df = gt.Container(file_path)
    df_CCS = pd.DataFrame(df.data["CC_YCRAG"].records)
    df_CCS.columns = ["Y", "C", "RRR","AAA", "G", "FFF", "TECH_TYPE", "Units", "Value"]
    df_CC = df_CCS[df_CCS['Y']==YEAR]
    yearly_sum = int(df_CC["Value"].sum())
   
    return yearly_sum

# Function to extract the info about the hydrogen capacities
def H2_CAP(df_CAP, Countries: list[str], YEAR) :
    if not isinstance(Countries, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries).__name__}.")
    
    #HYDROGEN CAPACITY 
    df_H2_CAP = df_CAP[(df_CAP['COMMODITY']=='HYDROGEN') & (df_CAP['C'].isin(Countries)) & (df_CAP['Y']==YEAR) & (df_CAP['FFF'] != 'IMPORT_H2')]
    #GREEN HYDROGEN CAPACITY
    df_H2_CAP_GREEN = df_H2_CAP[(df_H2_CAP['TECH_TYPE']=='ELECTROLYZER')]
    df_H2_CAP_GREEN_tot = df_H2_CAP_GREEN['value'].sum()
    #BLUE HYDROGEN CAPACITY
    df_H2_CAP_BLUE = df_H2_CAP[(df_H2_CAP['G'].str.contains('CCS')) & ((df_H2_CAP['TECH_TYPE']=='STEAMREFORMING'))]
    df_H2_CAP_BLUE_tot = df_H2_CAP_BLUE['value'].sum()
    #STO HYDROGEN CAPACITY
    df_H2_CAP_STO = df_H2_CAP[(df_H2_CAP['TECH_TYPE']=='H2-STORAGE')]
    df_H2_CAP_STO_tot = df_H2_CAP_STO['value'].sum()
    
    return df_H2_CAP, df_H2_CAP_GREEN, df_H2_CAP_GREEN_tot, df_H2_CAP_BLUE, df_H2_CAP_BLUE_tot, df_H2_CAP_STO, df_H2_CAP_STO_tot

# Function to extract the info about the hydrogen production
def H2_PRO(df_PRO, df_PRO_STO, df_CAP, Countries: list[str], YEAR) :
    if not isinstance(Countries, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries).__name__}.")
    
    #HYDROGEN CAPACITY 
    df_H2_CAP = df_CAP[(df_CAP['COMMODITY']=='HYDROGEN') & (df_CAP['C'].isin(Countries)) & (df_CAP['Y']==YEAR) & (df_CAP['FFF'] != 'IMPORT_H2')]
    #HYDROGEN PRODUCTION 
    df_H2_PRO = df_PRO[(df_PRO['COMMODITY']=='HYDROGEN') & (df_PRO['C'].isin(Countries)) & (df_PRO['Y']==YEAR)]
    #GREEN HYDROGEN PRODUCTION
    df_H2_PRO_GREEN = df_H2_PRO[(df_H2_PRO['TECH_TYPE']=='ELECTROLYZER')]
    df_H2_PRO_GREEN_tot = df_H2_PRO_GREEN['value'].sum()
    #BLUE HYDROGEN PRODUCTION
    df_H2_PRO_BLUE = df_H2_PRO[(df_H2_PRO['G'].str.contains('CCS')) & ((df_H2_PRO['TECH_TYPE']=='STEAMREFORMING'))]
    df_H2_PRO_BLUE_tot = df_H2_PRO_BLUE['value'].sum()
    #STO HYDROGEN PRODUCTION
    df_H2_PRO_STO = df_PRO_STO[(df_PRO_STO['TECH_TYPE']=='H2-STORAGE') & (df_PRO_STO['C'].isin(Countries))]
    df_H2_PRO_STO.loc[:,'value'] = df_H2_PRO_STO['value']/1000
    df_H2_PRO_STO_tot = df_H2_PRO_STO['value'].sum()
    
    return df_H2_PRO, df_H2_PRO_GREEN, df_H2_PRO_GREEN_tot, df_H2_PRO_BLUE, df_H2_PRO_BLUE_tot, df_H2_PRO_STO, df_H2_PRO_STO_tot

# Function to extract transmission capacities and flows
def XH2(df_XH2, Countries_from: list[str], YEAR, parameter: str) :
    if not isinstance(Countries_from, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries_from).__name__}.")
    
    df_XH2 = df_XH2[df_XH2['Y']==YEAR]
    df_XH2['CI'] = df_XH2['IRRRI'].map(RRR_to_CCC)
    df_XH2 = df_XH2[(df_XH2['C'].isin(Countries_from))]
    
    if parameter == 'dict' :
        df_XH2_tot = df_XH2.groupby(['CI'])['value'].sum().reset_index()
        Countries_to = df_XH2_tot['CI'].unique()
        dict_df_XH2_TO = {}
        for country in Countries_to :
            dict_df_XH2_TO[country] = df_XH2_tot[(df_XH2_tot['CI'].isin([country]))]
        return dict_df_XH2_TO
    
    elif parameter == 'total' :
        XH2_tot = df_XH2['value'].sum()
        return XH2_tot



#### Monte Carlo functions ####

# Function to import the tables from the MonteCarlo file
def Import_MonteCarlo(file_path):
    
    df_merged = gt.Container(file_path)

    df_PRO        = pd.DataFrame(df_merged.data["PRO_YCRAGF"].records)
    df_CAP        = pd.DataFrame(df_merged.data["G_CAP_YCRAF"].records)
    df_XH2_CAP    = pd.DataFrame(df_merged.data["XH2_CAP_YCR"].records)
    df_XH2_FLOW   = pd.DataFrame(df_merged.data["XH2_FLOW_YCR"].records)
    df_PRO_STO        = pd.DataFrame(df_merged.data["G_STO_YCRAF"].records)

    PRO_YCRAGF_headers     = ['scenarios', 'Y', 'C', 'RRR', 'AAA', 'G', 'FFF', 'COMMODITY', 'TECH_TYPE', 'UNITS', 'value']
    G_CAP_YCRAF_headers    = ['scenarios', 'Y', 'C', 'RRR', 'AAA', 'G', 'FFF', 'COMMODITY', 'TECH_TYPE', 'VARIABLE_CATEGORY', 'UNITS', 'value']
    XH2_CAP_YCR_headers    = ['scenarios', 'Y', 'C', 'IRRRE', 'IRRRI', 'VARIABLE_CATEGORY', 'UNITS', 'value']
    XH2_FLOW_YCR_headers   = ['scenarios', 'Y', 'C', 'IRRRE', 'IRRRI', 'UNITS', 'value']

    df_PRO.columns       = PRO_YCRAGF_headers
    df_CAP.columns       = G_CAP_YCRAF_headers
    df_XH2_CAP.columns   = XH2_CAP_YCR_headers
    df_XH2_FLOW.columns  = XH2_FLOW_YCR_headers
    df_PRO_STO.columns       = G_CAP_YCRAF_headers

    #drop na 
    df_PRO = df_PRO.dropna()
    df_CAP = df_CAP.dropna()
    df_XH2_CAP = df_XH2_CAP.dropna()
    df_XH2_FLOW = df_XH2_FLOW.dropna()
    df_PRO_STO = df_PRO_STO.dropna()

    #remove the word Scenario from the scenario column
    df_PRO['scenarios'] = df_PRO['scenarios'].str.extract(r'(\d+)').astype(int)
    df_CAP['scenarios'] = df_CAP['scenarios'].str.extract(r'(\d+)').astype(int)
    df_XH2_CAP['scenarios'] = df_XH2_CAP['scenarios'].str.extract(r'(\d+)').astype(int)
    df_XH2_FLOW['scenarios'] = df_XH2_FLOW['scenarios'].str.extract(r'(\d+)').astype(int)
    df_PRO_STO['scenarios'] = df_PRO_STO['scenarios'].str.extract(r'(\d+)').astype(int)

    scen = pd.unique(df_PRO['scenarios']).tolist()

    return df_PRO, df_CAP, df_XH2_CAP, df_XH2_FLOW, df_PRO_STO, scen

def RE_CAP_scen(df_CAP, YEAR) :
    
    df_CAP['TECH_GROUP'] = df_CAP['TECH_TYPE'].map(TECHT_to_TECHG)
    df_CAP = df_CAP[(df_CAP['TECH_GROUP'].isin(['SOLARPV', 'WINDTURBINE_ONSHORE', 'WINDTURBINE_OFFSHORE'])) & (df_CAP['Y']==YEAR)].reset_index(drop=True)
    df_RE_CAP = df_CAP.groupby(['scenarios','C','TECH_GROUP'])['value'].sum().reset_index()
    
    return df_RE_CAP

# Function to extract hydrogen capacities for specific countries
def H2_CAP_scen(df_CAP, scen, Countries: list[str], YEAR):
    if not isinstance(Countries, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries).__name__}.")
    
    df_H2_CAP = df_CAP[(df_CAP['COMMODITY']=='HYDROGEN') & (df_CAP['C'].isin(Countries)) & (df_CAP['Y']==YEAR) & (df_CAP['FFF'] != 'IMPORT_H2')]
    df_H2_CAP_GREEN = df_H2_CAP[(df_H2_CAP['TECH_TYPE']=='ELECTROLYZER')]
    df_H2_CAP_BLUE = df_H2_CAP[(df_H2_CAP['G'].str.contains('CCS')) & ((df_H2_CAP['TECH_TYPE']=='STEAMREFORMING'))]
    df_H2_CAP_STO = df_H2_CAP[(df_H2_CAP['TECH_TYPE']=='H2-STORAGE')]

    df_H2_CAP_GREEN = df_H2_CAP_GREEN.groupby('scenarios')['value'].sum().reset_index()
    df_H2_CAP_BLUE  = df_H2_CAP_BLUE.groupby('scenarios')['value'].sum().reset_index()
    df_H2_CAP_STO   = df_H2_CAP_STO.groupby('scenarios')['value'].sum().reset_index()

    df_H2_CAP_GREEN = df_H2_CAP_GREEN.sort_values(by=['scenarios'],ascending=True)
    df_H2_CAP_BLUE  = df_H2_CAP_BLUE.sort_values(by=['scenarios'],ascending=True)
    df_H2_CAP_STO   = df_H2_CAP_STO.sort_values(by=['scenarios'],ascending=True)

    df_H2_CAP_GREEN = df_H2_CAP_GREEN.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
    df_H2_CAP_BLUE  = df_H2_CAP_BLUE.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
    df_H2_CAP_STO   = df_H2_CAP_STO.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)

    return df_H2_CAP, df_H2_CAP_GREEN, df_H2_CAP_BLUE, df_H2_CAP_STO

# Function to extract hydrogen production for specific countries
def H2_PRO_scen(df_PRO, df_PRO_STO, df_CAP, scen, Countries: list[str], YEAR):
    if not isinstance(Countries, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries).__name__}.")
    
    df_H2_CAP = df_CAP[(df_CAP['COMMODITY']=='HYDROGEN') & (df_CAP['C'].isin(Countries)) & (df_CAP['Y']==YEAR) & (df_CAP['FFF'] != 'IMPORT_H2')]
    df_H2_PRO = df_PRO[(df_PRO['COMMODITY']=='HYDROGEN') & (df_PRO['C'].isin(Countries)) & (df_PRO['Y']==YEAR)]
    
    df_H2_PRO_GREEN = df_H2_PRO[(df_H2_PRO['TECH_TYPE']=='ELECTROLYZER')]
    df_H2_PRO_BLUE = df_H2_PRO[(df_H2_PRO['G'].str.contains('CCS')) & ((df_H2_PRO['TECH_TYPE']=='STEAMREFORMING'))]
    
    df_H2_PRO_GREEN = df_H2_PRO_GREEN.groupby('scenarios')['value'].sum().reset_index()
    df_H2_PRO_BLUE  = df_H2_PRO_BLUE.groupby('scenarios')['value'].sum().reset_index()

    df_H2_PRO_GREEN = df_H2_PRO_GREEN.sort_values(by=['scenarios'],ascending=True)
    df_H2_PRO_BLUE  = df_H2_PRO_BLUE.sort_values(by=['scenarios'],ascending=True)

    df_H2_PRO_GREEN = df_H2_PRO_GREEN.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
    df_H2_PRO_BLUE  = df_H2_PRO_BLUE.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
    
    df_H2_PRO_STO = df_PRO_STO[(df_PRO_STO['TECH_TYPE']=='H2-STORAGE') & (df_PRO_STO['C'].isin(Countries))]      
    df_H2_PRO_STO.loc[:,'value'] = df_H2_PRO_STO['value']/1000

    return df_H2_PRO, df_H2_PRO_GREEN, df_H2_PRO_BLUE, df_H2_PRO_STO

# Function to extract transmission capacities and flows
def XH2_scen(df_XH2, scen, Countries_from: list[str], YEAR, parameter: str) :
    if not isinstance(Countries_from, list):
        raise TypeError(f"The 'Countries' parameter must be a list, but got {type(Countries_from).__name__}.")
    
    df_XH2 = df_XH2[df_XH2['Y']==YEAR]
    df_XH2['CI'] = df_XH2['IRRRI'].map(RRR_to_CCC)
    df_XH2 = df_XH2[(df_XH2['C'].isin(Countries_from))]
    
    if parameter == 'dict' :
        df_XH2_tot = df_XH2.groupby(['scenarios','CI'])['value'].sum().reset_index()
        Countries_to = df_XH2_tot['CI'].unique()
        dict_df_XH2_TO_scen = {}
        for country in Countries_to :
            df_XH2_tot_TO = df_XH2_tot[(df_XH2_tot['CI'].isin([country]))]
            df_XH2_tot_TO = df_XH2_tot_TO.groupby('scenarios').sum().reset_index()
            df_XH2_tot_TO = df_XH2_tot_TO.sort_values(by=['scenarios'],ascending=True)
            df_XH2_tot_TO = df_XH2_tot_TO.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
            dict_df_XH2_TO_scen[country] = df_XH2_tot_TO
        return df_XH2_tot, dict_df_XH2_TO_scen
    
    elif parameter == 'total' :
        df_XH2_tot = df_XH2.groupby(['scenarios'])['value'].sum().reset_index()
        return df_XH2_tot


#### Plotting functions ####

# Function to plot the RE installed capacities
def RE_CAP(df_RE_CAP, Countries: list[str], YEAR) :
    
    df_RE_CAP = df_RE_CAP[df_RE_CAP['C'].isin(Countries)].reset_index(drop=True)
    
    df_RE_CAP = df_RE_CAP.groupby(['scenarios','TECH_GROUP'])['value'].sum().reset_index()
    
    df_RE_CAP_WINDON = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='WINDTURBINE_ONSHORE']['value'].reset_index(drop=True)
    df_RE_CAP_WINDOFF = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='WINDTURBINE_OFFSHORE']['value'].reset_index(drop=True)
    df_RE_CAP_SOLARPV = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='SOLARPV']['value'].reset_index(drop=True)
    
    # Create subplots
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.07)

    # Plotting Wind Onshore Histogram
    fig.add_trace(go.Histogram(x=df_RE_CAP_WINDON, name='Wind Onshore', marker_color='lightskyblue', opacity=0.8), row=1, col=1)

    # Plotting Wind Offshore Histogram
    fig.add_trace(go.Histogram(x=df_RE_CAP_WINDOFF, name='Wind Offshore', marker_color='darkblue', opacity=0.8), row=1, col=2)

    # Plotting Solar PV Histogram
    fig.add_trace(go.Histogram(x=df_RE_CAP_SOLARPV, name='Solar PV', marker_color='orange', opacity=0.8), row=1, col=3)

    annotations = [
        dict(xref='paper', yref='paper', x=0.5, y=-0.1, xanchor='center', yanchor='top', text='Wind Offshore [GW]', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=0.125, y=-0.1, xanchor='center', yanchor='top', text='Wind Onshore [GW]', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=0.875, y=-0.1, xanchor='center', yanchor='top', text='Solar PV [GW]', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=-0.03, y=0.5, xanchor='right', yanchor='middle', text='Frequency', showarrow=False, font=dict(size=15), textangle=-90)
    ]
    
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries)]
    except :
        region_name = ' '.join(Countries)

    # Update layout with custom axis titles and overall figure adjustments
    fig.update_layout(
        title=f'Histograms of Renewables in {region_name} ({YEAR})',
        width=1350,
        height=500,
        annotations=annotations,
        legend=dict(x=0.5, y=1.1, xanchor='center', yanchor='top', orientation='h',font=dict(size=11))
    )

    # Show the figure
    fig.show()

    return(fig)

# Function to Compare the RE installed capacities to the RE limits
def COMP_RE_LIM(df_RE_SUBTECH, df_RE_CAP, Countries: list[str], YEAR) :
    
    df_RE_SUBTECH = df_RE_SUBTECH[df_RE_SUBTECH['C'].isin(Countries)].reset_index(drop=True)
    df_RE_CAP = df_RE_CAP[df_RE_CAP['C'].isin(Countries)].reset_index(drop=True)
    
    df_RE_SUBTECH = df_RE_SUBTECH.groupby(['scenarios','TECH_GROUP'])['value'].sum().reset_index()
    df_RE_CAP = df_RE_CAP.groupby(['scenarios','TECH_GROUP'])['value'].sum().reset_index()
    
    df_RE_SUBTECH_WINDON = df_RE_SUBTECH[df_RE_SUBTECH['TECH_GROUP']=='WINDTURBINE_ONSHORE'].reset_index(drop=True)
    df_RE_SUBTECH_WINDOFF = df_RE_SUBTECH[df_RE_SUBTECH['TECH_GROUP']=='WINDTURBINE_OFFSHORE'].reset_index(drop=True)
    df_RE_SUBTECH_SOLARPV = df_RE_SUBTECH[df_RE_SUBTECH['TECH_GROUP']=='SOLARPV'].reset_index(drop=True)
    df_RE_CAP_WINDON = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='WINDTURBINE_ONSHORE'].reset_index(drop=True)
    df_RE_CAP_WINDOFF = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='WINDTURBINE_OFFSHORE'].reset_index(drop=True)
    df_RE_CAP_SOLARPV = df_RE_CAP[df_RE_CAP['TECH_GROUP']=='SOLARPV'].reset_index(drop=True)
    
    WINDON_RAP = df_RE_CAP_WINDON['value']/df_RE_SUBTECH_WINDON['value']
    WINDOFF_RAP = df_RE_CAP_WINDOFF['value']/df_RE_SUBTECH_WINDOFF['value']
    SOLARPV_RAP = df_RE_CAP_SOLARPV['value']/df_RE_SUBTECH_SOLARPV['value']
    
    # Create subplots
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.07)

    # Plotting Wind Onshore Histogram
    fig.add_trace(go.Histogram(x=WINDON_RAP, name='Wind Onshore', marker_color='lightskyblue', opacity=0.8, xbins=dict(start=0, end=1, size=0.01)), row=1, col=1)

    # Plotting Wind Offshore Histogram
    fig.add_trace(go.Histogram(x=WINDOFF_RAP, name='Wind Offshore', marker_color='darkblue', opacity=0.8, xbins=dict(start=0, end=1, size=0.01)), row=1, col=2)

    # Plotting Solar PV Histogram
    fig.add_trace(go.Histogram(x=SOLARPV_RAP, name='Solar PV', marker_color='orange', opacity=0.8, xbins=dict(start=0, end=1, size=0.01)), row=1, col=3)
    
    #Fix x axis
    fig.update_xaxes(range=[0, 1], row=1, col=1)
    fig.update_xaxes(range=[0, 1], row=1, col=2)
    fig.update_xaxes(range=[0, 1], row=1, col=3)

    annotations = [
        dict(xref='paper', yref='paper', x=0.5, y=-0.1, xanchor='center', yanchor='top', text='Wind Offshore', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=0.125, y=-0.1, xanchor='center', yanchor='top', text='Wind Onshore', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=0.875, y=-0.1, xanchor='center', yanchor='top', text='Solar PV', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=-0.03, y=0.5, xanchor='right', yanchor='middle', text='Frequency', showarrow=False, font=dict(size=15), textangle=-90)
    ]
    
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries)]
    except :
        region_name = ' '.join(Countries)

    # Update layout with custom axis titles and overall figure adjustments
    fig.update_layout(
        title=f'Histograms of Renewables limits in {region_name} ({YEAR})',
        width=1350,
        height=500,
        annotations=annotations,
        legend=dict(x=0.5, y=1.1, xanchor='center', yanchor='top', orientation='h',font=dict(size=11))
    )

    # Show the figure
    fig.show()

    return(fig)

# Function to plot ECDF and Histograms for hydrogen production
def ECDF_Hist_PRO(df_H2_PRO_GREEN_scen, df_H2_PRO_BLUE_scen, df_H2_PRO_STO_scen, df_H2_PRO_GREEN_tot_BASE, df_H2_PRO_BLUE_tot_BASE, df_H2_PRO_STO_tot_BASE, Countries_from: list[str], YEAR) :
    data_green = df_H2_PRO_GREEN_scen['value']
    data_blue = df_H2_PRO_BLUE_scen['value']
    data_sto = df_H2_PRO_STO_scen['value']

    sorted_data_blue = np.sort(data_blue)
    sorted_data_green = np.sort(data_green)
    sorted_data_sto = np.sort(data_sto)

    ecdf_blue = np.arange(1, len(sorted_data_blue) + 1) / len(sorted_data_blue)
    ecdf_green = np.arange(1, len(sorted_data_green) + 1) / len(sorted_data_green)
    ecdf_sto = np.arange(1, len(sorted_data_sto) + 1) / len(sorted_data_sto)

    # Create subplots
    fig = make_subplots(rows=1, cols=3, specs=[[{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}]], horizontal_spacing=0.07)

    # Plotting Green Data ECDF and Histogram
    fig.add_trace(go.Scatter(x=sorted_data_green, y=ecdf_green, mode='lines', name='Green ECDF', line=dict(color='green')), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Histogram(x=data_green, name='Green Histogram', marker_color='lightgreen', opacity=0.8), row=1, col=1, secondary_y=True)
    # Add vertical line for Green baseline
    fig.add_shape(type="line", xref="x", yref="paper", x0=df_H2_PRO_GREEN_tot_BASE, y0=0, x1=df_H2_PRO_GREEN_tot_BASE, y1=1, line=dict(color="green", width=2, dash="dash"), row=1, col=1)
    # Dummy trace for Green baseline line in legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='green', width=2, dash='dash'), name='Green Baseline'), row=1, col=1)

    # Plotting Blue Data ECDF and Histogram
    fig.add_trace(go.Scatter(x=sorted_data_blue, y=ecdf_blue, mode='lines', name='Blue ECDF', line=dict(color='blue')), row=1, col=2, secondary_y=False)
    fig.add_trace(go.Histogram(x=data_blue, name='Blue Histogram', marker_color='lightblue', opacity=0.8), row=1, col=2, secondary_y=True)
    # Add vertical line for Blue baseline
    fig.add_shape(type="line", xref="x", yref="paper", x0=df_H2_PRO_BLUE_tot_BASE, y0=0, x1=df_H2_PRO_BLUE_tot_BASE, y1=1, line=dict(color="blue", width=2, dash="dash"), row=1, col=2)
    # Dummy trace for Blue baseline line in legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='blue', width=2, dash='dash'), name='Blue Baseline'), row=1, col=2)

    # Plotting Storage Data ECDF and Histogram
    fig.add_trace(go.Scatter(x=sorted_data_sto, y=ecdf_sto, mode='lines', name='Storage ECDF', line=dict(color='orange')), row=1, col=3, secondary_y=False)
    fig.add_trace(go.Histogram(x=data_sto, name='Storage Histogram', marker_color='orange', opacity=0.8), row=1, col=3, secondary_y=True)
    # Add vertical line for Storage baseline
    fig.add_shape(type="line", xref="x", yref="paper", x0=df_H2_PRO_STO_tot_BASE, y0=0, x1=df_H2_PRO_STO_tot_BASE, y1=1, line=dict(color="darkorange", width=2, dash="dash"), row=1, col=3)
    # Dummy trace for Storage baseline line in legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='darkorange', width=2, dash='dash'), name='Storage Baseline'), row=1, col=3)

    annotations = [
        dict(xref='paper', yref='paper', x=0.5, y=-0.15, xanchor='center', yanchor='top', text='Hydrogen Production [TWh]', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=-0.03, y=0.5, xanchor='right', yanchor='middle', text='ECDF', showarrow=False, font=dict(size=15), textangle=-90),
        dict(xref='paper', yref='paper', x=0.97, y=0.5, xanchor='left', yanchor='middle', text='Frequency', showarrow=False, font=dict(size=15), textangle=-90)
    ]
    
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from)

    # Update layout with custom axis titles and overall figure adjustments
    fig.update_layout(
        title=f'ECDF Plots and Histograms for Hydrogen Production in {region_name} ({YEAR})',
        width=1350,
        height=500,
        annotations=annotations,
        legend=dict(x=0.5, y=1.1, xanchor='center', yanchor='top', orientation='h',font=dict(size=11))
    )

    # Show the figure
    fig.show()

    return(fig)
    
# Function to plot ECDF and Histograms for hydrogen capacity
def ECDF_Hist_CAP(df_H2_CAP_GREEN_scen, df_H2_CAP_BLUE_scen, df_H2_CAP_GREEN_tot_BASE, df_H2_CAP_BLUE_tot_BASE, Countries_from: list[str], YEAR) :
    data_green = df_H2_CAP_GREEN_scen['value']
    data_blue = df_H2_CAP_BLUE_scen['value']

    sorted_data_blue = np.sort(data_blue)
    sorted_data_green = np.sort(data_green)

    ecdf_blue = np.arange(1, len(sorted_data_blue) + 1) / len(sorted_data_blue)
    ecdf_green = np.arange(1, len(sorted_data_green) + 1) / len(sorted_data_green)

    # Create subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{"secondary_y": True}, {"secondary_y": True}]], horizontal_spacing=0.09)

    # Plotting Green Data ECDF and Histogram
    fig.add_trace(go.Scatter(x=sorted_data_green, y=ecdf_green, mode='lines', name='Green ECDF', line=dict(color='green')), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Histogram(x=data_green, name='Green Histogram', marker_color='lightgreen', opacity=0.8), row=1, col=1, secondary_y=True)
    # Add vertical line for Green baseline
    fig.add_shape(type="line", xref="x", yref="paper", x0=df_H2_CAP_GREEN_tot_BASE, y0=0, x1=df_H2_CAP_GREEN_tot_BASE, y1=1, line=dict(color="green", width=2, dash="dash"), row=1, col=1)

    # Dummy trace for Green baseline line in legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='green', width=2, dash='dash'), name='Green Baseline'), row=1, col=1)

    # Plotting Blue Data ECDF and Histogram
    fig.add_trace(go.Scatter(x=sorted_data_blue, y=ecdf_blue, mode='lines', name='Blue ECDF', line=dict(color='blue')), row=1, col=2, secondary_y=False)
    fig.add_trace(go.Histogram(x=data_blue, name='Blue Histogram', marker_color='lightblue', opacity=0.8), row=1, col=2, secondary_y=True)
    # Add vertical line for Blue baseline
    fig.add_shape(type="line", xref="x", yref="paper", x0=df_H2_CAP_BLUE_tot_BASE, y0=0, x1=df_H2_CAP_BLUE_tot_BASE, y1=1, line=dict(color="blue", width=2, dash="dash"), row=1, col=2)

    # Dummy trace for Blue baseline line in legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='blue', width=2, dash='dash'), name='Blue Baseline'), row=1, col=2)

    annotations = [
        dict(xref='paper', yref='paper', x=0.5, y=-0.15, xanchor='center', yanchor='top', text='Hydrogen Capacity [GW]', showarrow=False, font=dict(size=15)),
        dict(xref='paper', yref='paper', x=-0.03, y=0.5, xanchor='right', yanchor='middle', text='ECDF', showarrow=False, font=dict(size=15), textangle=-90),
    ]
    
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from)

    # Update layout with custom axis titles and overall figure adjustments
    fig.update_layout(
        title=f'ECDF Plots and Histograms for Hydrogen Capacity in {region_name} ({YEAR})',
        width=1000,
        height=500,
        annotations=annotations,
        legend=dict(x=0.5, y=1.1, xanchor='center', yanchor='top', orientation='h',font=dict(size=11))
    )

    fig.show()

    return(fig)

# Function to violin plot the distribution of H2 production
def Violin_Setups(df_H2_BASE_scen, df_H2_NoH2_scen, df_H2_tot_BASE, df_H2_tot_NoH2, Countries_from: list[str], YEAR, type: str) :
    if type not in ["Green Capacity", "Blue Capacity", "Green Production", "Blue Production", "Storage", "Transmission Capacity", "Transmission Flow"]: 
        raise ValueError(f"Invalid type: {type}")
    
    # Example DataFrames and baseline values (ensure these dataframes and variables are defined)
    baseline_y = np.array([df_H2_tot_BASE, df_H2_tot_NoH2])

    df_H2_BASE_scen['category'] = 'Base'
    df_H2_NoH2_scen['category'] = 'No H2 Target'

    # Combine the dataframes into a single dataframe
    combined_df = pd.concat([df_H2_BASE_scen, df_H2_NoH2_scen])
    
    # Color and unit of the violin plots
    if type in ["Green Capacity", "Green Production"]:
        color = 'green'
    elif type in ["Blue Capacity", "Blue Production"]:
        color = 'blue'
    elif type == "Storage":
        color = 'orange'
        unit = 'TWh'
    elif type in ["Transmission Capacity"]:
        color = 'red'
    elif type in ["Transmission Flow"]:
        color = 'red'
    
    if "Capacity" in type:
        unit = 'GW'
    elif "Production" in type or "Flow" in type:
        unit = 'TWh'

    # Create plot
    fig = go.Figure()

    # Plot Green H2
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Base']['value'], name='Base',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['Base'], y=[baseline_y[0]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline Base'))

    # Plot Blue H2
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'No H2 Target']['value'], name='No H2 Target',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['No H2 Target'], y=[baseline_y[1]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline No H2 Target'))

   
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from) 
    
    fig.update_layout(
        title={
            'text': f'Violin Plot: Value Distribution of H2 {type} in {region_name} ({YEAR})',
            'font': {'size': 16}
        },
        yaxis_title=f"H2 {type} [{unit}]",
        yaxis_range=[0, None],
        height=600,
        width=1200,
        legend=dict(orientation='h', x=0.5, y=1.04, xanchor='center', yanchor='bottom'),  # Adjust legend position
        margin=dict(t=120, b=100)  # Adjust top and bottom margins to accommodate title and legend
    )

    # Show the figure
    fig.show()

    return(fig)
    
# Function to violin plot the distribution of H2 production
def Violin_PRO(df_H2_PRO_GREEN_scen, df_H2_PRO_BLUE_scen, df_H2_PRO_STO_scen, df_H2_PRO_GREEN_tot_BASE, df_H2_PRO_BLUE_tot_BASE, df_H2_PRO_STO_tot_BASE, Countries_from: list[str], YEAR) :
    # Example DataFrames and baseline values (ensure these dataframes and variables are defined)
    baseline_y = np.array([df_H2_PRO_GREEN_tot_BASE, df_H2_PRO_BLUE_tot_BASE, df_H2_PRO_STO_tot_BASE])
    categories = ['Green H2', 'Blue H2', 'Storage H2']

    df_H2_PRO_GREEN_scen['category'] = 'Green H2'
    df_H2_PRO_BLUE_scen['category'] = 'Blue H2'
    df_H2_PRO_STO_scen['category'] = 'Storage H2'

    # Apply the threshold to the Blue H2 data only
    #threshold = 5
    #df_H2_PRO_DK_BLUE_N1000 = df_H2_PRO_DK_BLUE_N1000[df_H2_PRO_DK_BLUE_N1000['value'] < threshold]

    # Combine the dataframes into a single dataframe
    combined_df = pd.concat([df_H2_PRO_GREEN_scen, df_H2_PRO_BLUE_scen, df_H2_PRO_STO_scen])

    # Create subplots
    fig = make_subplots(rows=1, cols=2, column_widths=[2/3, 1/3])

    # Plot Green H2
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Green H2']['value'], name='Green H2',
                            box_visible=True, line_color='green'), row=1, col=1)
    fig.add_trace(go.Scatter(x=['Green H2'], y=[baseline_y[0]], mode='markers',
                            marker=dict(color='#a5eb34', size=10), name='Baseline Green H2'), row=1, col=1)

    # Plot Blue H2
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Blue H2']['value'], name='Blue H2',
                            box_visible=True, line_color='blue'), row=1, col=1)
    fig.add_trace(go.Scatter(x=['Blue H2'], y=[baseline_y[1]], mode='markers',
                            marker=dict(color='#34ebe5', size=10), name='Baseline Blue H2'), row=1, col=1)

    # Plot Storage H2
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Storage H2']['value'], name='Storage H2',
                            box_visible=True, line_color='orange'), row=1, col=2)
    fig.add_trace(go.Scatter(x=['Storage H2'], y=[baseline_y[2]], mode='markers',
                            marker=dict(color='#eb4034', size=10), name='Baseline Storage H2'), row=1, col=2)
   
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from) 
    
    fig.update_layout(
        title={
            'text': f'Violin Plot: Value Distribution of H2 Production in {region_name} ({YEAR})',
            'font': {'size': 16}
        },
        yaxis_title="H2 Production [TWh]",
        yaxis2_title="H2 Storage [TWh]",
        yaxis_range=[0, None],
        yaxis2_range=[0, None],
        height=600,
        width=1200,
        legend=dict(orientation='h', x=0.5, y=1.04, xanchor='center', yanchor='bottom'),  # Adjust legend position
        margin=dict(t=120, b=100)  # Adjust top and bottom margins to accommodate title and legend
    )

    # Show the figure
    fig.show()

    return(fig)
    
# Function to violin plot the distribution of H2 capacities
def Violin_CAP(df_H2_CAP_GREEN_scen, df_H2_CAP_BLUE_scen, df_H2_CAP_STO_scen, df_H2_CAP_GREEN_tot_BASE, df_H2_CAP_BLUE_tot_BASE, df_H2_CAP_STO_tot_BASE, Countries_from: list[str], YEAR) :
    
    baseline_y = np.array([df_H2_CAP_GREEN_tot_BASE, df_H2_CAP_BLUE_tot_BASE, df_H2_CAP_STO_tot_BASE])
    categories = ['Green H2', 'Blue H2', 'Storage H2']

    # Assigning categories
    df_H2_CAP_GREEN_scen['category'] = 'Green H2'
    df_H2_CAP_BLUE_scen['category'] = 'Blue H2'
    df_H2_CAP_STO_scen['category'] = 'Storage H2'

    #threshold = 0.2
    #df_H2_CAP_DK_BLUE_N1000 = df_H2_CAP_DK_BLUE_N1000[df_H2_CAP_DK_BLUE_N1000['value'] < threshold]

    # Combine the dataframes into one dataframe
    combined_df = pd.concat([df_H2_CAP_GREEN_scen, df_H2_CAP_BLUE_scen, df_H2_CAP_STO_scen])

    # Create subplots with 1 row and 3 columns
    fig = go.Figure()

    # Add violin plots to each subplot
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Green H2']['value'], name='Green H2',
                            line_color='green', box_visible=True, meanline_visible=False))
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Blue H2']['value'], name='Blue H2',
                            line_color='blue', box_visible=True, meanline_visible=False))

    # Add baseline markers for each category
    fig.add_trace(go.Scatter(x=['Green H2'], y=[baseline_y[0]], mode='markers',
                            marker=dict(color='#a5eb34', size=10), name='Baseline Green H2'))
    fig.add_trace(go.Scatter(x=['Blue H2'], y=[baseline_y[1]], mode='markers',
                            marker=dict(color='#34ebe5', size=10), name='Baseline Blue H2'))
    #Update y-axes
    # fig.update_yaxes(range=[0,1],row=1,col=2)
    # Adjust layout
    
    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from) 
    
    fig.update_layout(
        title=f'Violin Plot: Value Distribution of H2 Capacity in {region_name} ({YEAR})',
        yaxis_title="H2 Capacity [GW]",
        yaxis_range=[0, None],
        height=600,
        width=1200,
        showlegend=False  # Optionally hide the legend if it is not needed
        
    )


    # Show the figure
    fig.show()

    return(fig)
    
# Function for box plot of transmission capacities 
def BoxPlot_Transmission(dict_df_XH2_TO_BASE, dict_df_XH2_TO_scen, Countries_from: list[str], YEAR, type: str) :
    if type not in ["Capacity", "Flow"]:
        raise ValueError(f"Invalid type: {type}. Expected 'Capacity' or 'Flow'.")
    
    dict_BASE = dict_df_XH2_TO_BASE.copy()
    dict_scen = dict_df_XH2_TO_scen.copy()
    
    # Get the keys of the dict
    keys = list(dict_df_XH2_TO_BASE.keys())
    neighbors = [key for key in keys if key not in Countries_from]
    
    baseline_y = np.array([dict_BASE[key]['value'].sum() for key in neighbors])
    means_y = np.array([dict_BASE[key]['value'].mean() for key in neighbors])
    
    # Combine the data into one DataFrame with an additional 'category' column
    L = []
    for key in neighbors :
        df = dict_scen[key].copy()
        df['category'] = key
        L.append(df)
    
    combined_df = pd.concat(L)

    # Create the box plot using go.Box to control width
    fig = go.Figure()

    # Define colors for each category
    # Function to darken a color by a factor
    def darken_color(color, factor=0.7):
        rgb = mcolors.to_rgb(color)  # Convert to RGB
        darkened_rgb = tuple([c * factor for c in rgb])  # Darken by scaling each component
        return darkened_rgb

    colormap = plt.cm.viridis  # You can use other colormaps like 'plasma', 'coolwarm', etc.
    num_colors = len(neighbors)
    base_colors = [colormap(i / num_colors) for i in range(num_colors)]

    # Generate the dictionaries
    colors_dict = {key: mcolors.to_hex(base_colors[i]) for i, key in enumerate(neighbors)}
    dark_colors_dict = {key: mcolors.to_hex(darken_color(base_colors[i])) for i, key in enumerate(neighbors)}
    
    # Add box plots for each category
    for category in neighbors:
        fig.add_trace(go.Box(
            x=combined_df[combined_df['category'] == category]['value'],
            name=category,
            marker_color=colors_dict[category],
            # boxmean='sd',
            width=0.15  # Adjust the width of the box plots
        ))
        
    max_whisker = 0
    # Calculate the max whisker value
    for category in neighbors:
        q3 = combined_df[combined_df['category'] == category]['value'].quantile(0.75)
        iqr = combined_df[combined_df['category'] == category]['value'].quantile(0.75) - combined_df[combined_df['category'] == category]['value'].quantile(0.25)
        whisker = q3 + 1.5 * iqr
        if whisker > max_whisker:
            max_whisker = whisker

    # Add baseline markers
    for i, baseline in enumerate(baseline_y):
        fig.add_trace(go.Scatter(y=[neighbors[i]], x=[baseline],
                                mode='markers', marker=dict(color=colors_dict[neighbors[i]], size=8, symbol='circle'),
                                name=f'Baseline {neighbors[i]}'))

    # Add mean markers
    for i, means in enumerate(means_y):
        fig.add_trace(go.Scatter(y=[neighbors[i]], x=[means],
                                mode='markers', marker=dict(color=dark_colors_dict[neighbors[i]], size=8, symbol='x'),
                                name=f'Mean {neighbors[i]}'))

    # Name of the region
    try : 
        region_name = Regions_name[tuple(Countries_from)]
    except :
        region_name = ' '.join(Countries_from) 
        
    # Capactiy or Flow
    if type == "Capacity":
        title = f'Box Plot: H2 Transmission Capacity between {region_name} and Neighboring Countries ({YEAR})'
        xaxis_title = "H2 Transmission Capacity [GW]"
    elif type == "Flow":
        title = f'Box Plot: H2 Transmission Flow between {region_name} and Neighboring Countries ({YEAR})'
        xaxis_title = "H2 Transmission Flow [TWh]"

    # Adjust layout
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 15}
            },
        yaxis_title="Neighboring Countries",
        xaxis_title=xaxis_title,
        height=500,
        width=900,
        margin=dict(
            l=50,
            r=50,
            t=100,
            b=100)
            )
    
    # Adjuste x-axis limits
    fig.update_xaxes(range=[0, max_whisker * 1.2])

    # Show the figure
    fig.show()

    return(fig)

# Function to violin plot the distribution for the four european regions

def Violin_Setups_Europe(
    df_H2_BASE_scen_EU_North, df_H2_NoH2_scen_EU_North, df_H2_tot_BASE_EU_North, df_H2_tot_NoH2_EU_North,
    df_H2_BASE_scen_EU_South, df_H2_NoH2_scen_EU_South, df_H2_tot_BASE_EU_South, df_H2_tot_NoH2_EU_South,
    df_H2_BASE_scen_EU_West, df_H2_NoH2_scen_EU_West, df_H2_tot_BASE_EU_West, df_H2_tot_NoH2_EU_West,
    df_H2_BASE_scen_EU_East, df_H2_NoH2_scen_EU_East, df_H2_tot_BASE_EU_East, df_H2_tot_NoH2_EU_East,
    YEAR, type: str
):
    if type not in ["Green Capacity", "Blue Capacity", "Green Production", "Blue Production", "Storage", "Transmission Capacity", "Transmission Flow"]: 
        raise ValueError(f"Invalid type: {type}")
    print(df_H2_BASE_scen_EU_North)
    # Baseline values
    baseline_y = np.array([
        df_H2_tot_BASE_EU_North, df_H2_tot_NoH2_EU_North,
        df_H2_tot_BASE_EU_South, df_H2_tot_NoH2_EU_South,
        df_H2_tot_BASE_EU_West, df_H2_tot_NoH2_EU_West,
        df_H2_tot_BASE_EU_East, df_H2_tot_NoH2_EU_East
    ])

    # Assign categories
    df_H2_BASE_scen_EU_North['category'] = 'Base EU North'
    df_H2_NoH2_scen_EU_North['category'] = 'No H2 Target EU North'
    df_H2_BASE_scen_EU_South['category'] = 'Base EU South'
    df_H2_NoH2_scen_EU_South['category'] = 'No H2 Target EU South'
    df_H2_BASE_scen_EU_West['category'] = 'Base EU West'
    df_H2_NoH2_scen_EU_West['category'] = 'No H2 Target EU West'
    df_H2_BASE_scen_EU_East['category'] = 'Base EU East'
    df_H2_NoH2_scen_EU_East['category'] = 'No H2 Target EU East'

    # Combine all dataframes
    combined_df = pd.concat([
        df_H2_BASE_scen_EU_North, df_H2_NoH2_scen_EU_North,
        df_H2_BASE_scen_EU_South, df_H2_NoH2_scen_EU_South,
        df_H2_BASE_scen_EU_West, df_H2_NoH2_scen_EU_West,
        df_H2_BASE_scen_EU_East, df_H2_NoH2_scen_EU_East
    ])

    # Determine color and unit
    if type in ["Green Capacity", "Green Production"]:
        color = 'green'
    elif type in ["Blue Capacity", "Blue Production"]:
        color = 'blue'
    elif type == "Storage":
        color = 'orange'
        unit = 'TWh'
    elif type == "Transmission Capacity":
        color = 'red'
    elif type == "Transmission Flow":
        color = 'red'

    if "Capacity" in type:
        unit = 'GW'
    elif "Production" in type or "Flow" in type:
        unit = 'TWh'

    # Create plot
    fig = go.Figure()

    # Plot Base EU North
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Base EU North']['value'], name='Base EU North',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['Base EU North'], y=[baseline_y[0]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline Base EU North'))

    # Plot NoH2 EU North
    if YEAR == '2030':
        fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'No H2 Target EU North']['value'], name='No H2 Target EU North',
                                box_visible=True, line_color=color))
        fig.add_trace(go.Scatter(x=['No H2 Target EU North'], y=[baseline_y[1]], mode='markers',
                                marker=dict(color='#3C3D37', size=10), name='Baseline No H2 Target EU North'))
    
    # Plot Base EU South
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Base EU South']['value'], name='Base EU South',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['Base EU South'], y=[baseline_y[2]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline Base EU South'))

    # Plot NoH2 EU South
    if YEAR == '2030':
        fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'No H2 Target EU South']['value'], name='No H2 Target EU South',
                                box_visible=True, line_color=color))
        fig.add_trace(go.Scatter(x=['No H2 Target EU South'], y=[baseline_y[3]], mode='markers',
                                marker=dict(color='#3C3D37', size=10), name='Baseline No H2 Target EU South'))

    # Plot Base EU West
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Base EU West']['value'], name='Base EU West',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['Base EU West'], y=[baseline_y[4]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline Base EU West'))

    # Plot NoH2 EU West
    if YEAR == '2030':
        fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'No H2 Target EU West']['value'], name='No H2 Target EU West',
                                box_visible=True, line_color=color))
        fig.add_trace(go.Scatter(x=['No H2 Target EU West'], y=[baseline_y[5]], mode='markers',
                                marker=dict(color='#3C3D37', size=10), name='Baseline No H2 Target EU West'))

    # Plot Base EU East
    fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'Base EU East']['value'], name='Base EU East',
                            box_visible=True, line_color=color))
    fig.add_trace(go.Scatter(x=['Base EU East'], y=[baseline_y[6]], mode='markers',
                            marker=dict(color='#3C3D37', size=10), name='Baseline Base EU East'))

    # Plot NoH2 EU East
    if YEAR == '2030':
        fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == 'No H2 Target EU East']['value'], name='No H2 Target EU East',
                                box_visible=True, line_color=color))
        fig.add_trace(go.Scatter(x=['No H2 Target EU East'], y=[baseline_y[7]], mode='markers',
                                marker=dict(color='#3C3D37', size=10), name='Baseline No H2 Target EU East'))
    

     
    fig.update_layout(
        title={
            'text': f'Violin Plot: Value Distribution of H2 {type} in ({YEAR})',
            'font': {'size': 16}, 
            
        },

        yaxis_title=f"H2 {type} [{unit}]",
        yaxis_range=[0, None],
        height=600,
        width=1200,
        legend=dict(orientation='h', x=0.5, y=1, xanchor='center', yanchor='bottom'),  # Adjust legend position
        margin=dict(t=200, b=50)  # Adjust top and bottom margins to accommodate title and legend
    )

    # Show the figure
    fig.show()

    return(fig)

#Correlation Analysis
#Function correlation outputs
def Post_analysis(df_CAP_scen, df_H2_CAP_GREEN_scen, df_H2_CAP_GREEN_tot_BASE, df_CAP, df_PRO_scen, df_H2_PRO_GREEN_scen, df_H2_PRO_GREEN_tot_BASE, df_PRO, scen, YEAR, Countries_from, type: str, type2 : str) :
    if type2 =="Capacity" :
    
        df_ELEC_CAP = df_CAP_scen[(df_CAP_scen['COMMODITY']=='ELECTRICITY') & (df_CAP_scen['C'].isin(Countries_from)) & (df_CAP_scen['Y']==YEAR) & (df_CAP_scen['TECH_TYPE']==type)]
        df_ELEC_CAP = df_ELEC_CAP.groupby('scenarios')['value'].sum().reset_index()
        df_ELEC_CAP = df_ELEC_CAP.sort_values(by=['scenarios'],ascending=True)
        df_ELEC_CAP = df_ELEC_CAP.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
        df_BASE_ELEC_CAP = df_CAP[(df_CAP['COMMODITY']=='ELECTRICITY') & (df_CAP['C'].isin(Countries_from)) & (df_CAP['Y']==YEAR) & (df_CAP['TECH_TYPE']==type)]
        df_BASE_ELEC_CAP_tot = df_BASE_ELEC_CAP['value'].sum()

        BO = pd.concat([df_H2_CAP_GREEN_scen['value'], df_ELEC_CAP['value']], axis=1)
        BO.columns = ['Green H2 Capacity [GW]', 'Capacity [GW]']

        X = BO['Capacity [GW]'].values.reshape(-1, 1)
        y = BO['Green H2 Capacity [GW]'].values

    elif type2 =="Production" :
        df_ELEC_PRO = df_PRO_scen[(df_PRO_scen['COMMODITY']=='ELECTRICITY') & (df_PRO_scen['C'].isin(Countries_from)) & (df_PRO_scen['Y']==YEAR) & (df_PRO_scen['TECH_TYPE']==type)]
        df_ELEC_PRO = df_ELEC_PRO.groupby('scenarios')['value'].sum().reset_index()
        df_ELEC_PRO = df_ELEC_PRO.sort_values(by=['scenarios'],ascending=True)
        df_ELEC_PRO = df_ELEC_PRO.set_index('scenarios').reindex(scen, fill_value=0).reset_index(drop=True)
        df_BASE_ELEC_PRO = df_PRO[(df_PRO['COMMODITY']=='ELECTRICITY') & (df_PRO['C'].isin(Countries_from)) & (df_PRO['Y']==YEAR) & (df_PRO['TECH_TYPE']==type)]
        df_BASE_ELEC_PRO_tot = df_BASE_ELEC_PRO['value'].sum()
        BO = pd.concat([df_H2_PRO_GREEN_scen['value'], df_ELEC_PRO['value']], axis=1)
        BO.columns = ['Green H2 Production [TWh]', 'Production [TWh]']

        X = BO['Production [TWh]'].values.reshape(-1, 1)
        y = BO['Green H2 Production [TWh]'].values


    reg = LinearRegression().fit(X, y)
    y_pred = reg.predict(X)
    r2 = r2_score(y, y_pred)

    fig = go.Figure()


    if type2 =="Capacity" :
        fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=BO['Green H2 Capacity [GW]'], mode='markers',showlegend=False))
        fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=y_pred, mode='lines', name='Trendline', line=dict(color='red'),showlegend=False))

        new_point_x = df_BASE_ELEC_CAP_tot
        new_point_y = df_H2_CAP_GREEN_tot_BASE
        print(new_point_x)
    
    elif type2 =="Production" :
        fig.add_trace(go.Scatter(x=BO['Production [TWh]'], y=BO['Green H2 Production [TWh]'], mode='markers',showlegend=False))
        fig.add_trace(go.Scatter(x=BO['Production [TWh]'], y=y_pred, mode='lines', name='Trendline', line=dict(color='red'),showlegend=False))

        new_point_x = df_BASE_ELEC_PRO_tot
        new_point_y = df_H2_PRO_GREEN_tot_BASE

    fig.add_trace(go.Scatter(
        x=[new_point_x],
        y=[new_point_y],
        mode='markers',
        marker=dict(color='yellow', size=10),
        name='New Point',
        showlegend=False
    ))


    if type2 =="Capacity" :
        fig.update_layout(
            title={
                'text': f'R² = {r2:.2f}',
                # 'text': f'Green H2 Capacity vs Offshore Wind Production in DK for 2050 <br>R² = {r2:.2f}',
                'y': 0.84,  
                'x': 0.5,  
                'xanchor': 'center', 
                'yanchor': 'top' 
            },
            xaxis_title= (f"{type} Capacity [GW]"),
            yaxis_title="Green H2 Capacity [GW]",
            width=600,
            height=500
        )

        fig.show()

    elif type2 =="Production" :
        fig.update_layout(
            title={
                'text': f'R² = {r2:.2f}',
                # 'text': f'Green H2 Capacity vs Offshore Wind Production in DK for 2050 <br>R² = {r2:.2f}',
                'y': 0.84,  
                'x': 0.5,  
                'xanchor': 'center', 
                'yanchor': 'top' 
            },
            xaxis_title= (f"{type} Production [TWh]"),
            yaxis_title="Green H2 Production [TWh]",
            width=600,
            height=500
        )

        fig.show()



#Correlation Analysis
#Function to import the input data from the baseline
def Import_input_data(input_data_baseline_file_path, sample_path, type: str):
    
    df = gt.Container(input_data_baseline_file_path)
    df_CCS = pd.DataFrame(df.data["CCS_CO2CAPTEFF_G"].records)
    df_DE = pd.DataFrame(df.data["DE"].records)
    df_EMIPOL = pd.DataFrame(df.data["EMI_POL"].records)
    df_FUELPRICE = pd.DataFrame(df.data["FUELPRICE"].records)
    df_GDATA_categorical = pd.DataFrame(df.data["GDATA_categorical"].records)
    df_GDATA_numerical = pd.DataFrame(df.data["GDATA_numerical"].records)
    df_HYDROGEN_DH2 = pd.DataFrame(df.data["HYDROGEN_DH2"].records)
    df_SUBTECHGROUPKPOT = pd.DataFrame(df.data["SUBTECHGROUPKPOT"].records)
    df_XH2INVCOST = pd.DataFrame(df.data["XH2INVCOST"].records)
    df_XINVCOST = pd.DataFrame(df.data["XINVCOST"].records)

    scenario_data = {
    'CCS_CO2CAPTEFF_G': df_CCS,
    'DE': df_DE,
    'EMI_POL': df_EMIPOL,
    'FUELPRICE': df_FUELPRICE,
    'GDATA_numerical': df_GDATA_numerical,
    'GDATA_categorical': df_GDATA_categorical,
    'HYDROGEN_DH2': df_HYDROGEN_DH2,
    'SUBTECHGROUPKPOT': df_SUBTECHGROUPKPOT,
    'XH2INVCOST': df_XH2INVCOST,
    'XINVCOST': df_XINVCOST
    }

    with open(sample_path, 'r') as file:
        sample_raw = file.read()
        #print(content) 
    df_sample = pd.read_csv(StringIO(sample_raw), header=None)
    
    if type == 'EU': 
        df_sample.columns = [
        "CO2_TAX","CO2_EFF","ELYS_ELEC_EFF","H2S_INVC","SMR_CCS_INVC","PV_INVC","ONS_WT_INVC","H2_OandM","SMR_CCS_OandM","H2_TRANS_INVC","ELEC_TRANS_INVC",
        "IMPORT_H2_P","DH2_DEMAND_EAST","DH2_DEMAND_SOUTH","DH2_DEMAND_NORTH","DH2_DEMAND_WEST",
        "DE_DEMAND_EAST","DE_DEMAND_SOUTH","DE_DEMAND_NORTH","DE_DEMAND_WEST","PV_LIMIT_NORTH","PV_LIMIT_SOUTH","PV_LIMIT_EAST","PV_LIMIT_WEST","ONS_LIMIT_EAST","ONS_LIMIT_WEST","ONS_LIMIT_NORTH","ONS_LIMIT_SOUTH",
        "TRANS_DEMAND_NORTH","TRANS_DEMAND_SOUTH", "TRANS_DEMAND_EAST", "TRANS_DEMAND_WEST", "NATGAS_P" ]
    elif type == 'DK': 
        df_sample.columns = ["CO2_TAX", "CO2_EFF", "ELYS_ELEC_EFF", "H2S_INVC", "SMR_CCS_INVC", "PV_INVC", "ONS_WT_INVC", 
                             "H2_OandM", "SMR_CCS_OandM", "H2_TRANS_INVC", "ELEC_TRANS_INVC", "IMPORT_H2_P", "DH2_DEMAND_Rest", 
                             "DH2_DEMAND_DK", "DH2_DEMAND_DE", "DE_DEMAND_Rest", "DE_DEMAND_DK", "DE_DEMAND_DE", "PV_LIMIT_NORTH", 
                             "PV_LIMIT_SOUTH", "ONS_LIMIT_DK", "ONS_LIMIT_DE", "ONS_LIMIT_NORTH", "ONS_LIMIT_SOUTH", "TRANS_DEMAND_REST", "TRANS_DEMAND_DE", "NATGAS_P"]

    return scenario_data, df_sample

#scenario data = input baseline data 
#Function to re-create the input data of the scenarios for some parameters of the GSA
def Sample_input_data(scenario_data, sample, YEAR): 

    df_NGAS_Price = scenario_data["FUELPRICE"]
    NatGas_Price = df_NGAS_Price[(df_NGAS_Price["FFF"]=="NATGAS") &  (df_NGAS_Price['YYY']==YEAR) & (df_NGAS_Price['AAA']=='FinA')]
    NatGas_Price_base = NatGas_Price.iloc[0]['value'] #Natural gas price baseline
    NatGas_Price_scenario = NatGas_Price_base * sample['NATGAS_P'] #Natural gas price all scenarios

    df_CO2_tax = scenario_data["EMI_POL"]
    CO2_tax = df_CO2_tax[(df_CO2_tax['YYY']==YEAR) & (df_CO2_tax['CCCRRRAAA']=='DENMARK')]
    CO2_tax_base = CO2_tax.iloc[0]['value'] #CO2 tax baseline
    CO2_Tax_scenario = CO2_tax_base * sample['CO2_TAX'] #CO2 tax all scenarios

    df_SMR_CCS_INVC = scenario_data["GDATA_numerical"]
    SMR_CCS_INVC = df_SMR_CCS_INVC[(df_SMR_CCS_INVC['GGG'].str.contains("GNR_STEAM-REFORMING-CCS")) & (df_SMR_CCS_INVC['GDATASET']=='GDINVCOST0')]
    SMR_CCS_INVC_base = SMR_CCS_INVC.iloc[0]['value'] 
    SMR_CCS_INVC_scenario = SMR_CCS_INVC_base * sample['SMR_CCS_INVC'] 

    return NatGas_Price_base, NatGas_Price_scenario, CO2_tax_base, CO2_Tax_scenario, SMR_CCS_INVC_base, SMR_CCS_INVC_scenario

#Functions to plot correlation
def Post_analysis_Natgas(df_H2_CAP_GREEN_scen, df_H2_CAP_GREEN_tot_BASE, NatGas_Price_base, NatGas_Price_scenario, type : str) :
    
    BO = pd.concat([df_H2_CAP_GREEN_scen['value'], NatGas_Price_scenario], axis=1)
    BO = BO.dropna() 
    #print(BO)
    BO.columns = ['Green H2 Capacity [GW]', 'Capacity [GW]']

    X = BO['Capacity [GW]'].values.reshape(-1, 1)
    y = BO['Green H2 Capacity [GW]'].values

    reg = LinearRegression().fit(X, y)
    y_pred = reg.predict(X)
    r2 = r2_score(y, y_pred)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=BO['Green H2 Capacity [GW]'], mode='markers',showlegend=False))
    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=y_pred, mode='lines', name='Trendline', line=dict(color='red'),showlegend=False))

    new_point_x =  NatGas_Price_base
    new_point_y = df_H2_CAP_GREEN_tot_BASE
    #print(new_point_x)
    
    
    fig.add_trace(go.Scatter(
        x=[new_point_x],
        y=[new_point_y],
        mode='markers',
        marker=dict(color='yellow', size=10),
        name='New Point',
        showlegend=False
    ))


    fig.update_layout(
        title={
            'text': f'R² = {r2:.2f}',
            # 'text': f'Green H2 Capacity vs Offshore Wind Production in DK for 2050 <br>R² = {r2:.2f}',
            'y': 0.84,  
            'x': 0.5,  
            'xanchor': 'center', 
            'yanchor': 'top' 
        },
        xaxis_title= "Natural gas price [€/GJ]",
        yaxis_title=f"Green H2{type}",
        width=600,
        height=500
    )

    fig.show()

def Post_analysis_CO2_tax(df_H2_CAP_GREEN_scen, df_H2_CAP_GREEN_tot_BASE, CO2_tax_base, CO2_Tax_scenario, type : str) :
    
    BO = pd.concat([df_H2_CAP_GREEN_scen['value'], CO2_Tax_scenario], axis=1)
    BO = BO.dropna() 
    #print(BO)
    BO.columns = ['Green H2 Capacity [GW]', 'Capacity [GW]']

    X = BO['Capacity [GW]'].values.reshape(-1, 1)
    y = BO['Green H2 Capacity [GW]'].values

    reg = LinearRegression().fit(X, y)
    y_pred = reg.predict(X)
    r2 = r2_score(y, y_pred)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=BO['Green H2 Capacity [GW]'], mode='markers',showlegend=False))
    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=y_pred, mode='lines', name='Trendline', line=dict(color='red'),showlegend=False))

    new_point_x =  CO2_tax_base
    new_point_y = df_H2_CAP_GREEN_tot_BASE
    #print(new_point_x)
    
    
    fig.add_trace(go.Scatter(
        x=[new_point_x],
        y=[new_point_y],
        mode='markers',
        marker=dict(color='yellow', size=10),
        name='New Point',
        showlegend=False
    ))


    fig.update_layout(
        title={
            'text': f'R² = {r2:.2f}',
            # 'text': f'Green H2 Capacity vs Offshore Wind Production in DK for 2050 <br>R² = {r2:.2f}',
            'y': 0.84,  
            'x': 0.5,  
            'xanchor': 'center', 
            'yanchor': 'top' 
        },
        xaxis_title= "CO2 tax price [€/ ton CO2]",
        yaxis_title=f"Green H2 {type}",
        width=600,
        height=500
    )

    fig.show()

def Post_analysis_SMR_CCS_INVC(df_H2_CAP_GREEN_scen, df_H2_CAP_GREEN_tot_BASE, SMR_CCS_INVC_base, SMR_CCS_INVC_scenario, type : str) :
    
    BO = pd.concat([df_H2_CAP_GREEN_scen['value'], SMR_CCS_INVC_scenario], axis=1)
    BO = BO.dropna() 
    #print(BO)
    BO.columns = ['Green H2 Capacity [GW]', 'Capacity [GW]']

    X = BO['Capacity [GW]'].values.reshape(-1, 1)
    y = BO['Green H2 Capacity [GW]'].values

    reg = LinearRegression().fit(X, y)
    y_pred = reg.predict(X)
    r2 = r2_score(y, y_pred)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=BO['Green H2 Capacity [GW]'], mode='markers',showlegend=False))
    fig.add_trace(go.Scatter(x=BO['Capacity [GW]'], y=y_pred, mode='lines', name='Trendline', line=dict(color='red'),showlegend=False))

    new_point_x =  SMR_CCS_INVC_base
    new_point_y = df_H2_CAP_GREEN_tot_BASE
    #print(new_point_x)
    
    
    fig.add_trace(go.Scatter(
        x=[new_point_x],
        y=[new_point_y],
        mode='markers',
        marker=dict(color='yellow', size=10),
        name='New Point',
        showlegend=False
    ))


    fig.update_layout(
        title={
            'text': f'R² = {r2:.2f}',
            # 'text': f'Green H2 Capacity vs Offshore Wind Production in DK for 2050 <br>R² = {r2:.2f}',
            'y': 0.84,  
            'x': 0.5,  
            'xanchor': 'center', 
            'yanchor': 'top' 
        },
        xaxis_title= "SMR CCS Investement Cost [M€/MW]",
        yaxis_title=f"Green H2 {type}",
        width=600,
        height=500
    )

    fig.show()

                



def Appendix_Violin_Setups_Europe(
    df_H2_BASE_scen_all, df_H2_NoH2_scen_all, df_H2_tot_BASE_all, df_H2_tot_NoH2_all,
    YEAR, type: str, Countries
):
    if type not in ["Green Capacity", "Blue Capacity", "Green Production", "Blue Production", "Storage", "Transmission Capacity", "Transmission Flow"]: 
        raise ValueError(f"Invalid type: {type}")

    # Initialize baseline values array
    baseline_y = np.array(
    [value for i in range(len(Countries)) for value in (df_H2_tot_BASE_all[i], df_H2_tot_NoH2_all[i])])

    # Determine color and unit
    if type in ["Green Capacity", "Green Production"]:
        color = 'green'
    elif type in ["Blue Capacity", "Blue Production"]:
        color = 'blue'
    elif type == "Storage":
        color = 'orange'
        unit = 'TWh'
    elif type == "Transmission Capacity":
        color = 'red'
    elif type == "Transmission Flow":
        color = 'red'

    if "Capacity" in type:
        unit = 'GW'
    elif "Production" in type or "Flow" in type:
        unit = 'TWh'

    # Create plot
    fig = go.Figure()

    # Loop through countries to dynamically create plots
    for i, country in enumerate(Countries):
        # Add categories for each country
        df_H2_BASE_scen_all[i]['category'] = f'Base {country}'
        df_H2_NoH2_scen_all[i]['category'] = f'No H2 Target {country}'

        # Combine dataframes for plotting
        combined_df = pd.concat([df_H2_BASE_scen_all[i], df_H2_NoH2_scen_all[i]])

        # Plot Base Country
        fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == f'Base {country}']['value'], 
                                name=f'Base {country}', box_visible=True, line_color=color))
        fig.add_trace(go.Scatter(x=[f'Base {country}'], y=[baseline_y[i*2]], mode='markers', 
                                marker=dict(color='#3C3D37', size=10), name=f'Baseline Base {country}'))

        # Plot NoH2 Country
        if YEAR == '2030':
            fig.add_trace(go.Violin(y=combined_df[combined_df['category'] == f'No H2 Target {country}']['value'], 
                                    name=f'No H2 Target {country}', box_visible=True, line_color=color))
            fig.add_trace(go.Scatter(x=[f'No H2 Target {country}'], y=[baseline_y[i*2 + 1]], mode='markers', 
                                    marker=dict(color='#3C3D37', size=10), name=f'Baseline No H2 Target {country}'))

    # Update layout
    fig.update_layout(
        title={
            'text': f'Violin Plot: Value Distribution of H2 {type} in ({YEAR})',
            'font': {'size': 16}, 
        },
        yaxis_title=f"H2 {type} [{unit}]",
        yaxis_range=[0, None],
        height=600,
        width=1200,
        legend=dict(orientation='h', x=0.5, y=1, xanchor='center', yanchor='bottom'),  # Adjust legend position
        margin=dict(t=350, b=50)  # Adjust top and bottom margins to accommodate title and legend
    )

    # Show the figure
    fig.show()

    return fig

