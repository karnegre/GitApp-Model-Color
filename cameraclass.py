import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import streamlit as st

delta_wave_nm=5
interpwaves_nm= np.arange(350,1050,delta_wave_nm)

# class LED:
# 	Le = Ie / D^2 / pi *I/F_ground


class camera:
	# create camera class from precanned values
	def __init__(self,name):
		self.pixelarea=(4.8e-6)**2 #m^2
		self.fullwell=10000 #electrons
		self.opticstransmission=0.8 # total, window + lens
		self.detectorsize_npix=2048*2048
		self.bandpasslimits=[540,960] #nm
		# seconds, a default value
		self.gain = 15.6 #DN/e
		self.SNR = 50

		if name=='MAC':
			# Medium angle camera. formerly panorama
			self.name=name
			self.iFOV=380e-6 #r
			self.bandpasslimits=[540,960] #nm
			self.focallength = 12.6 #mm
			self.detectorsize_npix=2592*2048
			self.fno=7.4
			self.set_opticalthroughput() # m^2sr
			self.set_spectralthroughput() # unitless
			self.integrationtime_s=.01 #seconds

		if name=='WAC':
			# Wide angle camera; side looking, forward looking, downward looking
			self.name=name
			self.iFOV=828e-6 #rad
			self.bandpasslimits=[540,960] #nm
			self.focallength = 5.8 #mm
			self.fno=2.7
			self.set_opticalthroughput() # m^2sr
			self.set_spectralthroughput() # unitless
			self.integrationtime_s=0.001 #seconds

		if (name=='Micro') | (name=='Microscopic'):
			self.name=name
			self.iFOV=40e-6 #r
			self.bandpasslimits=[440,975] #nm
			self.focallength = 120.6 #mm
			self.fno=7.4
			self.set_opticalthroughput() # m^2sr
			self.set_spectralthroughput() # unitless
			self.integrationtime_s=.01 #seconds


	def set_opticalthroughput(self):
		self.opticalthroughput=np.pi*self.pixelarea/(4*self.fno**2)

	def set_spectralthroughput(self):
		# read in QE file: this is QE + Bayer transmission
		cwd =os.getcwd()
		QE_R=pd.read_csv(os.sep.join([cwd, 'color', 'QEBandPass_red.txt']),sep=',',names=['wave_nm','QE'])
		QE_G=pd.read_csv(os.sep.join([cwd, 'color', 'QEBandPass_green.txt']),sep=',',names=['wave_nm','QE'])
		QE_B=pd.read_csv(os.sep.join([cwd, 'color', 'QEBandPass_blue.txt']),sep=',',names=['wave_nm','QE'])

		# use bandpass limits to crop
		QE_R=extendfilters(QE_R,self.bandpasslimits[0],self.bandpasslimits[1])
		QE_G=extendfilters(QE_G,self.bandpasslimits[0],self.bandpasslimits[1])
		QE_B=extendfilters(QE_B,self.bandpasslimits[0],self.bandpasslimits[1])

		#setdetectorQE
		self.spectralthroughput_R=pd.DataFrame({'wave_um':QE_R.index,'throughput':QE_R.QE*self.opticstransmission})
		self.spectralthroughput_G=pd.DataFrame({'wave_um':QE_G.index,'throughput':QE_G.QE*self.opticstransmission})
		self.spectralthroughput_B=pd.DataFrame({'wave_um':QE_B.index,'throughput':QE_B.QE*self.opticstransmission})



	# create camera class by defining values

def extendfilters(df,shortlim,longlim,cutoffwindow_nm=20):
		  # since cutoffs won't be perfectly "hard", we do a linear drop off over 20 nm from the target cutoff
	if df.columns[1] != 'QE':
		st.write('Uhoh. Did you feed in the right data frame to the extendfilters function?')
		exit()

	# check in case wavelengths were given in the opposite expected order
	if shortlim>longlim:
		s=longlim
		l=shortlim
		shortlim=s
		longlim=l

    # cropping
	cropped=pd.DataFrame({'wave_nm':interpwaves_nm,'QE':np.interp(interpwaves_nm,df.wave_nm,df.QE,left=0,right=0)})
	cropped=cropped.set_index('wave_nm')
	cropped=cropped.loc[(shortlim-cutoffwindow_nm):(longlim+cutoffwindow_nm)]

	# finding the slopes (m) and y intercepts (b) of a linear extrapolation of the QE
	shortm=(cropped.at[shortlim,'QE'] )/ (cutoffwindow_nm)
	shortb=cropped.at[shortlim,'QE']  -shortm*(shortlim)
	#
	# st.write(longlim)
	# st.write(cropped)

	longm=cropped.at[longlim,'QE']  / (-1*cutoffwindow_nm)
	longb=cropped.at[longlim,'QE'] -longm*longlim

	cropped['QE']=[w*shortm+shortb if w < shortlim else q for w,q in zip(cropped.index,cropped.QE) ]
	cropped['QE']=[w*longm+longb if w > longlim else q for w,q in zip(cropped.index,cropped.QE) ]

	return cropped


def pixelobserve(insolation,surfrefl,camera,integrationtime_s,noise=None):
	# insolation == dataframe with wavelength, W/m2/sr/um
	#				assumed column names: wave_nm, flux
	# surfrefl == unitless, dataframe with wavelength + reflectance
	#			  assumed column names: wave_nm, refl
	# camera: see object above


	if integrationtime_s ==None:
		integrationtime_s=camera.integrationtime_s

    ## make sure wavelengths are equivalent across arrays: insolation, surfrefl relative to camera spectral throughput (QE)
	if insolation.fluxspectrum.wave_nm.equals(interpwaves_nm) is False:
		insolation=pd.DataFrame({'wave_nm':interpwaves_nm,'flux':np.interp(interpwaves_nm,insolation.fluxspectrum.wave_nm,insolation.fluxspectrum.flux,left=0,right=0)},index=interpwaves_nm)
		insolation=insolation.loc[camera.spectralthroughput_R.index.min():camera.spectralthroughput_R.index.max()]

	if surfrefl.wave_nm.equals(interpwaves_nm) is False:
		surfrefl=pd.DataFrame({'wave_nm':interpwaves_nm,'refl':np.interp(interpwaves_nm,surfrefl.wave_nm,surfrefl.refl,left=0,right=0)},index=interpwaves_nm)
		surfrefl=surfrefl.loc[camera.spectralthroughput_R.index.min():camera.spectralthroughput_R.index.max()]

	### Insolation
	#Convert insolation to phots/s ## must be done after normalizing all the wavelengths
	h=6.626e-34 # plank's const
	c=2.988e8  # speed of light m/s
	insolation['flux']=[i/(h*c)/(w*1000) for w,i in zip(insolation.wave_nm,insolation.flux) ] #(photons/s/m2/sr/um)
	# DISR IS IN /um FYI so we need to convert w to micron
	### now taht we ar e operating in nm, we need anohter factor of 10^3 in the above


	Red = np.trapz(insolation.flux*surfrefl.refl*camera.spectralthroughput_R.throughput,x=insolation.wave_nm/1000)
	Green = np.trapz(insolation.flux*surfrefl.refl*camera.spectralthroughput_G.throughput,x=insolation.wave_nm/1000)
	Blue = np.trapz(insolation.flux*surfrefl.refl*camera.spectralthroughput_B.throughput,x=insolation.wave_nm/1000)

	pixel = np.array([Red,Green,Blue])*camera.opticalthroughput/camera.gain*integrationtime_s
	return np.array(pixel,ndmin=2)

def observemultiplematerials(insolation,materialsdf,camera,integrationtime_s=None):
	## materialsdf = dataframe with reflectances, pref in nanometers
	## insolation == dataframe with wavelength, W/m2/sr/um
	##				assumed column names: wave_nm, flux
	## surfrefl == unitless, dataframe with wavelength + reflectance
	#			  assumed column names: wave_nm, refl
	## camera ==  see object above

	st.write(materialsdf)
	if 'wave_nm' not in materialsdf.columns:
		print('Modifying the wavelength of refl to match insolutation')
		if 'wave' in materialsdf.columns:
			materialsdf['wave_nm']=materialsdf.wave*1000
			materialsdf.pop('wave')
		if 'wave_um' in materialsdf.columns:
			materialsdf['wave_nm']=materialsdf.wave_um*1000
			materialsdf.pop('wave_um')

		materialsdf = materialsdf.reindex(np.insert(materialsdf.columns[:-1].values,0,'wave_nm'), axis=1)

	materialsdf['White']=np.ones_like(materialsdf.wave_nm)
	materialsdf['Dark']=np.ones_like(materialsdf.wave_nm)*0.01

	caltargetimage=pixelobserve(insolation,materialsdf[['wave_nm','White']].rename(columns={'White':'refl'}) ,camera,integrationtime_s)

	imagearray=np.zeros([1,len(materialsdf.columns)-1,3])
	calimagearray=np.zeros_like(imagearray)

	for i,c in enumerate(materialsdf.columns[1:]):
		#code in something here to check first column of df is wavelnthg
		#remember that pixelobserve expects the surface reflectance column to be called "refl"
		thismaterial=materialsdf[['wave_nm',c]].rename(columns={c:'refl'})
		imagearray[0,i]=pixelobserve(insolation,thismaterial,camera,integrationtime_s)
		print(c,imagearray[0,i])
		calimagearray[0,i]=imagearray[0,i]/caltargetimage
		#print(c,calimagearray[0,i])


	return imagearray,calimagearray


# def observewithmultiplelightsources(materialsdf,insolationdf,camera,integration=None):
# 	## materialsdf = dataframe with reflectances, pref in nanometers
# 	## insolation == dataframe with wavelength, W/m2/sr/um
# 	##				assumed column names: wave_nm, flux
# 	## surfrefl == unitless, dataframe with wavelength + reflectance
# 	#			  assumed column names: wave_nm, refl
# 	## camera ==  see object above

# 	for i,lights in enumerate(insolationdf.columns[1:]):
# 		observemutliplematerials(materialsdf,insolationdf['wave_nm',lights],camera,integration)

# 		# how do we want to return these data?
