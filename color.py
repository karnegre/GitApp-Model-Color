import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
from plotly import express as px
import os
import os.path
import streamlit as st



    # -----------------------Function Library--------------------------------------
def make_sim_im(wavelengthlims,compounds, QE, insolation = None, normalizetowhite=True):
    # st.write(len(compounds.columns))
    # compounds.columns
    # imagearray=np.zeros((len(compounds.columns),1,3))
    global DISRinsolation
    imagearray=np.zeros([1,len(compounds.columns)-1,3])
    QE_r = QE[['wave_um','R']].copy()
    # st.write(QE_r)
    QE_g = QE[['wave_um','G']].copy()
    # st.write(QE_g)
    QE_b = QE[['wave_um','B']].copy()
    # st.write(QE_b)

    ##define R G B filters according to wavelength cutoff specified
    rfil=extendfilters(QE_r,wavelengthlims[0],wavelengthlims[1])
    gfil=extendfilters(QE_g,wavelengthlims[0],wavelengthlims[1])
    bfil=extendfilters(QE_b,wavelengthlims[0],wavelengthlims[1])

    #print(len(rfil),len(DISRinsolation_resampled))
    if normalizetowhite:
        normalizetowhite={'R':interp2waveandfilter(rfil,compounds['wave_um'],compounds['White'],insolation),
                          'G':interp2waveandfilter(gfil,compounds['wave_um'],compounds['White'],insolation),
                          'B':interp2waveandfilter(bfil,compounds['wave_um'],compounds['White'],insolation)}
    else:
        normalizetowhite={'R':1,'G':1,'B':1}

    compounds.insert(0, 'wave_um', compounds.pop('wave_um'))
    # st.write(normalizetowhite)
    for i,c in enumerate(compounds.columns[1:]):

        imagearray[0,i,0]=interp2waveandfilter(rfil,compounds['wave_um'],compounds[c],insolation)/normalizetowhite['R']
        imagearray[0,i,1]=interp2waveandfilter(gfil,compounds['wave_um'],compounds[c],insolation)/normalizetowhite['G']
        imagearray[0,i,2]=interp2waveandfilter(bfil,compounds['wave_um'],compounds[c],insolation)/normalizetowhite['B']

    return imagearray

def extendfilters(df,shortlim,longlim):
    # since cutoffs won't be perfectly "hard", we do a linear drop off over 20 nm from the target cutoff
    cutoffwindow=20
    # st.write(df)
    df.rename(columns={ df.columns[1]: 'QE'}, inplace= True )
    # st.write(df)
    df['wave_um'] = df['wave_um'].multiply(1000)
    # st.write(df)

    #check in case wavelengths were given in the opposite expected order
    if shortlim>longlim:
        s=longlim
        l=shortlim
        shortlim=s
        longlim=l

     # finding the slopes (m) and y intercepts (b) of a linear extrapolation of the QE
    cropped=df[(df.wave_um>=(shortlim-cutoffwindow))&(df.wave_um<=(longlim+cutoffwindow))]
    cropped=cropped.set_index('wave_um')
    # st.write(cropped)

    shortm=cropped.at[shortlim,'QE'] / (cutoffwindow)
    shortb=cropped.at[shortlim,'QE']  -shortm*(shortlim)

    longm=cropped.at[longlim,'QE']  / (-1*cutoffwindow)
    longb=cropped.at[longlim,'QE'] -longm*longlim

    cropped['QE']=[w*shortm+shortb if w < shortlim else q for w,q in zip(cropped.index,cropped.QE) ]
    cropped['QE']=[w*longm+longb if w > longlim else q for w,q in zip(cropped.index,cropped.QE) ]
    cropped['wave_um']=[w/1000 for w in cropped.index]
    # st.write(cropped)

    return cropped

def interp2waveandfilter(filterdf,spec_wave_um,spec_refl,insolation=None):
    # resample spectrum/filter to the same wavelengths
    I=0
    QE=0

    if filterdf['wave_um'].equals(spec_wave_um):
        QE=filterdf.QE
    else :
        QE=np.interp(spec_wave_um,filterdf.wave_um,filterdf.QE,left=0,right=0)
#         plt.plot(spec_wave_um,QE)
#         plt.plot(spec_wave_um,spec_refl)


    if insolation==None:
        ## uniform illumination, approximation of full spectrum LED with infinite integration time
        I=np.ones_like(spec_wave_um) #1W/m2/sr/wavelength
    elif insolation == 'phot':
        h=6.626e-34
        c=2.988e-8
        I=[1/(h*c)/w for w in spec_wave_um] # photons/s/m2/sr
    elif (insolation == 'Sun') or (insolation == 'solar'):
        ## DISR recorded illumination at surface, W/m2/sr/wavelength
        I=np.interp(spec_wave_um,DISRinsolation.wave_um,DISRinsolation.flux)
        #plt.plot(spec_wave_um,I,'k--')
        #plt.plot(DISRinsolation.wave_um,DISRinsolation.flux,c='k')
   # elif (insolation == 'LEDs') or (insolation == 'leds'):


    else:
        print('Insolation not implemented.')

    channelresponse=spec_refl*I*QE

    return sum(channelresponse)
# -------------------------------Main-----------------------------------------
def imaging(compound):
    global DISRinsolation
    interpwaves=np.arange(400,1100,5) #increments of 5 nm
    interpwaves_um=interpwaves/1000
    caseA=[540,960]

    cwd =os.getcwd()
    filename_DISR = "DISRillumination.csv"
    path_file_DISR = os.sep.join([cwd,'color', filename_DISR])

    filename_QE_NC = "QE_nocutoffs.csv"
    path_file_QE_NC = os.sep.join([cwd, 'color', filename_QE_NC])

    DISRinsolation=pd.read_csv(path_file_DISR,names=['wave_um','flux'],skiprows=1)
    QE_NC=pd.read_csv(path_file_QE_NC)

    compound['wave_um']=compound.index
    compound['White']=np.ones_like(compound.index)
    compound['Dark']=np.ones_like(compound.index)*0.01
    # st.write(compound)

    solar_norm=make_sim_im(caseA,compound, QE_NC, insolation='solar')
    solar=make_sim_im(caseA,compound, QE_NC, insolation='solar',normalizetowhite=False)
    # a = np.copy(solar_norm)
    # ind = np.lexsort((a[:,:,1],a[:,:,0]))
    # st.write(a[ind])

    st.write(solar_norm)
    st.write(solar)
    compound.pop('wave_um')

    st.header("Simulated Titan Imaging with Bayer Filters")
    dfSolarN = pd.DataFrame(np.row_stack(solar_norm),index=compound.columns, columns =['R','G','B'])
    dfSolar = pd.DataFrame(np.row_stack(solar),index=compound.columns, columns =['R','G','B'])

    dfSolarNAs= dfSolarN.sort_values(["R","G","B"], ascending=True)
    dfSolarAs= dfSolar.sort_values(["R","G","B"], ascending=True)
    st.write(dfSolarAs)
    row=len(dfSolarAs)
    DfSolarNfin= dfSolarNAs.to_numpy().reshape((1,row,3))
    DfSolarfin= dfSolarAs.to_numpy().reshape((1,row,3))


    st.subheader("RGB Values")
    st.caption("DISR Illumination (Normalized to White)")
    st.table(dfSolarNAs)
    st.caption("DISR Illumination")
    st.table(dfSolarAs)


    st.subheader("540-960 nm Bandpass")
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(6,6))
    ax1.imshow(DfSolarNfin)
    ax1.set_xticks(ticks=np.arange(0,len(compound.columns)))
    ax1.set_xticklabels(dfSolarNAs.index, Fontsize=5)
    ax1.autoscale(enable=True, axis='x')
    ax1.axes.yaxis.set_visible(False)
    # ax1.set_xticklabels(caseA[1])
    # plt.colorbar(ax1)
    ax1.set_title('DISR Illumination (Normalized to White)',fontsize=5)
    ax2.imshow(DfSolarfin.astype(int))
    ax2.set_xticks(ticks=np.arange(0,len(compound.columns)))
    ax2.set_xticklabels(dfSolarAs.index, Fontsize=5)
    ax2.axes.yaxis.set_visible(False)
    # ax2.set_yticks(ticks=np.arange(0,1))
    # ax2.set_xticklabels((case1[1],case2[1],case3[1],case4[1]))
    ax2.set_title('DISR Illumination',fontsize=5)

    st.pyplot(fig)
