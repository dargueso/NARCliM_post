#!/usr/bin/env python
"""postprocess_NARCliM.py script
   Script to postprocess WRF outputs from NARCliM project
   It reads an input file (NARClIM_post.input), where the input arguments are provided
	
   Authors: Daniel Argueso (d.argueso@unsw.edu.au), Alejandro Di Luca (a.diluca@unsw.edu.au)
   Institution: CoECSS, UNSW. CCRC, UNSW.
   Created: 13 September 2013
   Modified: 17 Septemvber 2013
"""

import netCDF4 as nc
import numpy as np
import sys
import os 
import datetime as dt
import glob
from optparse import OptionParser
import postprocess_modules as pm
import compute_vars as cv
import calendar as cal

# Check initial time
ctime_i=pm.checkpoint(0)
ctime=pm.checkpoint(0)

#### READING INPUT FILE ######
### Options 

parser = OptionParser()

parser.add_option("-i", "--infile", dest="infile",
help="file with the input arguments", metavar="INPUTFILE")
(opts, args) = parser.parse_args()

###


inputinf,out_variables=pm.read_input(opts.infile)



##############################

pathin=inputinf['pathin']
pathout=inputinf['pathout']
GCM=inputinf['GCM']
RCM=inputinf['RCM']
syear=int(inputinf['syear'])
eyear=int(inputinf['eyear'])
domain=inputinf['domain']
outfile_patt=inputinf['outfile_patt']
overwrite=False
time_units="hours since 1949-12-01 00:00:00"

#CREATE OUTPUT DIR IF IT DOESN'T EXIST
fullpathout='%s/%s/%s/%s-%s/%s' %(pathout,GCM,RCM,syear,eyear,domain)
if not os.path.exists(fullpathout):
	os.makedirs(fullpathout)

#CREATE A TEMPORAL DIR WITHIN THE OUTPUT DIR IF IT DOESN'T EXIST
if not os.path.exists("%s/temp/" %(fullpathout)):
	os.makedirs("%s/temp/" %(fullpathout))


#CREATE A LOG IFLE TO PUT OUTPUT FROM THE MAIN SCRIPT
datenow=dt.datetime.now().strftime("%Y-%m-%d_%H:%M")
logfile = '%s/postprocess_%s_%s_%s-%s_%s_%s.log' %(fullpathout,GCM,RCM,syear,eyear,domain,datenow)
print 'The output messages are written to %s' %(logfile)
#sys.stdout = open('%s' %(logfile), "w") 


#### Reading variable info file ######
varinfo=pm.read_varinfo("./info_files/variables.inf")
file_type=varinfo.keys()

######################################
if GCM=='CCCMA3.1':
	calendar=='noleap'
else:
	calendar='standard'


#***********************************************
# LOOP OVER ALL TYPES OF WRF FILE OUTPUTS (i.e., wrfhrly, wrfout, etc) 
for filet in file_type:
	filet='wrfout'
	#filet='wrfhrly'
	print '\n','\n', '*************************************'
	print '  PROCESSING ', filet, ' FILE OUTPUTS'
	print '*************************************'

		
	if filet=='wrfhrly':
		n_files=12	
		time_step=1 #hours between two time steps
		file_freq='01H'
		sper=syear
		eper=eyear
		perstep=1


	if filet=='wrfout':
		time_step=3 #hours between two time steps
		file_freq='03H'
		sper=syear
		eper=eyear
		perstep=5
		

	#***********************************************
	# LOOP OVER YEARS
	for per in np.arange(sper,eper+1,perstep):
		per_f=per+perstep-1

		if filet=='wrfout':
			n_leap=0
			for pp in np.arange(per,per_f+1):
				if cal.isleap(pp):
					n_leap=n_leap+1	
				n_files=perstep*365+n_leap


		# SELECTING FILES TO READ
		print '\n', ' -> PROCESSING PERIOD: ', str(per)+' - '+str(per_f)
		loadfiles = pathin+'%s_%s_%s*' % (filet,domain,per) # Specify path
		files_in=[]
		tot_files=0
		pp_count=0
		for pp in np.arange(per,per_f+1):
			loadfiles = pathin+'%s_%s_%s*' % (filet,domain,pp) # Specify path
			files_in.append(sorted(glob.glob(loadfiles)))
			tot_files=len(files_in[pp_count])+tot_files
			pp_count=pp_count+1
		print '  -->  Number of files to read:', tot_files	

		# -------------------
		# CHECKING: Check if the number of files is right
		if tot_files!=n_files:
			print '\n', 'ERROR: the number of ',filet, ' files in period ', per,' is INCORRECT'
			print ' ---- SOME FILES ARE MISSING ---'
			print 'SCRIPT stops running ','\n' 
			sys.exit(0)

		# ***********************************************
		# LOOP OVER VARIABLES IN THE GIVEN KIND OF FILE
		for var in varinfo[filet].keys():
			ctime_var=pm.checkpoint(0)

			# ***********************************************************
			# BEFORE READING AND PROCESSING THE VARIABLE OF INTEREST CHECK 
			# IF THE FILE ALREADY EXISTS
			# If it does then go to the next one...
			file_out=pathout+'%s%s_%s-%s_%s.nc' % (outfile_patt,file_freq,per,per_f,var) # Specify output file
			a=os.path.exists(file_out)
			print '  --> OUTPUT FILE:'
			print '                 ', file_out
			if a==True and overwrite==False:
				print '                  +++ FILE ALREADY EXISTS +++'
			else:
				if  a==True and overwrite==True:
					print '                   +++ FILE EXISTS AND WILL BE OVERWRITE +++'
				else:
					print '                   +++ FILE DOES NOT EXISTS YET +++'
			# ***********************************************************

				print '  -->  READING VARIABLE ', var
				time_bounds=False
				time_bnds=pm.const.missingval
				wrfvar=(pm.getwrfname(var)[0]).split('-')

				# READ FILES FROM THE CORRESPONDING PERIOD
				time_old =[]
				varval=[]
				varval1=[]
				varval2=[]
				pp_count=0
				for pp in np.arange(per,per_f+1):
					print '     -> READING YEAR: ', pp
					fin=nc.MFDataset(files_in[pp_count]) # Read all files
					print '        fin done'
					time_old.append(fin.variables['Times'][:]) # Get time variable
					print '        time done'
					# ***********************************************
					# LOOP over wrf variables need to compute the variable of interest
					count_v=0
					for wrfv in wrfvar:
						if count_v==0:
							varval.append(fin.variables[wrfv][:])
						if count_v==1:
							varval1.append(fin.variables[wrfv][:])
						if count_v==2:
							varval2.append(fin.variables[wrfv][:])
						count_v=count_v+1
					print '        vars done'
					pp_count=pp_count+1
					fin.close()
					print '        fin close'

				sys.exit(0)

				# FIRST YEAR, MONTH, DAY AND HOUR OF ALL READ FILES
				year_i, month_i, day_i, hour_i = pm.get_wrfdate(time_old[0,:])

				# LAST YEAR, MONTH, DAY AND HOUR OF ALL READ FILES
				year_f, month_f, day_f, hour_f = pm.get_wrfdate(time_old[-1,:])

				# DEFINE DATES USING STANDARD CALENDAR
				n_days = dt.datetime(per+1,month_i,day_i,hour_i)-dt.datetime(per,month_i,day_i,hour_i)
				n_timesteps=n_days.days*int(24./time_step)
				date = [dt.datetime(per,month_i,day_i,hour_i)+ dt.timedelta(hours=x) for x in xrange(0,n_timesteps*time_step,time_step)]
				time=nc.date2num(date[:],units=time_units)

				# -------------------
				# CHECKING: Check if the of time steps is right
				if n_timesteps!=time_old.shape[0]:
					print '\n', 'ERROR: the number of timesteps in period ', per,' is INCORRECT'
					print 'There should be: ', n_timesteps
					print 'There are: ', time_old.shape[0]
					print 'SCRIPT stops running ','\n'
					sys.exit(0)


				# FOR LEAP YEARS AND MODELS WITH NO LEAP YEARS REPLACE THE 29TH FEBRUARY BY 
				# MISSING VALUES
				if calendar=='noleap' and cal.isleap(per)==True:
					months_all=np.asarray([date[i].month for i in xrange(len(date))]) 
					days_all=np.asarray([date[i].day for i in xrange(len(date))])
					index=np.where(np.logical_and(months_all==2,days_all==29))

					count_v=0
					for wrfv in wrfvar:
						if count_v==0:
							varval = pm.add_leap(varval,index)

						if count_v==1:
							varval1 = pm.add_leap(varval1,index)

						if count_v==2:
							varval2 = pm.add_leap(varval2,index)

						count_v=count_v+1


				# PRECIPITATION NEEDS ONE TIME STEP MORE TO COMPUTE DIFFERENCES
				if var=='pracc' or var=='potevp' or var=='evspsbl':

					# DEFINE TIME BOUNDS FOR ACCUMULATED VARIABLES
					time_bounds=True
					date_inf=date
					time_inf=nc.date2num(date_inf[:],units=time_units)
					date_sup=[dt.datetime(per,month_i,day_i,hour_i+time_step)+ \
							   dt.timedelta(hours=x) for x in xrange(0,n_timesteps*time_step,time_step)]
					time_sup=nc.date2num(date_sup[:],units=time_units)
					time_bnds=np.reshape(np.concatenate([time_inf,time_sup]), (time.shape[0],2))

					# READ ONE MORE TIME STEP FOR ACCUMULATED COMPUTATIONS
					last_file = sorted(glob.glob(pathin+'%s_%s_%s-01-01_*' % (filet,domain,per+1)))
					fin2=nc.Dataset(last_file[0],mode='r')
					count_v=0
					for wrfv in wrfvar:
						if count_v==0:
							last_varval=np.reshape(np.array(fin2.variables[wrfv][0,:,:], \
												dtype='d'),(1,varval.shape[1],varval.shape[2]))
							varval=np.concatenate((varval,last_varval))
						if count_v==1:
							last_varval=np.reshape(np.array(fin2.variables[wrfv][0,:,:], \
												dtype='d'),(1,varval.shape[1],varval.shape[2]))
							varval1=np.concatenate((varval1,last_varval))
						count_v=count_v+1
					fin2.close()


				# CALL COMPUTE_VAR MODULE
				compute=getattr(cv,'compute_'+var) # FROM STRING TO ATTRIBUTE
				if len(wrfvar)==1:
					varval, varatt=compute(varval,date)
				if len(wrfvar)==2:
					varval, varatt=compute(varval,varval1,date)
				if len(wrfvar)==3:
					varval, varatt=compute(varval,varval1,varval2,date)

				# INFO NEEDED TO WRITE THE OUTPUT NETCDF
				netcdf_info=[file_out, var, varatt, calendar, domain, files_list[0], GCM, RCM, time_bounds]

				# CREATE NETCDF FILE
				aa=pm.create_netcdf(netcdf_info, varval, time, time_bnds)
				ctime=pm.checkpoint(ctime_var)
				print '=====================================================', '\n', '\n', '\n'
	
				
		# ***********************************************
		# LOOP over variables
		for var in out_variables:
		
			# ***********************************************
			# LOOP over FREQUENCIES
			freqlist=(varinfo[filet][var]).split(',')
			for freq in freqlist:
				print freq

    




#***********************************************
# Loop over all types of WRF output files (i.e., wrfhrly, wrfout, etc) 
for filet in file_type:
     if (filet!='wrfxtrm') or (filet!='wrfdly'): # These files are already daily
        for varname in varinfo[filet].keys():
            
            stat_all=varinfo[filet][varname].split(',')
            
            
            fileall=sorted(glob.glob('%s/%s0?H_*_%s.nc' %(fullpathout,outfile_patt,varname)))
            eyfile=np.asarray([int(fileall[i].split('_%s.nc' %(varname))[0][-4:]) for i in xrange(len(fileall))])
            syfile=np.asarray([int(fileall[i].split('_%s.nc' %(varname))[0][-9:-5]) for i in xrange(len(fileall))])
            
            fileref=nc.Dataset(fileall[0],'r')
            
            syp=syear
            while syp<eyear:
                eyp=((int(syp)/5)+1)*5
                sel_files=[fileall[i] for i in xrange(len(syfile)) if ((syfile[i]>=syp) & (eyfile[i]<eyp))]
                files=nc.MFDataset(sel_files)
                time=nc.num2date(files.variables['time'][:],units=files.variables['time'].units)
                var=files.variables[varname][:]
                
                for stat in stat_all:
                    dvar,dtime=cs.compute_daily(var,time,stat)
                    dtime_nc=nc.date2num(dtime,units=time_units)
                    varatts={}
                                        
                    for att in fileref.variables[varname].ncattrs():
                        varatts[att]=getattr(fileref.variables[varname],att)
                    
                    
                syp=eyp.copy()


for filet in filetype:
    for varname in varinfo[filet].keys():
        stat_all=varinfo[filet][varname].split(',')
        fileall=sorted(glob.glob('%s/%sDAY_*_%s.nc' %(fullpathout,outfile_patt,varname)))
        eyfile=np.asarray([int(fileall[i].split('_%s.nc' %(varname))[0][-4:]) for i in xrange(len(fileall))])
        syfile=np.asarray([int(fileall[i].split('_%s.nc' %(varname))[0][-9:-5]) for i in xrange(len(fileall))])
        
        fileref=nc.Dataset(fileall[0],'r')
        
        syp=syear
        while syp<eyear:
            eyp=((int(syp)/10)+1)*10
            sel_files=[fileall[i] for i in xrange(len(syfile)) if ((syfile[i]>=syp) & (eyfile[i]<eyp))]
            files=nc.MFDataset(sel_files)
            time=nc.num2date(files.variables['time'][:],units=files.variables['time'].units)
            var=files.variables[varname][:]

            for stat in stat_all:
                mvar,mtime=cs.compute_monthly(var,time,stat)
		mtime_nc=nc.date2num(mtime,units=time_units)
		varatts={}
   
		
		for att in fileref.variables[varname].ncattrs():
                    varatts[att]=getattr(fileref.variables[varname],att)
                    
            syp=eyp.copy()     
