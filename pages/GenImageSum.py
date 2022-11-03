import os.path
import cameraclass as cc
import illuminationclass as il
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib as mpl
import glob

# -----------------------Function Library--------------------------------------
def app():
    st.header("Welcome to the Synthetic Color Tool")
    # st.subheader("You have the option to select from a library of pre-canned multi-composite spectra from the Dragonfly Surface Composition Modeling tools")
    st.caption("You have the option to select from a library of pre-canned multi-composite spectra from the Dragonfly Surface Composition Modeling tools. By toggling parameters like camera type and illumination mode, we are able to generate a variety of color swatches for what DragonCam might see on Titan's surface.")

    #Creates drop-down to select surface reflectance
    cwd =os.getcwd()
    path= os.path.join( cwd,'MixedSpectraLib')             # use your path
    all_files = glob.glob(os.path.join(path, "*.csv"))     # advisable to use os.path.join as this makes concatenation OS independent
    data = {}
    result_df_led=[]
    result_df_led_N=[]
    LED_bands=[]
    for filename in all_files:
        data[filename[40:-4]] = pd.read_csv(filename)

    colsel1,colsel2,colsel3 = st.columns(3)
    with colsel1:
        specpick = st.selectbox(
        "Select a Spectra", sorted(data.keys()), help = "This is a library of pre-canned spectra from the Dragonfly Surface Composition Modeling App" )
        compound=pd.DataFrame(data.get(specpick).iloc[:, 0:2])
        compound.set_index('wave', inplace=True)
        comp_export=compound.copy()
        comp_export['wave_nm']=[w*1000 for w in comp_export.index]
        comp_export=comp_export.rename(columns={comp_export.columns[0]: 'refl'})
        ## Cal target
        white = pd.DataFrame({'wave_nm':comp_export.wave_nm,'refl':np.ones_like(comp_export.refl)})

    with colsel2:
        cam_pick = st.selectbox("Select a camera",['WAC','MAC','Microscopic'], help = "Wide angle camera, Medium angle camera, and Microscopic")
        cam=cc.camera(cam_pick)

    with colsel3:
        #this can be changed to st.multiselect to select multiple illumination modes. Im only doing one selection for aesthetics
        ilumpick= st.selectbox("Select a illumination mode",['Day','Night','Day+', 'Single'])
        if ilumpick == 'Single':
            LED_bands= st.multiselect('Select your single LED band(s): ',['band1','band2','band3','band4','band5','band6','band7','band8','band9'])
        # int_time=st.number_input('Input the integration time in seconds: ', min_value= .0001, max_value=1800.000)
        # int_time = 0.001

    st.header("Simulated Titan Imaging with Bayer Filters")

    col1,col2 = st.columns(2)
    with col1:
        compound.index = [w*1000 for w in compound.index]
        fig= plt.figure(figsize=(6, 3),dpi=300)
        plt.plot(compound.truncate(after=1250))  # Plot some data on the (implicit) axes.
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Reflactance')
        plt.title("Reflectance Spectra for " + str(specpick))
        plt.xlim(cam.bandpasslimits[0],cam.bandpasslimits[1])
        # plt.legend();
        st.pyplot(fig)

    # for i in ilumpick:
    mode=il.illumination(ilumpick,LED_bands)
    # When we sum Day+ in the illum class we sum both the wave_nm and flux columns putting the wavelength range at 800-2098 instead of 400-1049
    if ilumpick == 'Day+':
        mode.fluxspectrum.wave_nm=mode.fluxspectrum.wave_nm/2
    thispix=cc.pixelobserve(mode,comp_export,cam,cam.integrationtime_s)
    calibration=cc.pixelobserve(mode,white,cam,cam.integrationtime_s)
    normpix= thispix/calibration
    # st.subheader("Illumination mode selected: " + mode.description)
    # st.caption("540-960 nm Bandpass")


    with col2:

        illumfig, ax= plt.subplots(figsize=(5.95, 2.75),dpi=300)
        ax2=ax.twinx()
        ax.plot(mode.fluxspectrum.wave_nm, mode.fluxspectrum.flux, label= str(ilumpick) + ' illumination spectra', color = 'k')  # Plot some data on the (implicit) axes.
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Flux (W/m2/micron/Ster)')

        # st.write(mode.fluxspectrum)
        # st.write(mode.fluxspectrum.wave_nm)
        # st.write(cam.bandpasslimits[0])

        limitillumination=mode.fluxspectrum[(mode.fluxspectrum.wave_nm > cam.bandpasslimits[0]) &(mode.fluxspectrum.wave_nm < cam.bandpasslimits[1])]
        limitreflectance=compound[(compound.index > cam.bandpasslimits[0]) & (compound.index <cam.bandpasslimits[1]-1)].iloc[:, 0]
        limitR=mode.RQE[((mode.RQE.wave_nm) > cam.bandpasslimits[0]) & ((mode.RQE.wave_nm) < cam.bandpasslimits[1])].QE
        limitG=mode.GQE[((mode.GQE.wave_nm) > cam.bandpasslimits[0]) & ((mode.GQE.wave_nm) < cam.bandpasslimits[1])].QE
        limitB=mode.BQE[((mode.BQE.wave_nm) > cam.bandpasslimits[0]) & ((mode.BQE.wave_nm) < cam.bandpasslimits[1])].QE

        #Aligning the indices for multiplication step below
        limitillumination.reset_index(drop=True, inplace=True)
        limitreflectance.reset_index(drop=True, inplace=True)
        limitR.reset_index(drop=True, inplace=True)
        limitG.reset_index(drop=True, inplace=True)
        limitB.reset_index(drop=True, inplace=True)

        #flux*reflectance= photons times scattered in dir of detectors times filter
        #instead plot the bayer pattern filters independent from interference to give us color info
        ax2.fill_between(limitillumination.wave_nm,limitR,
                         0,color='r',alpha=0.5)
        ax2.fill_between(limitillumination.wave_nm,limitG,
                         0,color='g',alpha=0.5)
        ax2.fill_between(limitillumination.wave_nm,limitB,
                         0,color='b',alpha=0.5)
        ax2.set_ylabel('Bayer Pattern Efficiency')
        plt.xlim(cam.bandpasslimits[0],cam.bandpasslimits[1])
        plt.title( str(ilumpick)+ " Illumination & Bayer Filters")
        st.pyplot(illumfig)
        st.caption(mode.description)
    # st.header("Simulated Titan Imaging with Bayer Filters")
    dfSolarN = pd.DataFrame(np.row_stack(normpix),index=compound.columns, columns =['R','G','B'])
    dfSolar = pd.DataFrame(np.row_stack(thispix),index=compound.columns, columns =['R','G','B'])

    row=len(dfSolar)
    DfSolarNfin= dfSolarN.to_numpy().reshape((1,row,3))
    DfSolarfin= dfSolar.to_numpy().reshape((1,row,3))

    st.header("RGB Values & Synthetic Color at Titan's Surface for " + str(specpick))
    col3,col4 = st.columns(2)

    with col3:
        st.subheader(str(ilumpick) + " Mode Illumination (Normalized to White)")
        st.table(dfSolarN)
        ax1= plt.figure(figsize=(3,15),dpi=300)
        plt.imshow(DfSolarNfin)
        plt.xticks([])
        plt.yticks([])
        st.pyplot(ax1)
    with col4:
        st.subheader(str(ilumpick) + " Mode Illumination")
        st.table(dfSolar)
        ax2= plt.figure(figsize=(3,15),dpi=300)
        plt.imshow(DfSolarfin.astype(int))
        plt.xticks([])
        plt.yticks([])
        st.pyplot(ax2)
