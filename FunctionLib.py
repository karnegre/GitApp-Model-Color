#****IMPORTS***
import streamlit as st
import pandas as pd
import numpy as np
import time
from PIL import Image
import SessionState
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
from csv import writer
from datetime import datetime
import FunctionLib as funk

from streamlit import caching
st.legacy_caching.clear_cache()

CompDict={}
CompNameList=[]

session_state = SessionState.get(SpectraDict = [],CurrentSpectraIndex=0,Num_Spectra_Prev=0,OC_select=[],restart=0,IR_select=[])

def NewFileCheck(pathdirty, ModelType):
#This function is for verifying if 'dirty' data files (Optical constant or reflectance) exist in respective paths
#If 'dirty' files exist, the user must opt to clean.
#Cleaning is executed in Cleandata.py
    if os.path.exists(pathdirty):
        if len(os.listdir(pathdirty)) != 0:
            if st.button("Dirty files detected, click here to clean"):
                if ModelType == 'OC':
                    clean.CleanOC()
                    st.write("dirty files should no longer be in the same directory--should be cleaned and in OC clean folder")
                elif ModelType == 'IR':
                    clean.CleanIR()
                    st.write("dirty files should no longer be in the same directory--should be cleaned and in R clean folder")

@st.cache(suppress_st_warning=True)
def create_dictionary(path, ModelType):
#This function returns 2 values:
    #(1) CompNameList is a list of all the compound names from the cleaned file directory
    #(2) CompDict is a dictionary of compound dataframes
        # Each compound name has a df (index=wave) with either:
            # OC: 'wave', 'n', 'k', and 'N' columns
            # or IR: 'wave', 'r'
    global CompNameList
    global CompDict
    # @st.cache(allow_output_mutation=True)

    for name in os.listdir(path):
        if os.path.isfile(os.path.join(path, name)):
            if name.endswith(".txt"):
                namef= os.path.splitext(name)[0]
                CompNameList.append(namef)
                df = pd.read_csv(os.path.join(path,name))
                df.set_index(['wave'],drop=False,inplace=True)
                if ModelType == 'OC':
                    df['N']=[complex(n,k) for n,k in zip(df.n,df.k)]
                CompDict[namef]=df
    return CompNameList, CompDict

def ReadLib(number_of_elements, ModelType):
# This function creates the table first propagated after compounds are selected for each model type
# Tabled information for each compound is parsed from the Lib.xlsx excel by name and appended to a df called lib

    global dfLib
    global dfRLib
    global lib
    # global number_of_elements

    if (number_of_elements==0):
        return

    cwd =os.getcwd()
    filename = "Lib.xlsx"
    path_file = os.sep.join([cwd, filename])

    if ModelType == 'OC':
        dfLib=pd.read_excel(path_file,sheet_name="O Library")
        lib=pd.DataFrame()
        st.header('Compound Information Table')

        for i in range(number_of_elements):
            data=pd.DataFrame(dfLib[dfLib['Compound'].str.fullmatch(session_state.OC_select[i])])
            lib=lib.append(data,ignore_index=True)
        st.dataframe(lib)
    elif ModelType == 'IR':
        dfRLib=pd.read_excel(path_file,sheet_name="R Library")
        lib=pd.DataFrame()
        st.header('Compound Information Table')

        for i in range(number_of_elements):
            data=pd.DataFrame(dfRLib[dfRLib['Compound'].str.fullmatch(session_state.IR_select[i])])
            lib=lib.append(data,ignore_index=True)
        st.dataframe(lib)

def create_df_formixing(mix, number_of_elements,ss, check):
# This function returns a massive list where each index is a wavelength and
# for that wavelength there are n (n=1..5) number of compound's complex numbers or reflectance values
    #  OC example:
        # 0:[
            # 0:"(1.3194+2.3700000000000003e-11j)"
            # 1:"(1.4603039223518135+1.5715129843794172e-05j)"
        #   ]
    if (number_of_elements==1):
        if check == True:
            thismix=list(CompDict[ss[0]].N)
        else:
            thismix = mix
            thismix.drop(['wave'], axis=1, inplace=True)
    elif (number_of_elements==2):
            thismix=[[a,b] for a,b in zip(mix[ss[0]],mix[ss[1]])]
    elif (number_of_elements==3):
            thismix=[[a,b,c] for a,b,c in zip(mix[ss[0]],mix[ss[1]],mix[ss[2]])]
    elif (number_of_elements==4):
            thismix=[[a,b,c,d] for a,b,c,d in zip(mix[ss[0]],mix[ss[1]],mix[ss[2]],mix[ss[3]])]
    elif (number_of_elements==5):
            thismix=[[a,b,c,d,e] for a,b,c,d,e in zip(mix[ss[0]],mix[ss[1]],mix[ss[i+2]],mix[ss[3]],mix[Comp[4]])]
    else:
        thismix=[]

    return thismix

def writefilewithheader(lib,spectrumdf,s,c):
# This function appends the lib dataframe constructed in the ReadLib() function to create a metadata string variable
# The metadata string variable is appended to the header of the csv file that the user can optionally downnload in StartCalculation() function
    if s != None:
        if type(c) is list:
            c=[i*100 for i in c]
        else:
            c=c*100

        lib=lib.drop(columns=['Grouping'])
        lib.insert(2, 'Grainsize (micron)', value= s)
        lib.insert(3, 'Concentration (%)', value= c)
        metadata= 'Model: , Shkurtov mixing model of optical constants\n'
        metadata+='Timestamp: ,'+str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')) + '\n'
        metadata+= lib.to_csv(index=True, sep=',')
        csv=metadata+ '\n'+ spectrumdf.to_csv(index=True)
    else:
        lib=lib.drop(columns=['Grouping'])
        lib.insert(2, 'Concentration (%)', value= c)
        metadata= 'Model: , Areal mixture of reflectance\n'
        metadata+='Timestamp: ,'+str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')) + '\n'
        metadata+= lib.to_csv(index=True, sep=',')
        csv=metadata+ '\n'+ spectrumdf.to_csv(index=True)
    return csv

def StartCalculation(files,mixesArray,number_of_elements, S,p):
# This function produces the multi-composite reflectance spectra with df for VIS and VIS+IR- option to download spectra and dataset
 # Here Shkuratov and reflectance modeling is called and mixture data is returned
    global CompDict
    global lib
    i=0

    check = True
    if S == None:
        check = False

    mix=pd.DataFrame()

    for c in range(number_of_elements):
        if S != None:
            mix['wave']=CompDict[session_state.OC_select[0]].wave
            mix.set_index(mix.wave,inplace=True)
            dataname=[session_state.OC_select[i] for i in range(number_of_elements)]
            datanamecombo='-'.join(dataname)+ '-'+ str(S)+ 'micron'
            mix[session_state.OC_select[c]]=CompDict[session_state.OC_select[c]].N
            ss= session_state.OC_select
        else:
            mix['wave']=CompDict[session_state.IR_select[0]].wave
            mix.set_index(mix.wave,inplace=True)
            dataname=[session_state.IR_select[i] for i in range(number_of_elements)]
            datanamecombo='-'.join(dataname)
            mix[session_state.IR_select[c]]=CompDict[session_state.IR_select[c]].r
            ss= session_state.IR_select

    result=pd.DataFrame(index=mix.index)
    visresult=pd.DataFrame()
    thismix=create_df_formixing(mix,number_of_elements,ss, check)

    if (number_of_elements>=2):
        for m in mixesArray:
            # concentrations=[mm/100 for mm in m]
            colname=''
            colnamearray=[]

            if S != None:
                concentrations=[mm/100 for mm in m]
                for n,i in enumerate(session_state.OC_select):
                    # to limit the amount of compounds to 5 possible selections by the user
                    if(n<=4):
                        if (n==number_of_elements-1):
                            colname+=str(m[n])[0:3]
                        else:
                            colname+=str(m[n])[0:3]+"_"#[0:2]
                mix[colname]=[shkrtv.shkuratov_coarsemix(concentrations,a,p,S,w) for a,w in zip(thismix,mix.wave)]
                result[colname]=mix[colname]
                visresult[colname]=result[colname].copy().truncate(after=1.05)

            else:
                concentrations=[mm/100 for mm in mixesArray]
                for n,i in enumerate(session_state.IR_select):
                    if(n<=4):
                        if (n==number_of_elements-1):
                            colname+=str(mixesArray[n])[0:3]
                        else:
                            colname+=str(mixesArray[n])[0:3]+"_"#[0:2]

                mix[colname]=[rm.linearmixingmodel(concentrations,a,w) for a,w in zip(thismix,mix.wave)]
                result[colname]=mix[colname]

        if S == None:
            for i in range(number_of_elements):
                result[session_state.IR_select[i]]=CompDict[session_state.IR_select[i]].r
            visresult=result.copy().truncate(after=1.05)

    else:
        if S != None:
            concentrations=mixesArray/100
            colname=session_state.OC_select[0]
            mix[colname]=[shkrtv.shkuratov_coarsemix(concentrations,a,p,S,w) for a,w in zip(thismix,mix.wave)]
            result[colname]=mix[colname]
            visresult[colname]=result[colname].copy().truncate(after=1.05)
        else:
            concentrations=100
            result=thismix
            visresult=result.copy().truncate(after=1.05)

    fig1 = px.line(visresult)
    fig1.update_xaxes(title_text='Wavelength (μm)',fixedrange=True)
    fig1.update_yaxes(title_text='Reflectance')
    fig1.update_layout(legend_title_text='Concentrations')
    fig1.update_layout(showlegend=True, width=1100,height=700,margin= dict(l=1,r=1,b=1,t=1), font=dict(color='#383635', size=20))

    fig2 = px.line(result)
    fig2.update_xaxes(title_text='Wavelength (μm)',fixedrange=True)
    fig2.update_yaxes(title_text='Reflectance')
    fig2.update_layout(legend_title_text='Concentrations')
    fig2.update_layout(showlegend=True, width=1100,height=700,margin= dict(l=1,r=1,b=1,t=1), font=dict(color='#383635', size=20))

    col1, col2 = st.columns((1,1))
    with col1:
        st.header("Visible Spectra")
        st.plotly_chart(fig1, use_container_width=True)
        st.header("Visible Spectra Data")
        st.dataframe(visresult)
        csv= writefilewithheader(lib,visresult,S,concentrations)
        st.download_button(label="Download data as CSV",data=csv,file_name=datanamecombo +'.csv', mime='text/csv')

    with col2:
        st.header("Visible + IR Spectra")
        st.plotly_chart(fig2, use_container_width=True)
        st.header("Visible + IR Spectra Data")
        st.dataframe(result)
        csv2= writefilewithheader(lib,result,S,concentrations)
        st.download_button(label="Download data as CSV",data=csv2,file_name=datanamecombo +'.csv', mime='text/csv')
