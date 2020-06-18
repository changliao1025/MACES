#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 09:48:40 2020

Compare the simulated and observed sediment accretion and biomass.

@author: Zeli Tan
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from netCDF4 import Dataset
from datetime import date

# read sediment density and porosity of different mineral accretion models
models = ['F06MOD', 'T03MOD', 'KM12MOD', 'F07MOD', 'VDK05MOD', 'DA07MOD', 'M12MOD']
xmlfile = '/Users/tanz151/Python_maces/src/optpar_minac.xml'
tree = ET.parse(xmlfile)
root = tree.getroot()
rhoSed = {}
porSed = {}
for key in models:
    findstr = "./group/[@id='" + key + "']/entry"
    for entry in root.findall(findstr):
        if entry.get('id')=='rhoSed':
            rhoSed[key] = float(entry.get('value'))
        elif entry.get('id')=='porSed':
            porSed[key] = float(entry.get('value'))

# site elevation
z_LAC = 1.1     # Spartina alterniflora-dominated high salt marsh
z_LPC = 1.4     # Spartina patens-dominated high salt marsh
z_MRS = 0.89    # tall Spartina alterniflora low salt marsh
z_MAR = {'A': [0,0.5], 'B': [0.5,1.0], 'C': [1.0,1.5]}

# read simulation
filename = '/Users/tanz151/Python_maces/src/maces_ecogeom_2017-01-01_2019-01-01_4097.nc'
try:
    nc = Dataset(filename, 'r')
    x = np.array(nc.variables['x'][:])
    zh = np.array(nc.variables['zh'][0,:])
    Esed = np.array(nc.variables['Esed'][:])
    Dsed = np.array(nc.variables['Dsed'][:])
    Bag = np.array(nc.variables['Bag'][:])
finally:
    nc.close()
nx = np.size(x)
dx = np.zeros(nx)
zh0 = np.zeros(nx)
zh1 = np.zeros(nx)
for ii in range(nx):
    if ii==0:
        dx[ii] = 0.5 * (x[ii+1] - x[ii])
        zh0[ii] = zh[ii]
        zh1[ii] = 0.5 * (zh[ii+1] + zh[ii])
    elif ii==nx-1:
        dx[ii] = 0.5 * (x[ii] - x[ii-1])
        zh0[ii] = 0.5 * (zh[ii] + zh[ii-1])
        zh1[ii] = zh[ii]
    else:
        dx[ii] = 0.5 * (x[ii+1] - x[ii-1])
        zh0[ii] = 0.5 * (zh[ii] + zh[ii-1])
        zh1[ii] = 0.5 * (zh[ii] + zh[ii+1])
    
index_LAC = np.argmin(np.abs(zh - z_LAC))
index_LPC = np.argmin(np.abs(zh - z_LPC))
index_MRS = np.argmin(np.abs(zh - z_MRS))

minac_sim_LAC = 0.5e3 * (np.sum(8.64e4*Dsed[:,index_LAC]) - \
    np.sum(8.64e4*Esed[:,index_LAC])) / rhoSed['M12MOD'] / (1.0-porSed['M12MOD']) # mm/yr
minac_sim_LPC = 0.5e3 * (np.sum(8.64e4*Dsed[:,index_LPC]) - \
    np.sum(8.64e4*Esed[:,index_LPC])) / rhoSed['M12MOD'] / (1.0-porSed['M12MOD']) # mm/yr
minac_sim_MRS = 0.5e3 * (np.sum(8.64e4*Dsed[:,index_MRS]) - \
    np.sum(8.64e4*Esed[:,index_MRS])) / rhoSed['M12MOD'] / (1.0-porSed['M12MOD']) # mm/yr
minac_mean_sim = {}
minac_mean_sim['M12MOD'] = np.array([minac_sim_MRS, minac_sim_LAC, minac_sim_LPC])

# read Law's Point marsh biomass and mineral accretion
filename = '/Users/tanz151/Documents/Projects/TAI_BGC/Data/Hydrodynamics_obs/' + \
    'PlumIsland/LawsPoint/LTE-MP-LAC-biomassmeans_3.xls'
df = pd.read_excel(filename, sheet_name='LTE-MP-LAC-biomassmeans', header=0, 
                   usecols='A:F')
df.columns = ['Site', 'Year', 'Month', 'Day', 'Bag', 'Bag_std']
Bag_mean_obs_LAC = np.array(df['Bag'])[96:106]      # g/m2
Bag_std_obs_LAC = np.array(df['Bag_std'])[96:106]   # g/m2
Year_LAC = np.array(df['Year'],dtype=np.int32)[96:106]
Month_LAC = np.array(df['Month'],dtype=np.int32)[96:106]
Bag_sim_LAC = np.NaN * np.ones_like(Bag_mean_obs_LAC)
for ii, year in enumerate(Year_LAC):
    month = Month_LAC[ii]
    day0 = (date(year,month,1) - date(2017,1,1)).days
    day1 = (date(year,month+1,1) - date(2017,1,1)).days
    Bag_sim_LAC[ii] = 1e3 * np.mean(Bag[day0:day1,index_LAC])
Bag_sim_mean_LAC = {}
Bag_sim_mean_LAC['NULLMOD'] = Bag_sim_LAC

# read 2018/07 biomass in three elevation bands: 0-0.5, 0.5-1.0 and 1.0-1.5
filename = '/Users/tanz151/Documents/Projects/TAI_BGC/Data/Hydrodynamics_obs/' + \
    'PlumIsland/Estuary/MAR-SO-Biomass-S-alt-2018.xls'
df = pd.read_excel(filename, sheet_name='MAR-SO-Biomass-S-alt-2018', header=0, 
                   usecols='E,F')
df.columns = ['Bag', 'Elevation']
Bag_tmp = np.array(df['Bag'])           # g/m2
Elev_tmp = np.array(df['Elevation'])    # m
Bag_mean_obs_MAR = {}
Bag_std_obs_MAR = {}
z_MAR_corr = {'A': [-0.1,0.5], 'B': [0.5,1.0], 'C': [1.0,1.5]}
for key in z_MAR_corr:
    elev0 = z_MAR[key][0]
    elev1 = z_MAR[key][1]
    indices = np.logical_and(Elev_tmp>=elev0, Elev_tmp<elev1)
    Bag_mean_obs_MAR[key] = np.mean(Bag_tmp[indices])
    Bag_std_obs_MAR[key] = np.std(Bag_tmp[indices])
Bag_mean_obs = np.array([Bag_mean_obs_MAR['A'], Bag_mean_obs_MAR['B'], Bag_mean_obs_MAR['C']])
Bag_std_obs = np.array([Bag_std_obs_MAR['A'], Bag_std_obs_MAR['B'], Bag_std_obs_MAR['C']])
Bag_sim_MAR = {}
day0 = (date(2018,7,1) - date(2017,1,1)).days
day1 = (date(2018,8,1) - date(2017,1,1)).days
for key in z_MAR:
    elev0 = z_MAR[key][0]
    elev1 = z_MAR[key][1]
    index0 = np.argmin(np.abs(zh - elev0))
    index1 = np.argmin(np.abs(zh - elev1))
    Bag_tot = 0.0
    x_tot = 0.0
    for index in np.arange(index0,index1+1):
        frac = (min(zh1[index],elev1) - max(zh0[index],elev0)) / \
            (zh1[index] - zh0[index])
        Bag_tot = Bag_tot + np.mean(Bag[day0:day1,index])*frac*dx[index]
        x_tot = x_tot + frac*dx[index]
    Bag_sim_MAR[key] = Bag_tot / x_tot
Bag_mean_sim = {}
Bag_mean_sim['NULLMOD'] = np.array([Bag_sim_MAR['A'], Bag_sim_MAR['B'], Bag_sim_MAR['C']])
    
# from LTE-MP-LAC-elevationmeans_1.xls
minac_mean_obs_LAC = 5.3    # mm/yr
minac_std_obs_LAC = 0.1     # mm/yr

# from LTE-MP_LPC-elevationmeans_1.xls
minac_mean_obs_LPC = 2.3    # mm/yr
minac_std_obs_LPC = 0.1     # mm/yr

# from Wilson et al. (2014)
minac_mean_obs_MRS = 6.9    # mm/yr
minac_std_obs_MRS = 0.9     # mm/yr

minac_mean_obs = np.array([minac_mean_obs_MRS, minac_mean_obs_LAC, minac_mean_obs_LPC])
minac_std_obs = np.array([minac_std_obs_MRS, minac_std_obs_LAC, minac_std_obs_LPC])
    
# plot
plt.clf()
fig = plt.figure(figsize=(8,8))

plt.style.use('default')

colors = ["#aee39a", "#643176", "#4be32e", "#e72fc2", "#518413", "#7540fc", 
          "#b3e61c"]
linestyles = ['-', '--', '-.', ':', '-', '--', '-.']

# mineral accretion vs elevation
ax = plt.subplot2grid((2,2), (0,0))
xpos = np.arange(1,4)
hbar = ax.bar(xpos, minac_mean_obs, yerr=minac_std_obs, align='center', 
              width=0.8, color='#d8dcd6', ecolor='black', capstyle='butt', 
              capsize=2, alpha=1.0)
handles = []
for key in minac_mean_sim:
    indx = len(handles)
    h, = ax.plot(xpos, minac_mean_sim[key], color=colors[indx], marker='.',
                 ms=10, mfc='black', mec='black', linestyle=linestyles[indx], 
                 linewidth=2, alpha=1)
    handles.append(h)
legend = plt.legend(handles, list(minac_mean_sim.keys()), numpoints=1, loc=1, 
                    framealpha=0.0,
                    prop={'family':'Times New Roman', 'size':'medium'})
ax.set_xlim(0, 4)
#ax.set_ylim(0, 300)
ax.xaxis.set_ticks(np.arange(1,4,1))
#ax.yaxis.set_ticks(np.linspace(0,300,6))
ax.set_xticklabels(['LAC','LPC','MRS'])
#ax.set_xlabel('Time', fontsize=11, fontname='Times New Roman', color='black')
ylabel = 'Mineral accretion ($\mathregular{mm}$ $\mathregular{{yr}^{-1}}$)'
ax.set_ylabel(ylabel, fontsize=12, fontname='Times New Roman', color='black')
labels = ax.get_xticklabels() + ax.get_yticklabels()
[label.set_fontname('Times New Roman') for label in labels]
[label.set_fontsize(12) for label in labels]
[label.set_color('black') for label in labels]
ax.text(0.06, 0.93, 'a', transform=ax.transAxes, fontsize=16,
        fontname='Times New Roman', fontweight='bold')
ax.tick_params(which='major', direction='in', colors='xkcd:black', length=6, pad=8)
ax.tick_params(which='minor', direction='in', colors='xkcd:black')

# biomass vs elevation 
ax = plt.subplot2grid((2,2), (0,1))
xpos = np.arange(1,4)
hbar = ax.bar(xpos, Bag_mean_obs, yerr=Bag_std_obs, align='center', 
              width=0.8, color='#d8dcd6', ecolor='black', capstyle='butt', 
              capsize=2, alpha=1.0)
handles = []
for key in Bag_mean_sim:
    indx = len(handles)
    h, = ax.plot(xpos, Bag_mean_sim[key], color=colors[indx], marker='.',
                 ms=10, mfc='black', mec='black', linestyle=linestyles[indx], 
                 linewidth=2, alpha=1)
    handles.append(h)
legend = plt.legend(handles, list(Bag_mean_sim.keys()), numpoints=1, loc=1, 
                    prop={'family':'Times New Roman', 'size':'medium'}, 
                    framealpha=0.0)
ax.set_xlim(0, 4)
#ax.set_ylim(0, 300)
ax.xaxis.set_ticks(np.arange(1,4,1))
#ax.yaxis.set_ticks(np.linspace(0,300,6))
ax.set_xticklabels(['0–0.5 m','0.5–1 m','1–1.5 m'])
#ax.set_xlabel('Time', fontsize=11, fontname='Times New Roman', color='black')
ylabel = 'Biomass ($\mathregular{g}$ $\mathregular{{m}^{-2}}$)'
ax.set_ylabel(ylabel, fontsize=12, fontname='Times New Roman', color='black')
labels = ax.get_xticklabels() + ax.get_yticklabels()
[label.set_fontname('Times New Roman') for label in labels]
[label.set_fontsize(12) for label in labels]
[label.set_color('black') for label in labels]
ax.text(0.06, 0.93, 'b', transform=ax.transAxes, fontsize=16,
        fontname='Times New Roman', fontweight='bold')
ax.tick_params(which='major', direction='in', colors='xkcd:black', length=6, pad=8)
ax.tick_params(which='minor', direction='in', colors='xkcd:black')

# biomass seasonality
ax = plt.subplot2grid((2,2), (1,0), colspan=2)
xpos = np.arange(1,11)
hbar = ax.bar(xpos, Bag_mean_obs_LAC, yerr=Bag_std_obs_LAC, align='center', 
              width=0.8, color='#d8dcd6', ecolor='black', capstyle='butt', 
              capsize=2, alpha=1.0)
handles = []
for key in Bag_sim_mean_LAC:
    indx = len(handles)
    h, = ax.plot(xpos, Bag_sim_mean_LAC[key], color=colors[indx], marker='.', 
                 ms=10, mfc='black', mec='black', linestyle=linestyles[indx], 
                 linewidth=2, alpha=1)
    handles.append(h)
legend = plt.legend(handles, list(Bag_sim_mean_LAC.keys()), numpoints=1, loc=1, 
                    prop={'family':'Times New Roman', 'size':'medium'}, 
                    framealpha=0.0)
ax.set_xlim(0, 11)
#ax.set_ylim(0, 300)
ax.xaxis.set_ticks(np.arange(1,11,1))
#ax.yaxis.set_ticks(np.linspace(0,300,6))
ax.set_xticklabels(['17/5','17/6','17/7','17/8','17/10','18/5','18/6','18/7', 
                    '18/8','18/10'])
#ax.set_xlabel('Time', fontsize=11, fontname='Times New Roman', color='black')
ylabel = 'Biomass ($\mathregular{g}$ $\mathregular{{m}^{-2}}$)'
ax.set_ylabel(ylabel, fontsize=12, fontname='Times New Roman', color='black')
labels = ax.get_xticklabels() + ax.get_yticklabels()
[label.set_fontname('Times New Roman') for label in labels]
[label.set_fontsize(12) for label in labels]
[label.set_color('black') for label in labels]
ax.text(0.03, 0.93, 'c', transform=ax.transAxes, fontsize=16,
        fontname='Times New Roman', fontweight='bold')
ax.tick_params(which='major', direction='in', colors='xkcd:black', length=6, pad=8)
ax.tick_params(which='minor', direction='in', colors='xkcd:black')

plt.tight_layout()
fig.savefig('F10.png', dpi=300)
#fig.savefig('F10.pdf', dpi=600)
plt.show()