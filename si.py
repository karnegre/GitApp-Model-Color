import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
from plotly import express as px
import os
import os.path
import streamlit as st


# -----------------------------------------------------------------------
## function to plot out each LED spectrum, which is a gaussian
def gaussian(fwhm,x0,x):
    ## fwhm = full width half max
    sigma=fwhm/(2*np.sqrt(2*np.log(2)))
    answer=np.exp(-((x-x0)**2)/(2*sigma**2))
    answer*= 1/(sigma*np.sqrt(2*np.pi))
    return answer

LEDwavecolordict={370:'#00c6ff',450:'#0046ff',525:'#4aff00',585:'#ffef00',625:'#ff6300',
              685:'#ff0000',755:'#970000',800:'#610000',925:'#3a0000'}
LEDbandcolordict={'Band1':'#00c6ff','Band2':'#0046ff','Band3':'#4aff00','Band4':'#ffef00','Band5':'#ff6300',
              'Band6':'#ff0000','Band7':'#970000','Band8':'#610000','Band9':'#3a0000'}

#-------------------------------------------------------------------------
# Inputs
cwd =os.getcwd()

## illumination sources
filename_DISR = "DISRspectrumUniformWavelegnths.csv"
path_file_DISR = os.sep.join([cwd,'color','si', filename_DISR])
DISR=pd.read_csv(path_file_DISR)
DISR= DISR.set_index('wave_nm', drop = False, inplace=False)
DISR
st.write(len(DISR.index))

filename_LED = "LEDspectraUniformWavelegnths.csv"
path_file_LED = os.sep.join([cwd,'color', 'si', filename_LED])
LEDs= pd.read_csv(path_file_LED)
LEDs= LEDs.set_index('wave_nm', drop = False, inplace=False)
LEDs

## surface spectra, downloaded from the streamlit app
filename_surface = "Propadiene-Tholin He 21-Water Ice.csv"
path_file_surf = os.sep.join([cwd, 'color','si', filename_surface])
surfin=pd.read_csv(path_file_surf,skiprows=1,
                    names=('wave','propadine','tholin (He 21)','waterice','propadine40% \n tholin20% \n water40%','propadine20% \n tholin50% \n water30%'))
surfin= surfin.set_index('wave', drop = False, inplace=False)
surfin
# Option to upload a csv or make this entire thing a function

## Bayer Pattern QEs
filename_QE_R = "RQEUniformWavelegnths.csv"
path_file_QE_R = os.sep.join([cwd, 'color','si', filename_QE_R])
RQE=pd.read_csv(path_file_QE_R)
RQE= RQE.set_index('wave_nm', drop = False, inplace=False)
RQE

filename_QE_G = "GQEUniformWavelegnths.csv"
path_file_QE_G = os.sep.join([cwd, 'color','si', filename_QE_G])
GQE=pd.read_csv(path_file_QE_G)
GQE= GQE.set_index('wave_nm', drop = False, inplace=False)
GQE

filename_QE_B = "BQEUniformWavelegnths.csv"
path_file_QE_B = os.sep.join([cwd, 'color','si', filename_QE_B])
BQE=pd.read_csv(path_file_QE_B)
BQE= BQE.set_index('wave_nm', drop = False, inplace=False)
BQE

## detector bandpass limits (nm)
micro_bandpass = [440,960] # TBD
fordown_bandpass = [540,960]
pan_bandpass = [440,960] # probably will be set to same as forward/downward

# ------------------------------------------------------------------
# STEP 0: Illumination spectrum
# Light that comes in --> either from sun (DISR) or LEDs
st.set_option('deprecation.showPyplotGlobalUse', False)

st.header("Step 0: Illumination Spectrum")
plt.figure(figsize=(8,4.5))
ax1 = plt.subplot(1,2,1)
ax1.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],color='k')
ax1.set_title('DISR')
plt.ylabel('Observed Solar Flux \n (W/m2/micron/Ster)')
plt.xlabel('Wavelength (nm)')


ax2 = plt.subplot(1,2,2)
for c in LEDs.columns[1:]:
    plt.plot(LEDs.wave_nm,LEDs[c],c=LEDbandcolordict[c])
plt.title('LEDs')
plt.xlabel('Wavelength (nm)')
plt.ylabel('')
plt.tight_layout()
st.pyplot()

# ------------------------------------------------------------------
# STEP 1: Illuminate Surface
# Light that encounters surface--> white, spectra, black
st.header("Step 1: Illuminate Surface")
plt.figure(figsize=(16,9))
plt.subplot(2,5,1)
plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],label='solar flux',color='k',linewidth=2)
for c in surfin.columns[0:-1]:
    plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin[c],label=c)

plt.title('DISR')
plt.ylabel('Observed Solar Flux \n (W/m2/micron/Ster)')
plt.xlabel('Wavelength (nm)')

for i,l in enumerate(LEDs.columns[1:]):
    plt.subplot(2,5,i+2)
    plt.plot(LEDs.wave_nm,LEDs[l],c='k')
    for c in surfin.columns[0:-1]:
        plt.plot(LEDs.wave_nm,LEDs[l]*surfin[c],label=c)

    plt.title('LED '+str(l))
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('')
    if i==0:
        plt.legend()


# plt.tight_layout()
st.pyplot()

plt.figure(figsize=(16,9))
plt.subplot(2,3,1)
plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],label='solar flux',color='k',linewidth=2)
for c in surfin.columns[1:-1]:
    # st.write(surfin.columns[1:-1])
    plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin[c],label=c)

plt.title('DISR')
plt.ylabel('Observed Solar Flux \n (W/m2/micron/Ster)')
plt.xlabel('Wavelength (nm)')

for i,c in enumerate(surfin.columns[1:-1]):

    plt.subplot(2,3,i+2)
    plt.plot(surfin.index,surfin[c],c='k')
    for l in LEDs.columns[1:]:
        plt.plot(LEDs.wave_nm,LEDs[l],c='k',alpha=0.5)
        plt.plot(LEDs.wave_nm,LEDs[l]*surfin[c],label=c)
        #color dictionary

    plt.title(c)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('')


plt.tight_layout()
st.pyplot()
#What is significance of this plot? The black line is the flux of the compound?-->vertical line....

# ------------------------------------------------------------------
# STEP 2: Illuminaion on Surface through Bayer Filter
# The light reflected off the surface is then filtered through the bayer filters on each pixel
st.header("Step 2: Surface Illumination Passes through Bayer Filter")
st.subheader("Bayer Filters through different bandpass limits")
plt.figure(figsize=(16,2.5))
plt.subplot(1,3,1)
plt.fill_between(RQE.wave_nm,RQE.QE,0,color='r',alpha=0.5)
plt.fill_between(GQE.wave_nm,GQE.QE,0,color='g',alpha=0.5)
plt.fill_between(BQE.wave_nm,BQE.QE,0,color='b',alpha=0.5)
plt.title('Bayer Filters with Full Bandpass')

plt.subplot(1,3,2)

plt.fill_between(RQE[(RQE.wave_nm > micro_bandpass[0]) & (RQE.wave_nm < micro_bandpass[1])].wave_nm,RQE[(RQE.wave_nm > micro_bandpass[0]) & (RQE.wave_nm <micro_bandpass[1])].QE,0,color='r',alpha=0.5)
plt.fill_between(GQE[(GQE.wave_nm > micro_bandpass[0]) & (GQE.wave_nm <micro_bandpass[1])].wave_nm,GQE[(GQE.wave_nm > micro_bandpass[0]) & (GQE.wave_nm <micro_bandpass[1])].QE,0,color='g',alpha=0.5)
plt.fill_between(BQE[(BQE.wave_nm > micro_bandpass[0]) & (BQE.wave_nm <micro_bandpass[1])].wave_nm,BQE[(BQE.wave_nm > micro_bandpass[0]) & (BQE.wave_nm <micro_bandpass[1])].QE,0,color='b',alpha=0.5)
plt.title('Bayer Filters with '+str(micro_bandpass[0])+'-'+str(micro_bandpass[1])+' nm Bandpass')
plt.xlim(BQE.wave_nm.min(),BQE.wave_nm.max())

plt.subplot(1,3,3)

plt.fill_between(RQE[(RQE.wave_nm > fordown_bandpass[0]) & (RQE.wave_nm < fordown_bandpass[1])].wave_nm,RQE[(RQE.wave_nm > fordown_bandpass[0]) & (RQE.wave_nm <fordown_bandpass[1])].QE,0,color='r',alpha=0.5)
plt.fill_between(GQE[(GQE.wave_nm > fordown_bandpass[0]) & (GQE.wave_nm <fordown_bandpass[1])].wave_nm,GQE[(GQE.wave_nm > fordown_bandpass[0]) & (GQE.wave_nm <fordown_bandpass[1])].QE,0,color='g',alpha=0.5)
plt.fill_between(BQE[(BQE.wave_nm > fordown_bandpass[0]) & (BQE.wave_nm <fordown_bandpass[1])].wave_nm,BQE[(BQE.wave_nm > fordown_bandpass[0]) & (BQE.wave_nm <fordown_bandpass[1])].QE,0,color='b',alpha=0.5)
plt.title('Bayer Filters with '+str(fordown_bandpass[0])+'-'+str(fordown_bandpass[1])+' nm Bandpass')
plt.xlim(BQE.wave_nm.min(),BQE.wave_nm.max())

plt.tight_layout()
st.pyplot()

# ------
# plt.figure(figsize=(16,2.5))
# plt.subplot(1,3,1)
# plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
# plt.plot(surfin.wave,surfin['waterice'],'k--')
# plt.fill_between(RQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*RQE.QE,0,color='r',alpha=0.1)
# plt.fill_between(GQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*GQE.QE,0,color='g',alpha=0.1)
# plt.fill_between(BQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*BQE.QE,0,color='b',alpha=0.1)
# plt.title('DISR / Water Ice / Full Bayer ')
#
# ####
#
# plt.subplot(1,3,2)
# plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
# plt.plot(surfin.wave,surfin['waterice'],'k--')
#
# limitillumination=DISR[(DISR.wave_nm > micro_bandpass[0]) &(DISR.wave_nm <micro_bandpass[1])]
# limitreflectance=surfin[(surfin.wave > micro_bandpass[0]) &(surfin.wave <micro_bandpass[1])]['waterice']
# limitR=RQE[(RQE.wave_nm > micro_bandpass[0]) & (RQE.wave_nm < micro_bandpass[1])].QE
# limitG=GQE[(GQE.wave_nm > micro_bandpass[0]) & (GQE.wave_nm <micro_bandpass[1])].QE
# limitB=BQE[(BQE.wave_nm > micro_bandpass[0]) & (BQE.wave_nm <micro_bandpass[1])].QE
#
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitR,
#                  0,color='r',alpha=0.5)
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitG,
#                  0,color='g',alpha=0.5)
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitB,
#                  0,color='b',alpha=0.5)
# plt.title('DISR / Water Ice / '+str(micro_bandpass[0])+'-'+str(micro_bandpass[1])+' nm Bandpass Bayer')
# plt.xlim(BQE.wave_nm.min(),BQE.wave_nm.max())
#
#
# ###
# plt.subplot(1,3,3)
# plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
# plt.plot(surfin.wave,surfin['waterice'],'k--')
#
# limitillumination=DISR[(DISR.wave_nm > fordown_bandpass[0]) &(DISR.wave_nm <fordown_bandpass[1])]
# limitreflectance=surfin[(surfin.wave > fordown_bandpass[0]) &(surfin.wave <fordown_bandpass[1])]['waterice']
# limitR=RQE[(RQE.wave_nm > fordown_bandpass[0]) & (RQE.wave_nm < fordown_bandpass[1])].QE
# limitG=GQE[(GQE.wave_nm > fordown_bandpass[0]) & (GQE.wave_nm <fordown_bandpass[1])].QE
# limitB=BQE[(BQE.wave_nm > fordown_bandpass[0]) & (BQE.wave_nm <fordown_bandpass[1])].QE
#
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitR,
#                  0,color='r',alpha=0.5)
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitG,
#                  0,color='g',alpha=0.5)
# plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitB,
#                  0,color='b',alpha=0.5)
# plt.title('DISR / Water Ice / '+str(fordown_bandpass[0])+'-'+str(fordown_bandpass[1])+' nm Bandpass Bayer')
# plt.xlim(BQE.wave_nm.min(),BQE.wave_nm.max())
#
# plt.tight_layout()
# st.pyplot()

# ---------
st.subheader("DISR Illumination Bayer Filters")
plt.figure(figsize=(16,2.5))
plt.subplot(1,3,1)
plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
plt.plot(surfin.index,surfin['waterice'],'k--')
plt.fill_between(RQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*RQE.QE,0,color='r',alpha=0.25)
plt.fill_between(GQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*GQE.QE,0,color='g',alpha=0.1)
plt.fill_between(BQE.wave_nm,DISR['flux_W/m2/micron/Ster']*surfin['waterice']*BQE.QE,0,color='b',alpha=0.1)
plt.title('DISR / Water Ice / Full Bayer ')
plt.xlim(BQE.wave_nm.min(),BQE.wave_nm.max())
####

plt.subplot(1,3,2)
plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
plt.plot(surfin.index,surfin['waterice'],'k--')

limitillumination=DISR[(DISR.wave_nm > micro_bandpass[0]) &(DISR.wave_nm <micro_bandpass[1])]
limitreflectance=surfin[(surfin.index > micro_bandpass[0]) &(surfin.index <micro_bandpass[1])]['waterice']

limitR=RQE[(RQE.wave_nm > micro_bandpass[0]) & (RQE.wave_nm < micro_bandpass[1])].QE
limitG=GQE[(GQE.wave_nm > micro_bandpass[0]) & (GQE.wave_nm <micro_bandpass[1])].QE
limitB=BQE[(BQE.wave_nm > micro_bandpass[0]) & (BQE.wave_nm <micro_bandpass[1])].QE

plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitR,
                 0,color='r',alpha=0.25)
plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitG,
                 0,color='g',alpha=0.1)
plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitB,
                 0,color='b',alpha=0.1)
plt.title('DISR / Water Ice / '+str(micro_bandpass[0])+'-'+str(micro_bandpass[1])+' nm Bandpass Bayer')
plt.xlim(GQE.wave_nm.min(),GQE.wave_nm.max())


###
plt.subplot(1,3,3)
plt.plot(DISR.wave_nm,DISR['flux_W/m2/micron/Ster'],'k')
plt.plot(surfin.index,surfin['waterice'],'k--')

limitillumination=DISR[(DISR.wave_nm > fordown_bandpass[0]) &(DISR.wave_nm <fordown_bandpass[1])]
limitreflectance=surfin[(surfin.index > fordown_bandpass[0]) &(surfin.index <fordown_bandpass[1])]['waterice']
limitR=RQE[(RQE.wave_nm > fordown_bandpass[0]) & (RQE.wave_nm < fordown_bandpass[1])].QE
limitG=GQE[(GQE.wave_nm > fordown_bandpass[0]) & (GQE.wave_nm <fordown_bandpass[1])].QE
limitB=BQE[(BQE.wave_nm > fordown_bandpass[0]) & (BQE.wave_nm <fordown_bandpass[1])].QE

plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitR,
                 0,color='r',alpha=0.5)
plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitG,
                 0,color='g',alpha=0.5)
plt.fill_between(limitillumination.wave_nm,limitillumination['flux_W/m2/micron/Ster']*limitreflectance*limitB,
                 0,color='b',alpha=0.5)
plt.title('DISR / Water Ice / '+str(fordown_bandpass[0])+'-'+str(fordown_bandpass[1])+' nm Bandpass Bayer')
plt.xlim(RQE.wave_nm.min(),RQE.wave_nm.max())


st.pyplot()

# ---------
st.subheader("LED Illumination Bayer Filters")
material='waterice'
surfrefl=surfin[['wave',material]]

fig,axarr=plt.subplots(9,3,figsize=(11,11))

print(np.shape(axarr))

for i,l in enumerate(LEDs.columns[1:]):
    axarr[i,0].fill_between(RQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*RQE.QE,0,color='r',alpha=0.3)
    axarr[i,0].fill_between(GQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*GQE.QE,0,color='g',alpha=0.3)
    axarr[i,0].fill_between(BQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*BQE.QE,0,color='b',alpha=0.3)
    dummyax=axarr[i,0].twinx()
    dummyax.plot(LEDs.wave_nm,LEDs[l],'k',alpha=0.5)
    plt.legend(labels=(l),frameon=False,)

    limitillumination=LEDs[(LEDs.wave_nm > micro_bandpass[0]) &(LEDs.wave_nm <micro_bandpass[1])]
    limitreflectance=surfin[(surfin.index > micro_bandpass[0]) &(surfin.index <micro_bandpass[1])]['waterice']
    limitR=RQE[(RQE.wave_nm > micro_bandpass[0]) & (RQE.wave_nm < micro_bandpass[1])].QE
    limitG=GQE[(GQE.wave_nm > micro_bandpass[0]) & (GQE.wave_nm <micro_bandpass[1])].QE
    limitB=BQE[(BQE.wave_nm > micro_bandpass[0]) & (BQE.wave_nm <micro_bandpass[1])].QE
    axarr[i,1].fill_between(RQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitR,0,color='r',alpha=0.3)
    axarr[i,1].fill_between(GQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitG,0,color='g',alpha=0.3)
    axarr[i,1].fill_between(BQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitB,0,color='b',alpha=0.3)
    dummyax=axarr[i,1].twinx()
    dummyax.plot(LEDs.wave_nm,LEDs[l],'k',alpha=0.5)

    limitillumination=DISR[(DISR.wave_nm > fordown_bandpass[0]) &(DISR.wave_nm <fordown_bandpass[1])]
    limitreflectance=surfin[(surfin.index > fordown_bandpass[0]) &(surfin.index <fordown_bandpass[1])]['waterice']
    limitR=RQE[(RQE.wave_nm > fordown_bandpass[0]) & (RQE.wave_nm < fordown_bandpass[1])].QE
    limitG=GQE[(GQE.wave_nm > fordown_bandpass[0]) & (GQE.wave_nm <fordown_bandpass[1])].QE
    limitB=BQE[(BQE.wave_nm > fordown_bandpass[0]) & (BQE.wave_nm <fordown_bandpass[1])].QE

    axarr[i,2].fill_between(RQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitR,0,color='r',alpha=0.3)
    axarr[i,2].fill_between(GQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitG,0,color='g',alpha=0.3)
    axarr[i,2].fill_between(BQE.wave_nm,LEDs[l]*surfrefl.iloc[:, 1]*limitB,0,color='b',alpha=0.3)
    dummyax=axarr[i,2].twinx()
    dummyax.plot(LEDs.wave_nm,LEDs[l],'k',alpha=0.5)


axarr[0,0].set_title('DISR / '+material+' / \n Full Bayer ')
axarr[0,1].set_title('DISR / '+material+' / \n'+str(micro_bandpass[0])+'-'+str(micro_bandpass[1])+' nm Bandpass Bayer')
axarr[0,2].set_title('DISR / '+material+' / \n'+str(fordown_bandpass[0])+'-'+str(fordown_bandpass[1])+' nm Bandpass Bayer')

plt.tight_layout()
st.pyplot()
