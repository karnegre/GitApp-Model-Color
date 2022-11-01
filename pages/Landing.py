import streamlit as st
import numpy as np
import pandas as pd
from PIL import  Image
from IPython.display import HTML
import os

def app():

    display = Image.open('LandingLogo.png')
    display = np.array(display)

#LOGO Orientation-----------------------------
    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        st.write("")

    with col2:
        st.image(display, width=600)

    with col3:
        st.write("")

# #DESCRIPTION Orientation-----------------------------
    col4, col5, col6 = st.columns([2,10,3])

    with col4:
        st.write("")

    with col5:

        st.markdown(
        """
            _________________________________________________________________________________________________________________________________
            #### Welcome to The Dragonfly Surface Composition Modeling and Synthetic Color App!
             + This user-interface was created to support the New Frontiers mission to Titan, ands hosts features such as:
                + A database library filled with optical constant and reflectance data from literature of compounds antiicipated on Titan's surface.
                + Two modeling tools for creating multi-composite mixtures using optical constants [Shkuratov Model (1999)] and reflectance data, respectively.
                + A synthetic color generation tool for approximating what DragonCam might see multi-composite mixtures as at Titan's surface.
            ___________________________________________________________________________________________________________________________________________________________________________________________________
            """
            )
    with col6:
        st.write("")

#LIB Orientation-----------------------------
    col7, col8, col9 = st.columns([2,8,3])

    with col7:
        st.write("")

    with col8:

        st.header("Database Libraries")
        libpick = st.selectbox(
        "Select a Library",
        ('Optical Constant Library', 'Reflectance Spectra Library'))

        #Platform independence
        cwd =os.getcwd()

        filename = "Lib.xlsx"
        path_file = os.sep.join([cwd, filename])

        if libpick == 'Optical Constant Library':

            dfOLib=pd.read_excel(path_file,sheet_name="O Library").set_index("Compound")
            st.table(dfOLib)

        if libpick == 'Reflectance Spectra Library':

            dfRLib=pd.read_excel(path_file,sheet_name="R Library").set_index("Compound")
            st.table(dfRLib)

        else:
            st.write('')

    with col9:
        st.write("")
