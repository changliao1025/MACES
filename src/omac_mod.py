#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 23:42:08 2019

Derived class for organic matter accretion algorithms

@author: Zeli Tan
"""

import numpy as np
import maces_utilities as utils
from TAIMODSuper import OMACMODSuper

###############################################################################
class NULLMOD(OMACMODSuper):
    """Realization of the null organic matter accretion model.

    Attributes:
        Parameters : aa, bb, cc
    Constants:
        
    """ 
    
    # constructor
    def __init__(self, params):
        self.m_params = params
    
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        DepOM = inputs['DepOM']     # OM deposition (kg/m2/s)
        DepOM[:] = 0.0
        return DepOM
    
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass (Morris et al., 2012).
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """
        aa = self.m_params['aa']
        bb = self.m_params['bb']
        cc = self.m_params['cc']
        zh = inputs['zh']           # platform surface elevation (msl)
        MHT = 0.5*inputs['TR']      # mean high tide water level (msl)
        pft = inputs['pft']         # platform pft
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        indice = np.logical_and(np.logical_and(zh>=0,zh<=MHT), 
                                np.logical_and(pft>=2,pft<=5))
        DMHT = MHT - zh
        Bag[indice] = np.maximum(0.0, aa[pft[indice]]*DMHT[indice]+ \
           bb[pft[indice]]*(DMHT[indice]**2)+cc[pft[indice]])
        return Bag
    
###############################################################################
class VDK05MOD(OMACMODSuper):
    """Realization of the null organic matter accretion model with the 
       van de Koppel et al. (2005) Bag scheme.

    Attributes:
        Parameters : rB0, dP, dB, Bmax, czh
    Constants:
        
    """ 
    
    # constructor
    def __init__(self, params):
        self.m_params = params
    
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        DepOM = inputs['DepOM']     # OM deposition (kg/m2/s)
        DepOM[:] = 0.0
        return DepOM
    
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass.
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """
        rB0 = self.m_params['rB0']      # intrinsic growth rate (yr-1)
        Bmax = self.m_params['Bmax']    # maximal standing biomass (kg/m2)
        czh = self.m_params['czh']      # a half-saturation elev constant (m)
        dP = self.m_params['dP']        # plant mortality due to senescence (yr-1)
        dB = self.m_params['dB']        # plant mortality due to wave damage (yr-1)
        zh = inputs['zh']       # platform surface elevation (msl)
        S = inputs['S']         # platform surface slope (m/m)
        Bag = inputs['Bag']     # aboveground biomass (kg/m2)
        pft = inputs['pft']     # platform pft
        dt = inputs['dt']       # time step (s)
        indice = np.logical_and(pft>=2, pft<=5)
        A = rB0[pft[indice]]*(1-Bag[indice]/Bmax[pft[indice]])* \
            (np.maximum(zh[indice],0.0)/(np.maximum(zh[indice],0.0)+ \
            czh[pft[indice]])) - dP[pft[indice]] - dB[pft[indice]]*S[indice]
        Bag[indice] = np.maximum(0.0,Bag[indice]*(1.0+A*dt/3.1536e7)/(1.0-A*dt/3.1536e7))
        return Bag
    
###############################################################################
class M12MOD(OMACMODSuper):
    """Realization of the Morris et al. (2012) organic matter accretion model.

    Attributes:
        parameters : Kr, Tr, phi, aa, bb, cc
    Constants:
        
    """
    
    # constructor
    def __init__(self, params):
        self.m_params = params
        
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        Kr = self.m_params['Kr']    # the refractory fraction of root and rhizome biomass
        Tr = self.m_params['Tr']    # the root and rhizome turnover time (yr)
        phi = self.m_params['phi']  # the root:shoot quotient
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        pft = inputs['pft']         # platform pft
        DepOM = inputs['DepOM']     # OM deposition (kg/m2/s)
        DepOM[:] = 0.0
        indice = Bag>0
        DepOM[indice] = Kr[pft[indice]]*(phi[pft[indice]]*Bag[indice])/ \
            (Tr[pft[indice]]*3.1536e7)
        return DepOM
    
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass (Morris et al., 2012).
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """    
        aa = self.m_params['aa']
        bb = self.m_params['bb']
        cc = self.m_params['cc']
        zh = inputs['zh']           # platform surface elevation (msl)
        MHT = 0.5*inputs['TR']      # mean high tide water level (msl)
        pft = inputs['pft']         # platform pft
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        indice = np.logical_and(np.logical_and(zh>=0,zh<=MHT), 
                                np.logical_and(pft>=2,pft<=5))
        DMHT = MHT - zh[indice]
        Bag[indice] = np.maximum(0.0, aa[pft[indice]]*DMHT+ \
           bb[pft[indice]]*DMHT**2+cc[pft[indice]])
        return Bag

###############################################################################
class DA07MOD(OMACMODSuper):
    """Realization of the D'Alpaos et al. (2007) organic matter accretion model.

    Attributes:
        parameters : Qom0, Bmax, omega, mps
    Constants:
        
    """
    
    # constructor
    def __init__(self, params):
        self.m_params = params
        
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        Qom0 = self.m_params['Qom0']    # a typical OM deposition rate (m/yr)
        Bmax = self.m_params['Bmax']    # maximum Bag (kg/m2)
        rhoOM = self.m_params['rhoOM']  # OM density (kg/m3)
        Bag = inputs['Bag']             # aboveground biomass (kg/m2)
        pft = inputs['pft']             # platform pft
        DepOM = inputs['DepOM']         # OM deposition (kg/m2/s)
        DepOM[:] = 0.0
        indice = Bag>utils.TOL
        DepOM[indice] = Qom0/3.1536e7 * rhoOM * Bag[indice] / Bmax[pft[indice]]
        return DepOM
        
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass.
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """
        Bmax = self.m_params['Bmax']    # maximum Bag (kg/m2)
        omega = self.m_params['omega']  # the ratio of winter Bag to Bps 
        mps = self.m_params['mps']      # month of Bag at its peak
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        zh = inputs['zh']           # platform surface elevation (msl)
        pft = inputs['pft']         # platform pft
        MHT = 0.5*inputs['TR']      # mean high tide water level (msl)
        m = inputs['month']         # month (1 to 12)
        indice = np.logical_and(zh>=0, zh<=MHT)
        Bps = (MHT - zh[indice]) / MHT * Bmax[pft[indice]]   # peak season Bag
        Bag[indice] = 0.5*Bps*(1-omega)*(np.sin(np.pi*m/6-mps*np.pi/12)+1) + \
            omega*Bps
        return Bag

###############################################################################
class KM12MOD(OMACMODSuper):
    """Realization of the Kirwan & Mudd (2012) organic matter accretion model.

    Attributes:
        parameters : Bmax, Tref, sigmaB, rBmin, jdps, thetaBG, Dmbm, 
                     rGmin, rGps, sigmaOM, TrefOM, kl0, kr0
    Constants:
        
    """
    
    # constructor
    def __init__(self, params):
        self.m_params = params
        
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        thetaBG = self.m_params['thetaBG']  # coef for the root:shoot quotient
        Dmbm = self.m_params['Dmbm']        # coef for the root:shoot quotient 
        Bmax = self.m_params['Bmax']        # maximum Bag (kg/m2)
        rBmin = self.m_params['rBmin']      # the ratio of winter Bag to Bps
        Tref = self.m_params['Tref']        # reference temperature for veg growth (K)
        sigmaB = self.m_params['sigmaB']    # biomass increase due to temperature (K-1)
        rGmin = self.m_params['rGmin']      # the ratio of winter growth rate to Bps (day-1)
        rGps = self.m_params['rGps']        # the ratio of peak growth rate to Bps (day-1)
        jdps = self.m_params['jdps']        # the DOY when Bag is at its peak
        Tair = inputs['Tair']           # air temperature (K)
        zh = inputs['zh']               # platform surface elevation (msl)
        pft = inputs['pft']             # platform pft
        MHHW = inputs['MHHW']           # mean high high water level (msl)
        jd = inputs['dofy']             # day (1 to 365)
        DepOM = inputs['DepOM']         # OM deposition (kg/m2/s)
        DepOM[:] = 0.0
        jd_phi = 56     # the phase shift (in days) between Gps and Bps
        indice = np.logical_and(zh>=0, zh<=MHHW)
        # the root:shoot quotient
        phi = thetaBG[pft[indice]]*(MHHW-zh[indice]) + Dmbm[pft[indice]]
        # peak season Bag
        Bps = Bmax[pft[indice]]*(MHHW-zh[indice])/MHHW* \
            (1+(Tair-Tref[pft[indice]])*sigmaB[pft[indice]])
        Bmin = rBmin * Bps          # winter Bag
        Gmin = rGmin/8.64e4 * Bps   # winter growth rate (kg/m2/s)
        Gps = rGps/8.64e4 * Bps     # peak growth rate (kg/m2/s)
        # the mortality rate (kg/m2/s) of aboveground biomass
        Mag = 0.5*(Gmin+Gps+(Gps-Gmin)*np.cos(2.0*np.pi*(jd-jdps+jd_phi)/365)) + \
            np.pi/365*(Bps-Bmin)*np.sin(2.0*np.pi*(jd-jdps)/365)
        DepOM[indice] = np.maximum(phi,0.0) * np.maximum(Mag,0.0)
        return DepOM
        
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass.
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """
        Bmax = self.m_params['Bmax']        # maximum Bag (kg/m2)
        rBmin = self.m_params['rBmin']      # the ratio of winter Bag to Bps
        Tref = self.m_params['Tref']        # reference temperature for veg growth (K)
        sigmaB = self.m_params['sigmaB']    # biomass increase due to temperature (K-1)
        jdps = self.m_params['jdps']        # the DOY when Bag is at its peak
        Tair = inputs['Tair']       # soil temperature (K)
        zh = inputs['zh']           # platform surface elevation (msl)
        pft = inputs['pft']         # platform pft
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        MHHW = inputs['MHHW']       # mean high high water level (msl)
        jd = inputs['dofy']         # day (1 to 365)
        indice = np.logical_and(zh>=0, zh<=MHHW)
        Bps = Bmax[pft[indice]]*(MHHW-zh[indice])/MHHW* \
            (1+(Tair-Tref[pft[indice]])*sigmaB[pft[indice]])
        Bmin = rBmin * Bps          # winter Bag
        Bag[indice] = np.maximum(0.5*(Bmin+Bps+(Bps-Bmin)* \
           np.cos(2*np.pi*(jd-jdps)/365)), 0.0)
        return Bag
    
    def belowground_biomass(self, inputs):
        """"Calculate belowground biomass.
        Arguments:
            inputs : driving data for belowground biomass calculation
        Returns: belowground biomass (kg m-2)
        """
        thetaBG = self.m_params['thetaBG']  # coef for the root:shoot quotient
        Dmbm = self.m_params['Dmbm']        # coef for the root:shoot quotient    
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        Bbg = inputs['Bbg']         # belowground biomass (kg/m2)
        zh = inputs['zh']           # platform surface elevation (msl)
        pft = inputs['pft']         # platform pft
        MHHW = inputs['MHHW']       # mean high high water level (msl)
        indice = np.logical_and(zh>=0, zh<=MHHW)
        phi = thetaBG[pft[indice]]*(MHHW-zh[indice]) + Dmbm[pft[indice]]
        Bbg[indice] = np.maximum(phi,0.0) * np.maximum(Bag[indice],0.0)
        return Bbg
    
    def soilcarbon_decay(self, inputs):
        """"Calculate soil OC mineralization rate.
        klo within [0.5,5.0] and kr0 within [0.00008,0.0015]
        Arguments:
            inputs : driving data for SOC decay rate calculation
        Returns: SOC decay rate (kg m-2 s-1) of two pools
        """
        kl0 = self.m_params['kl0']  # column-integrated decay rate of labile pool (yr-1)
        kr0 = self.m_params['kr0']  # column-integrated decay rate of refractory pool (yr-1)
        TrefOM = self.m_params['TrefOM']    # reference temperature for decay (K)
        sigmaOM = self.m_params['sigmaOM']  # decay increase due to temperature (K-1)
        DecayOM = inputs['DecayOM']     # OM decay rate (kg/m2/s)
        SOM = inputs['OM']              # soil organic matter pools (kg/m2)
        Tsoi = inputs['Tair']           # soil temperature (K)
        Cl = SOM[:,0]                   # labile belowground SOM pool
        Cr = SOM[:,1]                   # refractory belowground SOM pool
        DecayOM[:] = 0.0
        DecayOM[:,0] = ((1.0+(Tsoi-TrefOM)*sigmaOM)*kl0/3.1536e7) * Cl
        DecayOM[:,1] = ((1.0+(Tsoi-TrefOM)*sigmaOM)*kr0/3.1536e7) * Cr
        return DecayOM
        
###############################################################################
class K16MOD(OMACMODSuper):
    """Realization of the Kakeh et al. (2016) organic matter accretion model.

    Attributes:
        parameters : gammaB, Bmax, Gmgv, b2mgv, b3mgv, Mdmax, Mhmax, phi
    Constants:
        
    """
    
    Md = None       # individual mangrove tree diameter (cm)
    Mh = None       # individual mangrove tree height (cm)
    
    # constructor
    def __init__(self, params, nx):
        self.m_params = params
        self.Md = np.zeros(nx, dtype=np.float64, order='F')
        self.Mh = np.zeros(nx, dtype=np.float64, order='F')
        
    def organic_deposition(self, inputs):
        """"Calculate organic matter deposition rate.
        gammaB within [1e-3,3e-3]
        Arguments:
            inputs : driving data for OM deposition calculation
        Returns: organic matter deposition rate (kg m-2 s-1)
        """
        gammaB = self.m_params['gammaB']    # m yr-1 m2 kg-1
        rhoOM = self.m_params['rhoOM']      # OM density (kg/m3)
        DepOM = inputs['DepOM']         # OM deposition (kg/m2/s)
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        DepOM[:] = rhoOM * gammaB/3.1536e7 * Bag
        return DepOM
        
    def aboveground_biomass(self, inputs):
        """"Calculate aboveground biomass.
        Arguments:
            inputs : driving data for OM accretion calculation
        Returns: aboveground biomass (kg m-2)
        """
        Bmax = self.m_params['Bmax']    # maximum Bag (kg/m2)
        Gmgv = self.m_params['Gmgv']    # stem diameter growth rate (cm s-1)
        b2mgv = self.m_params['b2mgv']  # coef for Md vs Mh equation (dimensionless)
        b3mgv = self.m_params['b3mgv']  # coef for Md vs Mh equation (cm-1)
        Mhmax = self.m_params['Mhmax']  # mangrove maximum height (cm)
        Mdmax = self.m_params['Mdmax']  # mangrove maximum diameter (cm)
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        zh = inputs['zh']           # platform surface elevation (msl)
        pft = inputs['pft']         # platform pft
        MHT = 0.5*inputs['TR']      # mean high tide water level (msl)
        dt = inputs['dt']           # time step (s)
        indice_zh = np.logical_and(zh>=0, zh<=MHT)
        # Spartina alterniflora dominated marshes
        indice = np.logical_and(indice_zh, pft==2)
        rz = (1-0.5*zh[indice]/MHT)/3.1536e7   # Bag production rate (s-1)
        mz = 0.5*zh[indice]/MHT/3.1536e7       # Bag mortality rate (s-1)
        Bag[indice] = np.maximum( (1+0.5*(rz*(1-Bag[indice]/Bmax[pft[indice]])-mz)*dt)* \
           Bag[indice]/(1-0.5*(rz*(1-Bag[indice]/Bmax[pft[indice]])-mz)*dt), 0.0 )
        # multi-species marshes
        indice = np.logical_and(np.logical_or(pft==3,pft==4), 
                                indice_zh)
        rz = 0.5*(1+zh[indice]/MHT)
        mz = 0.5*(1-zh[indice]/MHT)
        Bag[indice] = np.maximum( (1+0.5*(rz*(1-Bag[indice]/Bmax[pft[indice]])-mz)*dt)* \
           Bag[indice]/(1-0.5*(rz*(1-Bag[indice]/Bmax[pft[indice]])-mz)*dt), 0.0 )
        # mangroves
        indice = np.logical_and(indice_zh, pft==5)
        P = 1 - zh[indice]/MHT
        I = np.maximum(4*P-8*P**2+0.5, 0.0)
        self.Md[indice] = self.Md[indice] + dt*I*Gmgv/Mdmax/Mhmax* \
            self.Md[indice]*(1-self.Md[indice]*self.Mh[indice])/ \
            (274+3*b2mgv*self.Md[indice]-4*b3mgv*self.Md[indice]**2)
        self.Mh[indice] = 137 + b2mgv*self.Md[indice] + b3mgv*self.Md[indice]**2
        rout = 0.5/self.Md[indice]   # tree density (tree/m2)
        Bag[indice] = rout * 0.308*self.Md[indice]**2.11    # kg/m2
        return Bag
        
    def belowground_biomass(self, inputs):
        """"Calculate belowground biomass.
        Arguments:
            inputs : driving data for belowground biomass calculation
        Returns: belowground biomass (kg m-2)
        """
        phi = self.m_params['phi']  # the root:shoot quotient
        Bbg = inputs['Bbg']         # belowground biomass (kg/m2)
        Bag = inputs['Bag']         # aboveground biomass (kg/m2)
        pft = inputs['pft']         # platform pft
        zh = inputs['zh']           # platform surface elevation (msl)
        MHT = 0.5*inputs['TR']      # mean high tide water level (msl)
        indice_zh = np.logical_and(zh>=0, zh<=MHT)
        # marshes
        indice = np.logical_and(np.logical_and(pft>=2, pft<=4), 
                                indice_zh)
        Bbg[indice] = phi[pft[indice]]*Bag[indice]
        # mangroves
        indice = np.logical_and(indice_zh, pft==5)
        rout = 0.5/self.Md[indice]  # tree density (tree/m2)
        Bbg[indice] = rout * 1.28*self.Md[indice]**1.17
        return Bbg
         
