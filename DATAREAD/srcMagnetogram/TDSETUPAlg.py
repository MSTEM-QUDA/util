#!/usr/bin/env python
import numpy as np
import remap_magnetogram as rmag
import GLSETUPAlg as GL
import os
import fnmatch
import math
import subprocess
BMax = 1900.0
cPi  = np.pi
Rad2Deg = 180/cPi
Deg2Rad = cPi/180

def get_weighted_center(X,Y,Br_C,BrThreshold,nLat,nLong,Lat_I,Long_I,\
                           IsUniformLat):
   LonIndex = GL.round_my(X)
   LatIndex = GL.round_my(Y)
   print('\n Chosen Longitude, Latitude =',Long_I[LonIndex]*Rad2Deg,
         Lat_I[LatIndex]*Rad2Deg)
   #Occcupancy matrix
   occ = np.zeros([nLat,nLong])
   occ[LatIndex,LonIndex] = 1
   #Occupancy level
   occ_level = 0
   #Occupancy level check
   occ_check = 1
   while occ_check > 0:
      occ_level = occ_level + 1
      [row,col] = np.where(occ == occ_level)
      n = row.size
      # row= lat, col = long
      for i in np.arange(n):
         rowp = row[i]
         colp = col[i]
         if BrThreshold > 0. :
            if rowp-1 > 0:
               if (Br_C[rowp-1,colp] > BrThreshold and occ[rowp-1,colp] == 0):
                  occ[rowp-1,colp] = occ_level + 1
            if rowp+1 < nLat:
               if (Br_C[rowp+1,colp] > BrThreshold and occ[rowp+1,colp] == 0):
                  occ[rowp+1,colp] = occ_level + 1
            if colp-1 > 0:
               if (Br_C[rowp,colp-1] > BrThreshold and occ[rowp,colp-1] == 0):
                  occ[rowp,colp-1] = occ_level + 1
            if colp+1 < nLong:
               if (Br_C[rowp,colp+1] > BrThreshold and occ[rowp,colp+1] == 0):
                  occ[rowp,colp+1] = occ_level + 1
         elif BrThreshold < 0.:
            if rowp-1 > 0:
               if (Br_C[rowp-1,colp] < BrThreshold and occ[rowp-1,colp] == 0):
                  occ[rowp-1,colp] = occ_level + 1
            if rowp+1 < nLat:
               if (Br_C[rowp+1,colp] < BrThreshold and occ[rowp+1,colp] == 0):
                  occ[rowp+1,colp] = occ_level + 1
            if colp-1 > 0:
               if (Br_C[rowp,colp-1] < BrThreshold and occ[rowp,colp-1] == 0):
                  occ[rowp,colp-1] = occ_level + 1
            if colp+1 < nLong:
               if (Br_C[rowp,colp+1] < BrThreshold and occ[rowp,colp+1] == 0):
                  occ[rowp,colp+1] = occ_level + 1
      occ_check = n
   #end whileloop
   SizeMap_C = np.zeros([nLat,nLong])
   #Calculate weighted center
   [LatOcc,LonOcc] = np.where(occ>0)
   nSize = LatOcc.size
   LatCenter=0.
   LonCenter=0.
   Flux=0.
   Area = 0.
   #flux = SUM(area * Br)
   dLon    = 2.*cPi/nLong
   dLat    = cPi/nLat
   dSinLat = 2.0/nLat
   for i in np.arange(nSize):
      iLon  = LonOcc[i]
      iLat  = LatOcc[i]
      if IsUniformLat : # uniform in lat
         dArea = np.cos(Lat_I[iLat]) * dLat * dLon   # in radians^2
      else:
         dArea = dSinLat * dLon   # in radians^2
      dFlux = Br_C[iLat,iLon] * dArea
      LonCenter += Long_I[iLon] * dFlux
      LatCenter +=  Lat_I[iLat] * dFlux
      Flux += dFlux
      Area += dArea
      SizeMap_C[iLat,iLon]=Br_C[iLat,iLon]
   LonCenter /= Flux  # in Radians
   LatCenter /= Flux  # in Radians
   # return the longitude and latitude of the weighted center in radians, 
   # area in radians^2, and the occupancy matrix for plotting
   return(LatCenter,LonCenter,SizeMap_C,Flux, LatOcc, LonOcc)

def Alg(nLong, nLat, nParam, Param_I, Long_I, Lat_I, Br_C, UseCMEGrid, 
        Helicity, IsPositionInput, Time):
   Long0     = Param_I[0]
   LongEarth = Param_I[1]
   xPositive = Param_I[2]
   yPositive = Param_I[3]
   xNegative = Param_I[4]
   yNegative = Param_I[5]
   dLon    = 2.*cPi/nLong
   dLat    = cPi/nLat
   dSinLat = 2.0/nLat
   DsLat_C = np.zeros([nLat,nLong])
   Ds2_C   = np.zeros([nLat,nLong])
   # Check if the latitude grid is uniform
   if abs(Lat_I[2]-2*Lat_I[1]+Lat_I[0])<1.0e-5:
      IsUniformLat = True
      print('Uniform in Latitude grid')
      for k in np.arange(nLat):
         for l in np.arange(nLong):
            DsLat_C[k,l] = dLat
            Ds2_C[k,l]   = dLat**2 + (np.cos(Lat_I[k])*dLon)**2
   else:
      IsUniformLat = False
      print('Uniform in Sin(Latitude) grid')
      for k in np.arange(nLat):
         for l in np.arange(nLong):
            DsLat_C[k,l] = dSinLat/np.cos(Lat_I[k])
            Ds2_C[k,l]   = DsLat_I[k,l]**2 + (np.cos(Lat_I[k])*dLon)**2
   # Pass the x, y indices of the clicks to calculate weighted center
   # and their indices

   if IsPositionInput == 1:
      print ("\n User input  Lon/Lat for Positive and negative spots:")
      print ("{0:4.1f} {1:4.1f} {2:4.1f} {3:4.1f}".format(
            xPositive, yPositive,xNegative, yNegative))
      xPositive = GL.calculate_index(xPositive*Deg2Rad,Long_I,nLong)
      yPositive = GL.calculate_index(yPositive*Deg2Rad,Lat_I, nLat)
      xNegative = GL.calculate_index(xNegative*Deg2Rad,Long_I,nLong)
      yNegative = GL.calculate_index(yNegative*Deg2Rad,Lat_I, nLat)

   # get weighted centers(Lon,Lat), occupancy matrix, Area of AR for
   # positive and negative regions
   [LatPos,LonPos,PSizeMap_C,FluxP, LatP_I, LongP_I] = \
       get_weighted_center(xPositive,yPositive,Br_C,20.,\
                              nLat,nLong,Lat_I,Long_I,IsUniformLat)
   LongPMin =  min(LongP_I)
   LongPMax =  max(LongP_I)
   print('\n Positive spot: minimum and maximum longitude  indexes',\
         LongPMin,LongPMax)
   LatPMin =  min(LatP_I)
   LatPMax =  max(LatP_I)
   print('\n Positive spot: minimum and maximum latitude  indexes',\
         LatPMin,LatPMax)
   
   LonPosIndex = GL.calculate_index(LonPos,Long_I,nLong)
   LatPosIndex = GL.calculate_index(LatPos,Lat_I, nLat)
   print('\n Positive Weighted Center indexes (lon,lat) =',\
          LonPosIndex, LatPosIndex)
   print('\n Positive Weighted Center (lon,lat) =',\
            LonPos*Rad2Deg, LatPos*Rad2Deg)

   [LatNeg,LonNeg, NSizeMap_C,FluxN, LatN_I, LongN_I] = \
       get_weighted_center(xNegative,yNegative,Br_C,-20.,\
                              nLat,nLong,Lat_I,Long_I,IsUniformLat)
   LongNMin =  min(LongN_I)
   LongNMax =  max(LongN_I)
   print('\n Negative spot: minimum and maximum longitude  indexes',\
         LongNMin,LongNMax)
   LatNMin =  min(LatN_I)
   LatNMax =  max(LatN_I)
   print('\n Negative spot: minimum and maximum latitude  indexes',\
         LatNMin,LatNMax)
   
   LonNegIndex = GL.calculate_index(LonNeg,Long_I,nLong)
   LatNegIndex = GL.calculate_index(LatNeg,Lat_I, nLat)
   print('\n Negative Weighted Center indexes (lon,lat) =',\
          LonNegIndex, LatNegIndex)
   print('\n Negative Weighted Center (lon,lat) =',\
            LonNeg*Rad2Deg,LatNeg*Rad2Deg)
   # Rectangular box  for active region
   LongARMin=min([LongNMin,LongPMin])
   LongARMin=max([LongARMin-2,0])
   LongARMax=max([LongNMax,LongPMax])
   LongARMax=min([LongARMax+2,nLong-1])
   LatARMin =min([LatNMin, LatPMin])
   LatARMin=max([LatARMin-2,0])
   LatARMax =max([LatNMax, LatPMax])
   LatARMax =min([LatARMax+2,nLat-1])
   print('\n Box for AR: minimum and maximum longitude  indexes',\
         LongARMin,LongARMax)
   print('\n Box for AR: minimum and maximum longitude  indexes',\
         LatARMin,LatARMax)

   # Distance to negative spot
   nSizeN = LatN_I.size
   Dist2N_I=np.zeros(nSizeN)
   nSizeP=LatP_I.size
   Dist2P_I=np.zeros(nSizeP)
   nLonShort = LongARMax + 1 - LongARMin
   nLatShort = LatARMax + 1 - LatARMin
   Dist2Min_C=np.zeros([nLatShort,nLonShort])
   for k in range(LatARMin , LatARMax+1):
      CosLat=np.cos(Lat_I[k])
      for l in range(LongARMin, LongARMax+1):
         for  i in np.arange(nSizeN):
            Dist2N_I[i] = (Lat_I[LatN_I[i]]-Lat_I[k])**2+CosLat**2*(
               Long_I[LongN_I[i]]-Long_I[l])**2
         for  i in np.arange(nSizeP):
            Dist2P_I[i] = (Lat_I[LatP_I[i]]-Lat_I[k])**2+CosLat**2*(
               Long_I[LongP_I[i]]-Long_I[l])**2
         Dist2Min =max([min(Dist2N_I), min(Dist2P_I)])
         if Dist2Min<1.5*Ds2_C[k,l]:
            Dist2Min_C[k-LatARMin,l-LongARMin]=Ds2_C[k,l]/Dist2Min
   # [LatPIL_I,LongPIL_I]=np.where(Dist2Min_C>0)
   # nSizePIL=LatPIL_I.size
   # print('Total number of PIL points=',nSizePIL)
   nParam = 2
   Param_I = np.zeros(nParam)
   Param_I = [Long0, LongEarth]
   nVar=4
   Data_IV=np.zeros([nLatShort,nLonShort,nVar])
   NameVar='Longitude Latitude Br PIL MapP MapN Long0 LongEarth'
   for k in np.arange(nLatShort):
      for l in np.arange(nLonShort):
         Data_IV[k,l,0]=max([-BMax,min([BMax,Br_C[k+LatARMin,l+LongARMin]])])
         Data_IV[k,l,1]=Dist2Min_C[k,l]
         Data_IV[k,l,2]=PSizeMap_C[k+LatARMin,l+LongARMin]
         Data_IV[k,l,3]=NSizeMap_C[k+LatARMin,l+LongARMin]
   FinalFile=rmag.save_bats('AfterGLSETUP.out', 'After GLSETUP: Br[Gauss]', 
                            NameVar, [nLonShort,nLatShort], nVar, nParam,
                            Param_I, Rad2Deg*Long_I[LongARMin:LongARMax+1],
                            Rad2Deg*Lat_I[LatARMin:LatARMax+1], Data_IV, Time)
   print('Select the CME Source Region (POSITIVE) with the left button')
   print('Then select negative region with the right button')

   FileId=open('runidl2','w')
   FileId.write(';\n;\n')
   FileId.write(
      "      TDSETUP1,file='"+FinalFile+"' \n")
   FileId.close()
   ########SHOW MAGNETOGRAM##########################
   # GLSETUP1.pro is run, it reads the magnetogram(fitsfile.out)
   # reads the cursor x,y indices for neg and pos. AR.
   ls = subprocess.Popen(["idl", "runidl2"],stdout=subprocess.PIPE,
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
   exit()
   PointN_I=[LonNeg,LatNeg] # negative spot
   PointP_I=[LonPos,LatPos] # positive spot

   # Find center of the active region as the point on the line
   # connecting the positive and negative center at which the MF is minimal
   # (i.e as intersection of this with PIL,
   # herewith PIL=Polarity Inversion Line
   nProfile = max([GL.round_my(abs(LonPos - LonNeg)*Rad2Deg),
                   GL.round_my(abs(LatPos-LatNeg)*Rad2Deg)]) + 1
   LonProfile_C = np.zeros(nProfile)
   LatProfile_C = np.zeros(nProfile)
   BTmp = BMax + 1.0
   for i in np.arange(nProfile):
      LonProfile = LonPos+(
         LonNeg - LonPos)*i/(nProfile - 1)
      LonProfile_C[i] = LonProfile
      LatProfile = LatPos+(
         LatNeg - LatPos)*i/(nProfile - 1)
      LatProfile_C[i] = LatProfile
      IndexLon = GL.calculate_index(LonProfile,Long_I,nLong)
      IndexLat = GL.calculate_index(LatProfile,Lat_I, nLat)
      AbsBr = abs(Br_C[IndexLat,IndexLon])
      if (AbsBr < BTmp):
         BTmp = AbsBr
         IndexARCenter_D = [IndexLon,IndexLat]
   iLonAR = IndexARCenter_D[0]
   iLatAR = IndexARCenter_D[1]
   LonAR  = Long_I[iLonAR]  # in radians
   LatAR  =  Lat_I[iLatAR]  # in radians
   print ("Center for Active region(Lon,Lat in deg):" )
   print ("{0:4.1f} {1:4.1f}".format(LonAR*Rad2Deg,LatAR*Rad2Deg))
   GL_Latitude  = LatAR * Rad2Deg
   GL_Longitude = LonAR * Rad2Deg
   if Long0>0:
      GL_Longitude +=Long0
      if GL_Longitude>=360:
         GL_Longitude-=360
   print ("GL_Longitude: {0:4.1f} GL_Latitude:{1:4.1f}".format(
         GL_Longitude, GL_Latitude))

   AngularDistance = GL.get_angular_dist(PointN_I,PointP_I)


   # GL_Orientation calculation
   # Calculate the GL flux rope orientation from the two weighted points.
   #r1=[LonNegIndex-LonPosIndex,LatNegIndex-LatPosIndex] - incorrect
   r1 = [PointN_I[0] - PointP_I[0], PointN_I[1] - PointP_I[1]]
   r1[0] *= np.cos(LonAR)
   r1 /= np.sqrt(r1[0]**2+r1[1]**2)
   r2=[1.0,0.0]
   GL_Orientation=np.arccos(r1[0]*r2[0]+r1[1]*r2[1])*Rad2Deg
   if r1[1] < 0:
      # If sine of Orientation is negative
      GL_Orientation=360-GL_Orientation  
   if IsUniformLat :
      grid_type = 'uniform'
   else:
      grid_type = 'sin(lat)'

   if Helicity != 0 : # helicity input by user
      iHelicity = Helicity
      print('Using user input helicity = ', Helicity)
   else:
      # based on hemisphere
      iHelicity = 1
      if GL_Latitude > 0: 
         iHelicity = -1
      print('Helicity based on hemisphere: ',iHelicity)

      iHelicity = -1
      Depth=0
   #Recommended GL flux rope parameters
   ### TEMPORARY !!!!!
   AngularDistance = 0.2
   print ('========================================')
   print ('The Recommended GL FLux Rope Parameters')
   print ('========================================')
   print ('#CME')
   print ('                Latitude: %6.2f'%(GL_Latitude))
   print ('               Longitude: %6.2f'%(GL_Longitude))
   print ('             Orientation: %6.2f'%(GL_Orientation))
   print ('      Angular size [deg]: %6.2f'%(AngularDistance*Rad2Deg))
   print (' Poloidal flux: positive: %6.2f'%(FluxP))
   print (' Poloidal flux: negative: %6.2f'%(FluxN))
   print ('-----------------------------------------')
   FileId=open('CME.in','a')
   FileId.write("#CME \n")
   FileId.write("T                   UseCme \n")
   FileId.write("T                   DoAddFluxRope \n")
   FileId.write("%-10.2f          LongitudeCme \n"% GL_Longitude)
   FileId.write("%-10.2f          LatitudeCme \n"% GL_Latitude)
   FileId.write("%-10.2f          OrientationCme \n"% GL_Orientation)
   FileId.write("TD22                  TypeCme \n")
   FileId.write("%-+d                  iHelicity \n"% iHelicity)
   FileId.write("%-10.2f	  RadiusMajor \n"%(AngularDistance))
   FileId.write("%-10.2f	  RadiusMinor \n"%(0.35*AngularDistance))
   FileId.write("%-10.2f	  Depth \n"%Depth)
   FileId.write("1.0e-3                 PlasmaBeta \n")
   FileId.write("5.0e5                 EjectaTemperature \n")
   FileId.write("readbstrap            TypeBStrap \n")
   FileId.write("5.0                 BStrappingDim \n")
   FileId.write("none            TypeCharge \n")
   FileId.write(" \n")
   FileId.write("#END \n")
   FileId.write("\n")
   FileId.write("Angular Size            = %5.2f\n"%(AngularDistance
                                                     *Rad2Deg))
   print (' Poloidal flux: positive: %6.2f'%(FluxP))
   print (' Poloidal flux: negative: %6.2f'%(FluxN))
   FileId.close() 

   if UseCMEGrid:
      #Calculate the CME grid refinement parameters based on the flux rope
      #location and size.                                                
      
      print ('==========================================')
      print ('The Recommended Grid Refinement Parameters')
      print ('==========================================')
      print ('              R_Start: %6.2f'% (CMEbox_Start[0]))
      print ('                R_End: %6.2f'% (CMEbox_End[0]))
      print ('      Longitude_Start: %6.2f'% ( CMEbox_Start[1]))
      print ('        Longitude_End: %6.2f'% ( CMEbox_End[1]))
      print ('       Latitude_Start: %6.2f'% ( CMEbox_Start[2]))
      print ('         Latitude_End: %6.2f'% ( CMEbox_End[2]))
      print ('-----------------------------------------')
      FileId=open('CME_AMR.in','w')
      FileId.write("#AMRREGION \n")
      FileId.write("CMEbox              NameRegion \n")
      FileId.write(" \n")
      FileId.write("#END \n")
      FileId.close()
   #For comparison, make magnetogram of a flux rope field
   FileId=open('RunFRM','w')
   FileId.write('%-3d \n'%Long0)
   if IsUniformLat :
      FileId.write('uniform latitude \n')
   else:
       FileId.write('sin(latitude) \n')
   FileId.close()
   FileId=open('RunFRM','r')
   subprocess.call('./FRMAGNETOGRAM.exe',stdin=FileId)
   FileId.close()
   
   nParam = 8
   Param_I = np.zeros(nParam)
   Param_I[0:8] = [Long0,LongEarth,LonPosIndex,LatPosIndex,LonNegIndex,
                   LatNegIndex,iLonAR,iLatAR]
   FileId = open('AfterGLSETUP.out','w')
    
   FileId.write('After GLSETUP: Br[Gauss]'+'\n')
   FileId.write(
      '       0     '+str(Time)+'     2      %2d       3 \n'% nParam)
   FileId.write('      '+str(nLong)+'     '+str(nLat)+'\n')
   FileId.write(
      ' {0:5.1f} {1:5.1f} {2:5.1f} {3:5.1f} {4:5.1f} {5:5.1f} {6:5.1f} {7:5.1f}'.format(Long0,LongEarth,LonPosIndex,LatPosIndex,LonNegIndex,LatNegIndex,iLonAR,iLatAR))

   FileId.write('\n')
   FileId.write(
      'Longitude Latitude Br PMap NMap Long0 LongEarth xP yP xN yN xC yC \n')
   
   for k in np.arange(nLat):
      for l in np.arange(nLong):
         FileId.write("{0:6.1f} {1:6.1f} {2:14.6e} {3:14.6e} {4:14.6e} \n".format((180./cPi)*Long_I[l],(180./cPi)*Lat_I[k],max([-BMax,min([BMax,Br_C[k,l]])]),PSizeMap_C[k,l],NSizeMap_C[k,l]))
    
   FileId.close()

   return(nLong,nLat,nParam,Param_I,Long_I,Lat_I,Br_C,PSizeMap_C,NSizeMap_C)
