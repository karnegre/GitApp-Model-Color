#****IMPORTS***
import streamlit as st
import pandas as pd
import numpy as np
import time
from PIL import Image
import os
import os.path
import cmath
import math
import shkuratov_ssa_models as shkrtv
from plotly import express as px
import base64
import color
import CleanData as clean
from os.path import exists
from csv import writer
from datetime import datetime
import FunctionLib as funk

from streamlit import caching
st.legacy_caching.clear_cache()

number_of_elements =0
CompDict={}
CompNameList=[]
SpecDF= pd.DataFrame()
dfLib= pd.DataFrame()
q=0.50;

#Platform independence
cwd =os.getcwd()
OCfiles_path= os.path.join( cwd,'cleaningcode','cleaned','OC')
OCfiles_path_dirty= os.path.join( cwd,'cleaningcode','dirty','OC')

session_state = SessionState.get(SpectraDict = [],CurrentSpectraIndex=0,Num_Spectra_Prev=0,OC_select=[],restart=0,IR_select=[])
# -----------------------------------------MAIN------------------------------------------------
def app():
    global OCfiles_selected
    global CompNameList
    global CompDict
    if (st.sidebar.button("Restart OC Modeling")):
        session_state.restart=1
        session_state.OC_select=[]
        session_state.Num_Spectra_Prev=0
        session_state.CurrentSpectraIndex=0
        session_state.SpectraDict=[]
        session_state.GrainDict=[]
        OCfiles_selected =[]
        number_of_elements=0
        st.balloons()
    funk.NewFileCheck(OCfiles_path_dirty, ModelType='OC')
    CompNameList,CompDict=funk.create_dictionary(OCfiles_path, ModelType='OC')
    process_sidebar()
# ----------------------------------------
def process_sidebar():

        global number_of_elements
        global OCfiles_selected
        global CompNameList
        global CompDict
        global SpecDF
        global grainarray
        global OC_grainsize_selected
        global dfComp

        OCList=[]

        st.sidebar.title('Optical Constants Modeling')

#----------------------ITEM 1: Select desired compounds---------------------------------------
        st.sidebar.header('Select Compounds')
        OCfile_list = CompNameList
        Group_list = ['Ice','Organic','Oceanic','Tholin','Higher Order Organic']
        Group_selected = st.sidebar.selectbox(label="Grouping",options=Group_list)

        cwd =os.getcwd()
        filename = "Lib.xlsx"
        path_file = os.sep.join([cwd, filename])
        Lib=pd.read_excel(path_file,sheet_name="O Library")

        GroupLib=Lib[Lib.Grouping.str.fullmatch(Group_selected)]
        OCfile_list = GroupLib['Compound'].tolist()
        OCfiles_selected = st.sidebar.multiselect(label="Compounds",options=OCfile_list)
        number_oc = len(OCfiles_selected)
        number_oc_statelist = len(session_state.OC_select)

        if (len(OCfiles_selected)>=1):
            for index in range(number_oc):
                if (number_oc_statelist>0):
                        if not (OCfiles_selected[index] in session_state.OC_select):
                            session_state.OC_select.append(OCfiles_selected[index])
                else:
                    if (session_state.restart==0):
                        session_state.OC_select.append(OCfiles_selected[index])

        if (session_state.restart==1):
            session_state.restart=0
        number_of_elements = len(session_state.OC_select)

        if (number_of_elements>5):
            number_of_elements=5

        if (number_of_elements==0):
            session_state.Num_Spectra_Prev=0
            session_state.CurrentSpectraIndex=0
            session_state.SpectraDict=[]
            session_state.GrainDict=[]

        funk.ReadLib(number_of_elements, ModelType='OC')
        if (number_of_elements==1):
            st.sidebar.header("Modeling Pure Spectra")
            st.sidebar.caption("Concentration for " + str(session_state.OC_select[0]) + " is set to 100%")
            OC_conc=100

            st.sidebar.subheader('Select Grain Sizes (μm)')
            OC_grainsize_selected= st.sidebar.number_input("Grain size for " + session_state.OC_select[0],min_value=10, max_value=500,step= 1, help= "Must be between 10-500 μm")

            if (number_of_elements>=1 ):
                if (st.sidebar.button("Start Calculation")):
                    funk.StartCalculation(session_state.OC_select, OC_conc, number_of_elements, OC_grainsize_selected,q)

        elif (number_of_elements>1):
#-----------------------ITEM 2: Select # of spectra--------------------------------------
            st.sidebar.header('Select Number of Spectra')
            Num_Spectra= st.sidebar.number_input(
            "# of Spectra" ,min_value=1, max_value=5,step= 1, help= "Max is 5 spectra")

            if (session_state.Num_Spectra_Prev>Num_Spectra):
                session_state.SpectraDict.pop()

            session_state.Num_Spectra_Prev=Num_Spectra
            arr=[]
            len1=len(session_state.SpectraDict)

            if (len1<Num_Spectra):
                for index in range(Num_Spectra):
                    if ((len1==0) or (index>=len1)):
                        for idx in range(number_of_elements):
                            if (idx<(number_of_elements-1)):
                                arr.append(0)
                            else:
                                arr.append(100)
                        session_state.SpectraDict.append(arr)

    #---------------------------ITEM 3: Select Spectrum to edit----------------------------------
            st.sidebar.header('Select Spectrum to edit')
            SpecPick = st.sidebar.selectbox('Which Spectrum?', [(i+1) for i in range(Num_Spectra)],index=session_state.CurrentSpectraIndex)
            SpecPick =SpecPick-1
            session_state.CurrentSpectraIndex=SpecPick

            concarray=[]
            number_conc=0

#---------------------ITEM 3A: GRAINSIZE----------------------------------------
            st.sidebar.subheader('Select Grain Sizes (μm)')
            grainarray=[]
            for i in range(number_of_elements):
                OC_grainsize_selected= st.sidebar.number_input(
                "Grain size for " + session_state.OC_select[i],min_value=10, max_value=500,step= 1, help= "Must be between 10-500 μm")
                grainarray.append(OC_grainsize_selected)

#---------------------ITEM 3B: CONCENTRATION----------------------------------------
            st.sidebar.subheader('Select Concentration')
            for index in range(number_of_elements):
                number_conc = len(concarray)
                if (number_conc==0): #first slider - always 1 to 100
                    OC_conc= st.sidebar.slider(
                    "Concentration [%] for " + session_state.OC_select[index] , 0, 100,step=10)
                else:
                    if  (number_conc< number_of_elements-1):
                        Sum_conc=0
                        for i in range(number_conc):
                            Sum_conc=Sum_conc+concarray[i]
                        if (Sum_conc>100): Sum_conc=100

                        OC_conc= st.sidebar.slider(
                        "Concentration [%] for " + session_state.OC_select[index] , 0, 100-Sum_conc,value=0,step=10)
                    else:
                        Sum_conc=0
                        for i in range(number_conc):
                            if (Sum_conc>100): Sum_conc=100
                            Sum_conc=Sum_conc+concarray[i]

                        OC_conc=100-Sum_conc
                        st.sidebar.write("Concentration for "+ session_state.OC_select[index] + " is "+str(OC_conc)+ "%")

                concarray.append(OC_conc)
            session_state.SpectraDict[SpecPick]=concarray
            # st.write(session_state.SpectraDict[SpecPick])
# -----   TABLE FOR USER TO MONITOR SPECTRA INPUT FOR DESIRED OC CONSTANTS --------
            indexname= ["Spectrum #"+str(i+1) for i in range(Num_Spectra)]
            colname=[session_state.OC_select[i] for i in range(number_of_elements)]

            dfComp=pd.DataFrame(session_state.SpectraDict,columns=colname, index=indexname)
            dfGrain=pd.DataFrame(grainarray,index=colname,columns=["Grain size (μm)"])
            st.header("Spectrum Model Parameters")

            col1, col2 = st.columns((1,1))

            with col1:
                st.subheader("Grain Size Table")
                st.caption('Constant for all spectrum')
                st.table(dfGrain)

            with col2:
                st.subheader("Compound Concentration Table")
                st.caption('Compound Concentrations for each Spectrum')
                st.table(dfComp)

            if (number_of_elements>=1 ):
                    if (st.sidebar.button("Start Calculation")):
                        funk.StartCalculation(session_state.OC_select,session_state.SpectraDict, number_of_elements, grainarray,q)
