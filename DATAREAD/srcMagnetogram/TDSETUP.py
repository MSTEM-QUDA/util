#!/usr/bin/env python
# make FRM in SWMF/util/EMPIRICAL/srcEE/

import subprocess
import os
import fnmatch
import remap_magnetogram as rmag
import numpy as np
import argparse
import TDSETUPAlg as TD


BMax = 1900.0
cPi = np.pi
Rad2Deg = 180/cPi
Deg2Rad = 1/Rad2Deg
IsPositionInput = 0

if __name__ == '__main__':
   parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter)
   parser.add_argument('NameFile', help='Input FITS file name including path')
   parser.add_argument('-nSmooth',type=int, default=1, help=
                       'If nSmooth is ODD integer larger than 1, apply boxcar smoothing on the magnetic field')
   parser.add_argument('--CMEGrid',action='store_true', help=
                       'Output parameters of the refined CME grid')
   parser.add_argument('-Helicity',type=int,default=0, help=
                       'Use specified helicity')
   parser.add_argument('-LonPosIn',type=float,default=999.0, help=
                       'Longitude for positive spot center (Deg)')
   parser.add_argument('-LatPosIn',type=float,default=999.0, help=
                       'Latitude for positive spot center (Deg)')
   parser.add_argument('-LonNegIn',type=float,default=999.0, help=
                       'Longitude for negative spot center (Deg)')
   parser.add_argument('-LatNegIn',type=float,default=999.0, help=
                       'Latitude for negative spot center (Deg)')
   args = parser.parse_args()
   ##################OPTIONAL INPUT PARAMETERS######
   NameFile    = args.NameFile
   UseCMEGrid  = args.CMEGrid
   nSmooth     = args.nSmooth
   Helicity    = args.Helicity
   xPositive   = args.LonPosIn
   yPositive   = args.LatPosIn
   xNegative   = args.LonNegIn
   yNegative   = args.LatNegIn

   IdlFile = 'fitsfile.out'
   UseBATS = False
   # Check if the file extension is .out
   SplitName = NameFile.split('.')
   if  SplitName[-1]=='out':
      print('\n File name '+NameFile+
            ' has extension .out, is treated as ASCII converted file')
      UseBATS = True
  
   if (xPositive !=999. and yPositive !=999. and yNegative !=999.
       and xNegative !=999.):
      IsPositionInput = 1
      print('User input the x,y positions for Positive and Negative centers')
      print('Input Weighted centers :',xPositive,yPositive,xNegative,yNegative)
   else:
      IsPositionInput = 0
   
   ##################END OF PARSER#####################
   #################SERVER SIDE, PYTHON################
   #################PROCESS MAGNETOGRAM###
   ##READ AND SMOOTH, IF DESIRED########################
   if UseBATS:
      cc =  rmag.read_bats(NameFile)
      nIndex_I     = cc[0]
      nLong        = nIndex_I[0]
      nLat         = nIndex_I[1]
      nVar         = cc[1]
      nParam       = cc[2]
      Param_I      = cc[3]
      Long0        = Param_I[0] # Longitude of left edge
      Time         = cc[7]
      LongEarth    = Param_I[1]         # CR number
      Long_I       = cc[4]*Deg2Rad      # in radians
      Lat_I        = cc[5]*Deg2Rad      # in radians
      data         = cc[6]
      if nVar ==1:
         Br_C = data
      else:
         Br_C = data[:,:,0]
      if nSmooth > 2:
         Br_C = rmag.smooth(nLong,  nLat,  nSmooth, Br_C)
         StrHeader = cc[8]
         NameVar   = cc[9]
         if nVar==1:
            data = Br_C
         else:
            data[:,:,0] = Br_C
         IdlFile = rmag.save_bats('Smoothed.out',StrHeader, NameVar, [nLong,nLat], nVar, nParam, Param_I,
                                  Long_I*Rad2Deg, Lat_I*Rad2Deg, data, Time)
      else:
         IdlFile = NameFile
   else:
      # fits magnetogram is read, remapped (if required) using
      # remap_magnetogram.py to fitsfile.out
      cc = rmag.remap(NameFile, IdlFile, nlat, nlon, 'unspecified',
                      0, nSmooth,BMax)
      nLong        = cc[0]
      nLat         = cc[1]
      nParam       = cc[2]
      Param_I      = cc[3]
      Long0        = Param_I[0] # Longitude of left edge
      LongEarth    = Param_I[1] # CR number of central meridian
      Long_I       = cc[4]      # in radians
      Lat_I        = cc[5]      # in radians
      Br_C         = cc[6]
      Time         = cc[9]

   FileId=open('CME.in','w')
   if NameFile=='field_2d.out':
      FileId.write("#LOOKUPTABLE \n")
      FileId.write("B0			NameTable \n")
      FileId.write("load			NameCommand \n")
      FileId.write("harmonics_bxyz.out		NameFile \n")
      FileId.write("real4			TypeFile \n")
   FileId.write("\n")
   FileId.close()
   #Info to the idl session is passed via the fitsfile.out file####
   ############END OF PYTHON FIRST SESSION##########
   ###IDL SESSION IN THE SWMF_GLSETUP/BROWSER SESSION IN EEGGL##

   if IsPositionInput == 0:
      print('Select the CME Source Region (POSITIVE) with the left button')
      print('Then select negative region with the right button')

      FileId=open('runidl1','w')
      FileId.write(';\n;\n')
      FileId.write(
         "      GLSETUP1,file='"+IdlFile+"' \n")
      FileId.close()
   ########SHOW MAGNETOGRAM##########################
   # GLSETUP1.pro is run, it reads the magnetogram(fitsfile.out)
   # reads the cursor x,y indices for neg and pos. AR.
      ls = subprocess.Popen(["idl", "runidl1"],stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,text=True)
   #################PROCESSING STDOUT################
      stdout,stderr=ls.communicate()
      b=stdout[stdout.index('===')+4:len(stdout)]
      a=b.split() # x,y coordinates 
   ###### TAKE TWO COORDINATES FROM TWO CLICKS#######
      xPositive = float(a[0])
      yPositive = float(a[1])
      xNegative = float(a[2])
      yNegative = float(a[3])
   ##########SHAPE INPUTS FOR THE SECOND SERVER-SIDE SESSION####
   nParam  = 6
   Param_I = np.zeros(nParam)
   Param_I[0] = Long0
   Param_I[1] = LongEarth
   # Below the x,y positions are equal to location of clicks OR 
   # the location of weighted centers as input by the user, IsPositionInput =1
   # These are passed to TDSETUPALg.py and weighted centers are calculated
   Param_I[2] = xPositive
   Param_I[3] = yPositive
   Param_I[4] = xNegative
   Param_I[5] = yNegative

   ##SECOND SERVER-SIDE SESSION (PYTHON)#######################
   CC=TD.Alg(nLong,nLat,nParam,Param_I,Long_I,Lat_I,Br_C,UseCMEGrid,
             Helicity, IsPositionInput,Time)
   exit()
   FileId=open('runidl','w')
   FileId.write(';\n;\n')
   FileId.write("GLSETUP2, file='AfterGLSETUP.out',/UseBATS \n")
   FileId.close()
   ###FINAL SESSION: SHOW MAGNETOGRAM AND BIPOLAR STRUCTURE OF AR
   subprocess.call(['idl','runidl'])
   ###IF THE MASTER SCRIPT IS IN PYTHON, AND A CHILD PROCESS IS IN IDL
   #(1) THE TIME OF IDL SESSION SHOULD BE LIMITED (30 seconds or so) 
   #(2) WINDOWS SHOULD BE CLOSED 
   #(3) FINAL EXIT COMMAND MUST BE PRESENT IN THE IDL SCRIPT######
   #print 'GLSETUP Session is closed. Bye!!!'
##############################################