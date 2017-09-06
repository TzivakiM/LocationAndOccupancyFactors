# deposited nuclides
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np 
import os
import sys
import csv
from cycler import cycler


#Plot settings for black and white. If color is wanted, comment out!
#monochrome = (cycler('color', ['k']) * cycler('marker', ['', '.']) *
#                     cycler('linestyle', ['-', '--', ':', '-.']))

#plt.rc('axes', prop_cycle=monochrome)
mark_step_num=0.1

def main(nuclide,T,timestep,graphoption,totdosetimeoption,doseratetimeoption):
#def main(nuclide,T,timestep,graphoption):
	#define variables:
	#the conversion factors from Petoussi-Henss for radionuclides detected as ground contamination after the Fukushima accident
	#[adult, child, child4-7, infant]
	e_dotCs137 = [10950., 11738.4, 11738.4, 14804.4]
	e_dotCs134 = [30309.,32412., 32412., 40558.8]
	t_halfCs137 = 30.1871 #from NIST
	t_halfCs134 = 2.0654 #from NIST
	#this is the same numbers used in USNCEAR 2013, based on measurements in europe after chernobyl
	T1 = 1.5
	T2 = 50
	p1 = 0.5
	p2 = 0.5
	e_dot = [e_dotCs137,e_dotCs134]
	t_half = [t_halfCs137, t_halfCs134]
	nuclidename = ['Cs-137','Cs-134']

	#Sets the parameters for the plotting
	filetype = 'png'
	if totdosetimeoption[0] == 1:
		totdoseplottype = 'log'
	elif totdosetimeoption[0] == 0:
		totdoseplottype = 'linear'
	else:
		print 'Something went wrong with the total dose plot option'
	
	if doseratetimeoption[0] == 1:
		doserateplottype = 'linear'
	elif doseratetimeoption[0] == 0:
		doserateplottype = 'log'
	else:
		print 'Something went wrong with the dose rate plot option'


	for l in range(len(nuclide)):
		if nuclide[l]==1:
			#timestep in years: the interval at which the calculations will be performed
			numberT = int(T/timestep)
			#The number of timesteps for the first 5 years of life
			numberT5years = int(5./timestep)
			#The number of timesteps for 10 years
			numberT10years = int(10./timestep)
			#the number of timesteps for the first 15 years of life
			numberT15years = int(15./timestep)
			#the number of timesteps for the first 15 years of life

			def e_dep(t):
				e_dep = e_dot[l][0] * ( (p1/((math.log(2)/t_half[l])+(math.log(2)/T1)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T1)))) + (p2/((math.log(2)/t_half[l])+(math.log(2)/T2)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T2)))))
				return e_dep

			IntegratedDose = e_dep(T)


			#The following two functions are helper functions for further calculations. They don't have any real application or meaning.
			def e_depChild(t):
				e_dep = e_dot[l][1] * ( (p1/((math.log(2)/t_half[l])+(math.log(2)/T1)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T1)))) + (p2/((math.log(2)/t_half[l])+(math.log(2)/T2)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T2)))))
				return e_dep

			IntegratedDoseChild = e_depChild(T)

			#next block to be taken out for paper

			def e_depChild4(t):
				e_dep = e_dot[l][2] * ( (p1/((math.log(2)/t_half[l])+(math.log(2)/T1)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T1)))) + (p2/((math.log(2)/t_half[l])+(math.log(2)/T2)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T2)))))
				return e_dep

			IntegratedDoseChild4 = e_depChild4(T)

			def e_depInfant(t):
				e_dep = e_dot[l][3] * ( (p1/((math.log(2)/t_half[l])+(math.log(2)/T1)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T1)))) + (p2/((math.log(2)/t_half[l])+(math.log(2)/T2)))* (1-math.exp(-t*((math.log(2)/t_half[l])+(math.log(2)/T2)))))
				return e_dep

			IntegratedDoseInfant = e_depInfant(T)


			#variables for f_build [wood, woodFireproof, concrete]
			a1 = [0.2, 0.1, 0.05]
			a2 = [0.2, 0.1, 0.05]
			T_build = [1.8, 1.8, 1.8]

			#occupancy factors [new, out,in,child10,child1]
			OFhard = [0.1, 0.2, 0.05, 0.05, 0.1]
			OFdirt = [0.1, 0.1, 0.05, 0.1, 0.1]
			OFbuild = [0.8, 0.7, 0.9, 0.85, 0.8]

			#define variables for lists of location factors
			time = []
			f_hard = []
			f_dirt = []
			f_build = [[],[],[]]
			#simplified location factor TODO: need to be able to be defined!
			f_newOUT = 1.
			f_newIN = 0.1

			#define dose lists
			eDepInt = []
			eDepIntChild = []
			eDepIntChild4 = []
			eDepIntInfant = []
			eDepStep = []
			eDepStepChild = []
			eDepStepChild4 = []
			eDepStepInfant = []

			#calculate the development of location factors over time and the stepwise dose: calculation of dose at each time and then subtraction from dose at previous timestep
			for i in range(numberT+1):
				#location factor equations hard surface and unpaved surface: 
				time.append(i*timestep)
				f_hard.append(0.5 * math.exp(-(time[-1]*math.log(2)/0.9))+0.1)
				f_dirt.append(0.5 * math.exp(-(time[-1]*math.log(2)/2.2))+0.25)
				for j in range(len(f_build)):
					#[wood, woodFireproof, concrete]
					f_build[j].append(a1[j] * math.exp(-time[-1]*math.log(2)/T_build[j])+a2[j])
				#integrated dose (that means for every time it is the sum from all previous doses). this is the equation given in UNSCEAR for e_dep
				eDepInt.append(e_dep(time[-1]))
				eDepIntChild.append(e_depChild(time[-1]))
				eDepIntChild4.append(e_depChild4(time[-1]))
				eDepIntInfant.append(e_depInfant(time[-1]))
				#Dose in every timestep: Subtract dose from previous time from the current integrated dose value
				if time[-1] == 0.0:
					eDepStep.append(eDepInt[-1])
					eDepStepChild.append(eDepIntChild[-1])
					eDepStepChild4.append(eDepIntChild4[-1])
					eDepStepInfant.append(eDepIntInfant[-1])
				else:
					eDepStep.append(eDepInt[-1] - eDepInt[-2])
					eDepStepChild.append(eDepIntChild[-1] - eDepIntChild[-2])
					eDepStepChild4.append(eDepIntChild4[-1] - eDepIntChild4[-2])
					eDepStepInfant.append(eDepIntInfant[-1] - eDepIntInfant[-2])


			#to test if the last element of the integrated dose is equal to the sum of the timestep doses
			testDoseStep = sum(eDepStep)
			if testDoseStep == eDepInt[-1]:
				print 'Integrated and stepwise dose match for '+str(nuclidename[l]) +'!'
			else:
				print 'There has been a mistake...'

			#Make everything into np arrays
			time = np.array(time)
			f_hard = np.array(f_hard)
			f_dirt = np.array(f_dirt)
			#Location factor for buildings: [wood, woodFireproof, concrete]
			f_build = np.array(f_build)
			eDepInt = np.array(eDepInt)
			eDepIntChild = np.array(eDepIntChild)
			eDepIntChild4 = np.array(eDepIntChild4)
			eDepIntInfant = np.array(eDepIntInfant)
			eDepStep = np.array(eDepStep)
			eDepStepChild = np.array(eDepStepChild)
			eDepStepChild4 = np.array(eDepStepChild4)
			eDepStepInfant = np.array(eDepStepInfant)
			OFhard = np.array(OFhard)
			OFdirt = np.array(OFdirt)
			OFbuild = np.array(OFbuild)

			TotDoseStepOLD = []
			TotDoseIntOLD = []
			TotDoseStepNEW = []
			TotDoseIntNEW = []

			#Index explanation:

			#n=0 : NEW
			#n=1 : outdoor worker
			#n=2 : indoor worker
			#n=3 : child 10 years old
			#n=4 : child 1 year old

			#m=0 : wood house 1-3 storeys
			#m=1 : wood house 1-3 storeys fireproof
			#m=2 : concrete house multi-storey

			#Calculate dose values taking into account location factors
			#for integrated dose
			#in the case of UNSCEAR2013
			for n in range(len(OFhard)):
				#[new,out,in,child10,child1]
				if n==0:
					#print len(eDepStep)
					TotDoseStepNEW = np.array(OFhard[n]*f_newOUT*eDepStep+OFdirt[n]*f_newOUT*eDepStep+OFbuild[n]*f_newIN*eDepStep)
					for k in range(len(TotDoseStepNEW)):
						if k==0:
							TotDoseIntNEW.append(TotDoseStepNEW[k])
						elif k>0:
							TotDoseIntNEW.append(TotDoseStepNEW[k]+TotDoseIntNEW[k-1])
				elif n>0 and n<3:
					for m in range(len(f_build)):
						#[wood, woodFireproof, concrete]
						TotDoseStepOLD.append(np.array(OFhard[n]*f_hard*eDepStep+OFdirt[n]*f_dirt*eDepStep+OFbuild[n]*f_build[m]*eDepStep))
						#print "Length is " + str(len(TotDoseStepOLD))
						#print len(TotDoseStepOLD[0])
						#print "f_hard: " + str(len(f_hard))
						#print "eDepStep: " + str(len(eDepStep))
						TotDoseIntOLD.append([])
						for k in range(len(TotDoseStepOLD[0])):
							#print len(TotDoseStepOLD[0])
							if k==0: 
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k])
							elif k>0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k]+TotDoseIntOLD[-1][k-1])
				#Calculation for a Child
				elif n==3: 
					for m in range(len(f_build)):
						#[wood, woodFireproof, concrete]
						TotDoseStepOLD.append(np.array(OFhard[n]*f_hard*eDepStepChild+OFdirt[n]*f_dirt*eDepStep+OFbuild[n]*f_build[m]*eDepStep))
						TotDoseIntOLD.append([])
						for k in range(0, min(numberT10years,len(TotDoseStepOLD[0]))):
							if k==0: 
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k])
							elif k>0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k]+TotDoseIntOLD[-1][k-1])
						for k in range(numberT10years, len(TotDoseStepOLD[0])):
							if m==0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[3][k]+TotDoseIntOLD[-1][k-1])
							elif m==1:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[4][k]+TotDoseIntOLD[-1][k-1])
							elif m==2:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[5][k]+TotDoseIntOLD[-1][k-1])
							else:
								print 'There has been a mistake when calculating child dose'
				#Calculation for an infant					
				elif n==4: 
					for m in range(len(f_build)):
						#[wood, woodFireproof, concrete]
						TotDoseStepOLD.append(np.array(OFhard[n]*f_hard*eDepStepInfant+OFdirt[n]*f_dirt*eDepStep+OFbuild[n]*f_build[m]*eDepStep))
						TotDoseIntOLD.append([])
						for k in range(0, min(numberT5years,len(TotDoseStepOLD[0]))):
							if k==0: 
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k])
							elif k>0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[-1][k]+TotDoseIntOLD[-1][k-1])
						for k in range(numberT5years, min(numberT15years, len(TotDoseStepOLD[0]))):
						# This is for the age between 5 and 15: Use child dose
							if m==0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[6][k]+TotDoseIntOLD[-1][k-1])
							elif m==1:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[7][k]+TotDoseIntOLD[-1][k-1])
							elif m==2:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[8][k]+TotDoseIntOLD[-1][k-1])
							else:
								print 'There has been a mistake when calculating infant dose between 5 and 15 years'
						for k in range(numberT15years, len(TotDoseStepOLD[0])):
						#This is for the age 15 and over
							if m==0:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[3][k]+TotDoseIntOLD[-1][k-1])
							elif m==1:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[4][k]+TotDoseIntOLD[-1][k-1])
							elif m==2:
								TotDoseIntOLD[-1].append(TotDoseStepOLD[5][k]+TotDoseIntOLD[-1][k-1])
							else:
								print 'There has been a mistake when calculating infant dose over 15 years'


			#all raw dose values are in nSv/kBq/m^2 or 10^(-12)Sv/Bq

			#Make everything into numpy arrays and adjust units
			#in E-12 Sv/Bq/m^2
			TotDoseStepNEW = np.array(TotDoseStepNEW)
			TotDoseStepOLD = np.array(TotDoseStepOLD)
			#in E-9 Sv/Bq/m^2
			TotDoseIntNEW = np.array(TotDoseIntNEW)
			TotDoseIntNEW = 0.001 * TotDoseIntNEW
			TotDoseIntOLD = np.array(TotDoseIntOLD)
			TotDoseIntOLD = 0.001 * TotDoseIntOLD

			#make a directory for the graps and files
			script_dir = os.path.dirname(__file__)
			plots_dir = os.path.join(script_dir, 'plots/'+str(nuclidename[l])+str(T))
			results_dir = os.path.join(script_dir, 'files/'+str(nuclidename[l])+str(T))

			if not os.path.isdir(plots_dir):
				os.makedirs(plots_dir)
			if not os.path.isdir(results_dir):
				os.makedirs(results_dir)



			#Make an output file with all the data and input information: highligts
			#handy helper arrays and variables for plotting and output:
			Buildings = ["1-3 storey house, wood", "1-3 storey house, fireproof wood","multi-storey house, concrete"]
			OutTime = [0.2, 0.84, 1., 2.]
			OutTime = np.array(OutTime)
			OutTimeText = ['1 week', '1 month', '1 year', '2 years']
			annualDoseTime = 100.
			annualDoseTimeStart = annualDoseTime-1.


			outfile = open("files/"+ str(nuclidename[l])+str(T)+"/Summary"+str(nuclidename[l])+"_"+str(T)+"years.txt",'w')
			outfile.write("Summary of results for doses and inputs\n")
			outfile.write("\ne_dep after " +str(T)+" years, before the application of reduction factors\n")
			outfile.write('{:} {:} {:}\n'.format('Adult','Child (10 years)','Infant (1 year)'))
			outfile.write('{:} {:} {:}\n'.format(IntegratedDose,IntegratedDoseChild,IntegratedDoseInfant))

			outfile.write("\nEffective dose [nSv/Bq/$m^2] after " +str(T)+" years\n")
			outfile.write('{:}'.format('Simplified methodology'))
			outfile.write('\n{:}'.format(TotDoseIntNEW[-1]))
			outfile.write('\n{:} {:} {:} {:}'.format('Outdoor worker','Indoor worker','Child (10 years)', 'Infant (1 year)'))
			for a in range(len(Buildings)):
				outfile.write("\n"+str(Buildings[a]))
				outfile.write('\n{:} {:} {:} {:}'.format(TotDoseIntOLD[a][-1], TotDoseIntOLD[a+3][-1], TotDoseIntOLD[a+6][-1], TotDoseIntOLD[a+9][-1]))

			for c in range(len(OutTime)):
				if OutTime[c] <= T:
					outfile.write("\n\nEffective dose [nSv/Bq/$m^2] after "+str(OutTimeText[c])+"\n (actual time " +str(time[time<0.02][-1])+" years)")
					outfile.write('\n{:}'.format('Simplified methodology'))
					outfile.write('\n{:}'.format(TotDoseIntNEW[time<OutTime[c]][-1]))
					outfile.write('\n{:} {:} {:} {:}'.format('Outdoor worker','Indoor worker','Child (10 years)', 'Infant (1 year)'))
					for a in range(len(Buildings)):
						outfile.write("\n"+str(Buildings[a]))
						outfile.write('\n{:} {:} {:} {:}'.format(TotDoseIntOLD[a][time<OutTime[c]][-1], TotDoseIntOLD[a+3][time<OutTime[c]][-1], TotDoseIntOLD[a+6][time<OutTime[c]][-1], TotDoseIntOLD[a+9][time<OutTime[c]][-1]))
				elif OutTime[c] >= T:
					print "could not calculate the annual dose for " +str(OutTime[c]) + "years."
			
			for b in range(len(OutTime)):
				if OutTime[b] <= T:
					outfile.write("\n\nDose rate [nSv/Bq/$m^2/day] after "+str(OutTimeText[b])+"\n (actual time " +str(time[time<0.02][-1])+" years)")
					outfile.write('\n{:}'.format('Simplified methodology'))
					outfile.write('\n{:}'.format(TotDoseStepNEW[time<OutTime[b]][-1]))
					outfile.write('\n{:} {:} {:} {:}'.format('Outdoor worker','Indoor worker','Child (10 years)', 'Infant (1 year)'))
					for a in range(len(Buildings)):
						outfile.write("\n"+str(Buildings[a]))
						outfile.write('\n{:} {:} {:} {:}'.format(TotDoseStepOLD[a][time<OutTime[b]][-1], TotDoseStepOLD[a+3][time<OutTime[b]][-1], TotDoseStepOLD[a+6][time<OutTime[b]][-1], TotDoseStepOLD[a+9][time<OutTime[b]][-1]))
				elif OutTime[b] >= T:
					print "could not calculate the dose rate after " +str(OutTime[b]) + "years."

			if annualDoseTime <= T:
				outfile.write("\n\nEffective dose [nSv/Bq/$m^2] in year "+str(annualDoseTime))
				outfile.write('\n{:}'.format('Simplified methodology'))
				outfile.write('\n{:}'.format(TotDoseIntNEW[time<annualDoseTime][-1]-TotDoseIntNEW[time<(annualDoseTimeStart)][-1]))
			 	outfile.write('\n{:} {:} {:} {:}'.format('Outdoor worker','Indoor worker','Child (10 years)', 'Infant (1 year)'))
				for a in range(len(Buildings)):
			 		outfile.write("\n"+str(Buildings[a]))
					outfile.write('\n{:} {:} {:} {:}'.format(TotDoseIntOLD[a][time<annualDoseTime][-1]-TotDoseIntOLD[a][time<(annualDoseTimeStart)][-1], TotDoseIntOLD[a+3][time<annualDoseTime][-1]-TotDoseIntOLD[a+3][time<(annualDoseTimeStart)][-1], TotDoseIntOLD[a+6][time<annualDoseTime][-1]-TotDoseIntOLD[a+6][time<(annualDoseTimeStart)][-1], TotDoseIntOLD[a+9][time<annualDoseTime][-1]-TotDoseIntOLD[a+9][time<(annualDoseTimeStart)][-1]))
			elif annualDoseTime >= T:
				print "could not calculate the annual dose in year " +str(annualDoseTime)
			outfile.close()


			#Make an output file with all the data and input information: Location factors over time
			outfile = open("files/"+ str(nuclidename[l])+str(T)+"/LocationFactors"+str(nuclidename[l])+"_"+str(T)+"years.txt",'w')
			outfile.write("#Output file location factors over time as used in UNSCEAR 2013\n")
			outfile.write('#{:} {:} {:} {:} {:} {:}\n'.format('Time [y]','f_build','f_hard','f_build(wood)','f_build(woodFireproof)','f_build(concrete)'))
			for i in range(len(time)):
				outfile.write("{:} {:} {:} {:} {:} {:}\n".format(time[i],f_hard[i],f_dirt[i],f_build[0][i],f_build[1][i],f_build[2][i]))
			outfile.close()


			#Make an output file with all the data and input information: Integrated Dose
			outfile = open("files/"+str(nuclidename[l])+str(T)+"/depositionTotalDoseOutput_"+str(nuclidename[l])+"_"+str(T)+"years.txt",'w')
			outfile.write("#Output file for comparison of UNSCEAR 2013 and UNSCEAR 2016 methodology for calculating dose due to deposition\n")
			#outfile.write("#List of input variables:\n")
			outfile.write('#Effective dose rate coefficient for {:} = {:} nSv/kBq/m^2/y\n'.format(nuclidename[l],e_dot[l][0]))
			outfile.write('#{:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:}\n'.format('Time [y]', 'D_tot(simplified)[nSv/Bq/$m^2]', 'D_tot(wood_outdoorW)', 'D_tot(wood_indoorW)','D_tot(wood_Child10)','D_tot(wood_Child1)','D_tot(woodFireproof_outdoorW)', 'D_tot(woodFireproof_indoorW)','D_tot(woodFireproof_Child10)','D_tot(woodFireproof_Child1)','D_tot(concrete_outdoorW)', 'D_tot(concrete_indoorW)','D_tot(concrete_Child10)','D_tot(concrete_Child1)'))
			for i in range(len(time)):
				outfile.write("{:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:}\n".format(time[i],TotDoseIntNEW[i],TotDoseIntOLD[0][i],TotDoseIntOLD[3][i],TotDoseIntOLD[6][i],TotDoseIntOLD[9][i],TotDoseIntOLD[1][i],TotDoseIntOLD[4][i],TotDoseIntOLD[7][i],TotDoseIntOLD[10][i],TotDoseIntOLD[2][i],TotDoseIntOLD[5][i],TotDoseIntOLD[8][i],TotDoseIntOLD[11][i]))
			outfile.close()

			#Make an output file with all the data and input information: Dose Rate
			outfile = open("files/"+str(nuclidename[l])+str(T)+"/depositionDoseRateOutput_"+str(nuclidename[l])+"_"+str(T)+"years.txt",'w')
			outfile.write("#Output file for comparison of UNSCEAR 2013 and UNSCEAR 2016 methodology for calculating dose due to deposition\n")
			#outfile.write("#List of input variables:\n")
			outfile.write('#Effective dose rate coefficient for {:} = {:} nSv/kBq/m^2/y\n'.format(nuclidename[l],e_dot[l][0]))
			outfile.write('#{:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:}\n'.format('Time [y]', 'D_rate(simplified)[nSv/Bq/$m^2/day]', 'D_rate(wood_outdoorW)', 'D_rate(wood_indoorW)','D_rate(wood_Child10)','D_rate(wood_Child1)','D_rate(woodFireproof_outdoorW)', 'D_rate(woodFireproof_indoorW)','D_rate(woodFireproof_Child10)','D_rate(woodFireproof_Child1)','D_rate(concrete_outdoorW)', 'D_rate(concrete_indoorW)','D_rate(concrete_Child10)','D_rate(concrete_Child1)'))
			for i in range(len(time)):
				outfile.write("{:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:} {:}\n".format(time[i],TotDoseStepNEW[i],TotDoseStepOLD[0][i],TotDoseStepOLD[3][i],TotDoseStepOLD[6][i],TotDoseStepOLD[9][i],TotDoseStepOLD[1][i],TotDoseStepOLD[4][i],TotDoseStepOLD[7][i],TotDoseStepOLD[10][i],TotDoseStepOLD[2][i],TotDoseStepOLD[5][i],TotDoseStepOLD[8][i],TotDoseStepOLD[11][i]))
			outfile.close()


			#Plot all graphs

			#location factors
			plt.plot(time,f_hard, label=r'$f_{hard}$')
			plt.plot(time,f_dirt, label=r'$f_{dirt}$')
			plt.plot(time, f_build[0], label=r'$f_{build, wood}$')
			plt.plot(time, f_build[1], label=r'$f_{builf, fireproof}$')
			plt.plot(time, f_build[2], label=r'$f_{build,concrete}$',markevery=mark_step_num)
			plt.title('Location factors')
			plt.ylabel('Location factor')
			plt.xlabel('Time [y]')
			plt.xscale('log')
			plt.legend(loc ='best')
			plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/LocationFactorsOverTime'+'.'+str(filetype))
			#plt.show()
			plt.close()

			#make custom plots
			#  'Select variables to plot:'
			if graphoption[0]==1:
				#wood house
				plt.plot(time,TotDoseIntNEW, label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[0], label = 'Outdoor worker')
				plt.plot(time, TotDoseIntOLD[3], label = 'Indoor worker')
				plt.plot(time, TotDoseIntOLD[6], label = 'Child (10 years)')
				plt.plot(time, TotDoseIntOLD[9], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n 1-3 storey house, wood. ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseWood'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#wood house, fireproof
				plt.plot(time,TotDoseIntNEW, label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[1], label = 'Outdoor worker')
				plt.plot(time, TotDoseIntOLD[4], label = 'Indoor worker')
				plt.plot(time, TotDoseIntOLD[7], label = 'Child (10 years)')
				plt.plot(time, TotDoseIntOLD[10], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n 1-3 storey house, fireproof wood. ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))				
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseFireproofWood'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#concrete house, multi-storey
				plt.plot(time,TotDoseIntNEW, label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[2], label = 'Outdoor worker')
				plt.plot(time, TotDoseIntOLD[5], label = 'Indoor worker')
				plt.plot(time, TotDoseIntOLD[8], label = 'Child (10 years)')
				plt.plot(time, TotDoseIntOLD[11], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n multi-storey house, concrete. ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseConcrete'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Dose rates
				#wood house
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW, label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[0], label = 'Outdoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[3], label = 'Indoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[6], label = 'Child (10 years)')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[9], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n 1-3 storey house, wood. ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateWood'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#wood house, fireproof
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW, label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[1], label = 'Outdoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[4], label = 'Indoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[7], label = 'Child (10 years)')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[10], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n 1-3 storey house, fireproof wood. ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateFireproofWood'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#concrete
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW , label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[2], label = 'Outdoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[5], label = 'Indoor worker')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[8], label = 'Child (10 years)')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[11], label = 'Child (1 year)',markevery=mark_step_num)
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n multi-storey house, concrete. ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateConcrete'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

			if graphoption[1]==1:
				#Total doses
				#Outdoor worker
				plt.plot(time,TotDoseIntNEW , label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[0], label = '1-3 storey house, wood')
				plt.plot(time, TotDoseIntOLD[1], label = '1-3 storey house, fireproof wood')
				plt.plot(time, TotDoseIntOLD[2], label = 'multi-storey house, concrete)')
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n Outdoor worker. ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseOutdoorWorker'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Indoor worker
				plt.plot(time,TotDoseIntNEW , label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[3], label = '1-3 storey house, wood')
				plt.plot(time, TotDoseIntOLD[4], label = '1-3 storey house, fireproof wood')
				plt.plot(time, TotDoseIntOLD[5], label = 'multi-storey house, concrete)')
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n Indoor worker. ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseIndoorWorker'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Child 10 years
				plt.plot(time,TotDoseIntNEW , label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[6], label = '1-3 storey house, wood')
				plt.plot(time, TotDoseIntOLD[7], label = '1-3 storey house, fireproof wood')
				plt.plot(time, TotDoseIntOLD[8], label = 'multi-storey house, concrete)')
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n Child (10 years). ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseChild10yr'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Child 1 year
				plt.plot(time,TotDoseIntNEW , label = 'UNSCEAR 2016')
				plt.plot(time, TotDoseIntOLD[9], label = '1-3 storey house, wood')
				plt.plot(time, TotDoseIntOLD[10], label = '1-3 storey house, fireproof wood')
				plt.plot(time, TotDoseIntOLD[11], label = 'multi-storey house, concrete)')
				plt.title(r'Effective dose ($e_{dep}$) due to ' + str(nuclidename[l]) + ' deposition, \n Child (1 year). ')
				plt.ylabel(r'Effective Dose [$10^{-9}$ Sv/Bq/$m^2$]')
				plt.xlabel('Time [y]')
				plt.xscale(str(totdoseplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/IntDoseChild1yr'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()
			

				#dose rates
				#Outdoor worker
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW , label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[0], label = '1-3 storey house, wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[1], label = '1-3 storey house, fireproof wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[2], label = 'multi-storey house, concrete)')
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n Outdoor worker. ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateOutdoorWorker'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Indoor worker
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW , label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[3], label = '1-3 storey house, wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[4], label = '1-3 storey house, fireproof wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[5], label = 'multi-storey house, concrete)')
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n Indoor worker. ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateIndoorWorker'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Child 10 years
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW , label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[6], label = '1-3 storey house, wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[7], label = '1-3 storey house, fireproof wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[8], label = 'multi-storey house, concrete)')
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n Child (10 years). ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateChild10yr'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

				#Child 1 year
				plt.plot(time,(timestep/(1/365.))*TotDoseStepNEW , label = 'UNSCEAR 2016')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[9], label = '1-3 storey house, wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[10], label = '1-3 storey house, fireproof wood')
				plt.plot(time, (timestep/(1/365.))*TotDoseStepOLD[11], label = 'multi-storey house, concrete)')
				plt.title(r'Dose rate due to ' + str(nuclidename[l]) + ' deposition, \n Child (1 year). ')
				plt.ylabel(r'Dose rate [$10^{-9}$ Sv/Bq/$m^2$/day]')
				plt.xlabel('Time [y]')
				plt.xscale(str(doserateplottype))
				plt.legend(loc ='best')
				plt.savefig('plots/'+str(nuclidename[l])+str(T)+'/DoseRateChild1yr'+str(nuclidename[l]) +'.'+str(filetype))
				#plt.show()
				plt.close()

		elif nuclide[l]==0:
			print 'Skipping ' + str(nuclidename[l]) + ' since it was not selected!'

	return 
