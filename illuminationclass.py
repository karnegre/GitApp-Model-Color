import pandas as pd
import numpy as np
import os
import streamlit as st
cwd =os.getcwd()

#could also be photon source..think it again
class illumination:
	# create insolation class tht allows you to select mode
        # modes: Day (just DISR, LEDS off), Night (all LEDs on), Day+ (DISR + LEDS on)
        # add modes for just select LEDS (?)
        def __init__(self,mode):
            self.numberofLEDs={'band1':8,'band2':12,'band3':16,'band4':20,'band5':12,'band6':20,'band7':20,'band8':20,'band9':20}

            DISR= pd.read_csv(os.sep.join([cwd, 'color', 'DISRspectrumUniformWavelegnths.csv']),sep=',',names=['wave_nm','flux'], skiprows=1)
            LED= pd.read_csv(os.sep.join([cwd, 'color', 'LEDspectraUniformWavelegnths.csv']),sep=',',names=['wave_nm','band1','band2','band3','band4','band5','band6','band7','band8','band9'],skiprows=1)
            self.RQE= pd.read_csv(os.sep.join([cwd, 'color', 'RQEUniformWavelegnths.csv']),sep=',',names=['wave_nm','QE'], skiprows=1)
            self.GQE= pd.read_csv(os.sep.join([cwd, 'color', 'GQEUniformWavelegnths.csv']),sep=',',names=['wave_nm','QE'], skiprows=1)
            self.BQE= pd.read_csv(os.sep.join([cwd, 'color', 'BQEUniformWavelegnths.csv']),sep=',',names=['wave_nm','QE'], skiprows=1)

            # st.write(LED)
            ## SMACK: multiply each band spectrum by the corresponding number of LEDs
            for c in LED.columns[1:]:
                # st.write(LED[c])
                LED[c]=LED[c].multiply(self.numberofLEDs[c])
            # st.write(LED)
            #SM
            if mode=='Day':
                self.mode=mode
                self.fluxspectrum=DISR
                self.description="This mode uses the DISR spectrum as illumination mode to replicate day-time observation conditions"

            if mode=='Night':
                self.mode=mode
                # st.write(LED)
                # st.write(pd.DataFrame({'wave_nm':LED.wave_nm,'flux':LED.iloc[:,1:].sum(axis=1)}))
                self.fluxspectrum= pd.DataFrame({'wave_nm':LED.wave_nm,'flux':LED.iloc[:,1:].sum(axis=1)})
                self.description="This mode activates all LED bands as the illumination mode to replicate night-time observation conditions"
                #Multiply by FWHM value--in folder

            if mode == 'Day+':
                self.mode= mode
                self.fluxspectrum= DISR.add(pd.DataFrame({'wave_nm':LED.wave_nm,'flux':LED.iloc[:,1:].sum(axis=1)}))
                self.description="This mode uses the DISR spectrum in conjunction with all activated LED bands as the illumination mode to replicate day-time observation conditions with LEDs"

            if mode == 'Single':
                self.mode=mode
                # st.write(LED)
                self.LED_bands= st.multiselect('Select your single LED band(s): ',['band1','band2','band3','band4','band5','band6','band7','band8','band9'])
                # st.write(LED_bands)
                self.fluxspectrum = pd.DataFrame({'wave_um':LED.wave_nm,'flux':LED[self.LED_bands].sum(axis=1)})
                self.description="This mode activates user-specific LED bands as the illumination mode to observe at discrete wavelengths"
