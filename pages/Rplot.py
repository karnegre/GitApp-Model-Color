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
import rmodel as rm
from plotly import express as px
import base64
import color
import CleanData as clean
from os.path import exists
import FunctionLib as funk
import SessionState

from streamlit import caching
st.legacy_caching.clear_cache()

number_of_elements =0
CompDict={}
CompNameList=[]
SpecDF= pd.DataFrame()
dfRLib= pd.DataFrame()

#Platform independence
cwd =os.getcwd()
cleanIR_path= os.path.join( cwd,'cleaningcode','cleaned','R')
IR_path_dirty= os.path.join( cwd,'cleaningcode','dirty','R')
session_state = SessionState.get(SpectraDict = [],CurrentSpectraIndex=0,Num_Spectra_Prev=0,OC_select=[],restart=0,IR_select=[])
# ------------------------------------------------------
def app():
    global IRfiles_selected
    #session_state.IR_select=[]
    if (st.sidebar.button("Restart RS Modeling")):
        session_state.restart=1
        session_state.IR_select=[]
        session_state.Num_Spectra_Prev=0
        session_state.CurrentSpectraIndex=0
        session_state.SpectraDict=[]
        session_state.GrainDict=[]
        IRfiles_selected =[]
        number_of_elements=0
        st.balloons()
    funk.NewFileCheck(IR_path_dirty, ModelType='IR')
    CompNameList,CompDict=funk.create_dictionary(cleanIR_path, ModelType='IR')
    process_sidebar()
# ---------------------------------------------------------
def process_sidebar():

        global number_of_elements
        global IRfiles_selected
        global CompNameList
        global CompDict
        global SpecDF
        global grainarray

        IRList=[]
        concarray=[]
        number_conc=0

        st.sidebar.title('Reflectance Modeling')

#----------------------ITEM 1: Select desired compounds---------------------------------------
        st.sidebar.header('Select Compounds')
        IRfile_list = CompNameList

        Group_list = ['Ice','Organic','Oceanic','Tholin','Higher Order Organic']
        Group_selected = st.sidebar.selectbox(label="Grouping",options=Group_list)

        cwd =os.getcwd()
        filename = "Lib.xlsx"
        path_file = os.sep.join([cwd, filename])
        Lib=pd.read_excel(path_file,sheet_name="R Library")

        GroupLib=Lib[Lib.Grouping.str.match(Group_selected)]
        IRfile_list = GroupLib['Compound'].tolist()
        IRfiles_selected = st.sidebar.multiselect(label="Compounds",options=IRfile_list)

        number_ir = len(IRfiles_selected)
        number_ir_statelist = len(session_state.IR_select)

        if (len(IRfiles_selected)>=1):
            for index in range(number_ir):
                if (number_ir_statelist>0):
                        if not (IRfiles_selected[index] in session_state.IR_select):
                            session_state.IR_select.append(IRfiles_selected[index])
                else:
                    if (session_state.restart==0):
                        session_state.IR_select.append(IRfiles_selected[index])

        if (session_state.restart==1):
            session_state.restart=0

        number_of_elements = len(session_state.IR_select)
        #st.write(number_of_elements)
        #To limit the amount of elements to 5. If user selects more than 5, its truncate to 5
        if (number_of_elements>5):
            number_of_elements=5

        if (number_of_elements==0):
            session_state.Num_Spectra_Prev=0
            session_state.CurrentSpectraIndex=0
            session_state.SpectraDict=[]
            session_state.GrainDict=[]

        funk.ReadLib(number_of_elements, ModelType='IR')
        # ReadIRLib()

        if (number_of_elements==1):
            IR_conc=100
            concarray.append(IR_conc)
            index=[session_state.IR_select[i] for i in range(number_of_elements)]

            dfComp=pd.DataFrame(concarray,index=index, columns=['Concentration'])
            st.header('Model Spectrum Parameters')
            st.table(dfComp)

            if (number_of_elements>=1 ):
                    if (st.sidebar.button("Start Calculation")):
                        funk.StartCalculation(IRfiles_selected,concarray, number_of_elements, S=None, p=None)

        elif (number_of_elements>=2):
#-----------------------ITEM 2: Select concentration--------------------------------------
            st.sidebar.subheader('Select Concentration')
            for index in range(number_of_elements):
                #st.write(index)
                number_conc = len(concarray)
                if (number_conc==0): #first slider - always 1 to 100
                    IR_conc= st.sidebar.slider(
                    "[%] for:" + session_state.IR_select[index] , 0, 100,step=10)
                else:
                    if  (number_conc< number_of_elements-1):
                        Sum_conc=0
                        for i in range(number_conc):
                            Sum_conc=Sum_conc+concarray[i]
                        if (Sum_conc>100): Sum_conc=100

                        IR_conc= st.sidebar.slider(
                        "[%] for:" + session_state.IR_select[index] , 0, 100-Sum_conc,value=0,step=10)
                    else:
                        Sum_conc=0
                        for i in range(number_conc):
                            if (Sum_conc>100): Sum_conc=100
                            Sum_conc=Sum_conc+concarray[i]

                        IR_conc=100-Sum_conc
                        st.sidebar.write("[%] for:"+ session_state.IR_select[index] + ": "+str(IR_conc)+ "%")

                concarray.append(IR_conc)
# -----   TABLE FOR USER TO MONITOR SPECTRA INPUT FOR DESIRED OC CONSTANTS --------THINK ABOUT THIS

            index=[session_state.IR_select[i] for i in range(number_of_elements)]

            dfComp=pd.DataFrame(concarray,index=index, columns=['Concentration'])

            st.header('Model Spectrum Parameters')
            st.table(dfComp)

            if (number_of_elements>=1 ):
                    if (st.sidebar.button("Start Calculation")):
                        funk.StartCalculation(session_state.IR_select, concarray, number_of_elements, S=None, p=None)
