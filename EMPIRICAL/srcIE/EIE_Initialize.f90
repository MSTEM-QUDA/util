subroutine EIE_Initialize(iOutputError)

  use ModErrors
  use ModEIE_Interface
  use ModEIEFiles
  use ModIoUnit, only : UnitTmp_

  implicit none

  integer, intent(out) :: iOutputError
  character (len=100)  :: inFileName
  integer              :: iError

  integer, parameter  :: South_ = 1
  integer, parameter  :: North_ = 2

  logical :: IsFound_EFieldModel

  iError = 0
  iOutputError = 0

  IsFound_EFieldModel = .false.

  call set_error_codes

  !\
  ! --------------------------------------------------------------------
  ! Electric Field Models
  ! --------------------------------------------------------------------
  !/

  if (iDebugLevel > 1) &
       write(*,*) "==> Efield Model : ",EIE_NameOfEFieldModel

  if (iDebugLevel > 1) &
       write(*,*) "==> Model Directory : ",EIE_NameOfModelDir

  if (index(EIE_NameOfEFieldModel,'zero') > 0) then
     IsFound_EFieldModel = .true.
  endif

  LunEField_      = UnitTmp_
  LunConductance_ = UnitTmp_

  if (index(EIE_NameOfEFieldModel,'weimer96') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, weimer96_file)
     open(LunEField_,file=weimer96_file,status='old', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',weimer96_file
        iOutputError = ecFileNotFound_
     endif
     call ReadCoef96(LunEField_)
     close(LunEField_)
  endif

  if (index(EIE_NameOfEFieldModel,'weimer01') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, weimer01_file)
     open(LunEField_,file=weimer01_file,status='old',&
          form='unformatted', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',weimer01_file
        iOutputError = ecFileNotFound_
     endif
     call ReadCoef01(LunEField_)
     close(LunEField_)
  endif

!  if (index(EIE_NameOfEFieldModel,'samie') > 0) then
!     IsFound_EFieldModel = .true.
!     call merge_str(EIE_NameOfModelDir, stat_amie_file)
!     open(LunEField_,file=stat_amie_file,status='old', iostat = iError)
!     if (iError /= 0) then
!        write(6,*) 'Error opening file :',stat_amie_file
!        iOutputError = ecFileNotFound_
!     endif
!     call read_amies(LunEField_)
!     close(LunEField_)
!  endif

  if (index(EIE_NameOfEFieldModel,'millstone_hpi') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, millstone_hill_i_file)
     open(LunEField_,file=millstone_hill_i_file,status='old', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',millstone_hill_i_file
        iOutputError = ecFileNotFound_
     endif
     call mhinit(1, LunEField_, 1, iDebugLevel)
     close(LunEField_)
  endif

  if (index(EIE_NameOfEFieldModel,'millstone_imf') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, millstone_hill_s_file)
     open(LunEField_,file=millstone_hill_s_file,status='old', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',millstone_hill_s_file
        iOutputError = ecFileNotFound_
     endif
     call mhinit(2, LunEField_, 1, iDebugLevel)
     close(LunEField_)
  endif

  if (index(EIE_NameOfEFieldModel,'hmr89') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, hepner_maynard_file)
     open(LunEField_,file=hepner_maynard_file,status='old', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',hepner_maynard_file
        iOutputError = ecFileNotFound_
     endif
     call gethmr(LunEField_)
     close(LunEField_)
  endif

  if (index(EIE_NameOfEFieldModel,'izmem') > 0) then
     IsFound_EFieldModel = .true.
     call merge_str(EIE_NameOfModelDir, izmem_file)
     open(LunEField_,file=izmem_file,status='old', iostat = iError)
     if (iError /= 0) then
        write(6,*) 'Error opening file :',izmem_file
        iOutputError = ecFileNotFound_
     endif
     call izinit(LunEField_)
     close(LunEField_)
  endif

  !\
  ! --------------------------------------------------------------------
  ! Conductance Models
  ! --------------------------------------------------------------------
  !/

  if (iDebugLevel > 1) &
       write(*,*) "==> Conductance Model : ",EIE_NameOfAuroralModel

  if (index(EIE_NameOfAuroralModel,'ihp') > 0)  &
       call read_conductance_model(iError)
  if (index(EIE_NameOfAuroralModel,'pem') > 0)  &
       call read_conductance_model(iError)

  if (iDebugLevel > 4) write(*,*) "=====> Back from read conductance"

  if (index(EIE_NameOfEFieldModel,'amie') > 0) then

     IsFound_EFieldModel = .true.

     call AMIE_SetFileName(AMIEFileNorth)
     call readAMIEOutput(North_, .false., iError)

     if (index(AMIEFileSouth,'mirror') > 0) then
        call AMIE_SetFileName(AMIEFileNorth)
        call readAMIEOutput(South_, .true., iError)
     else
        call AMIE_SetFileName(AMIEFileSouth)
        call readAMIEOutput(South_, .false., iError)
     endif

     call AMIE_GetnLats(EIEi_HavenLats)
     call AMIE_GetnMLTs(EIEi_HavenMLTs)
     EIEi_HavenBLKs = 2

     if (iDebugLevel > 1) then
        write(*,*) "=> EIEi_HavenBLKs : ", EIEi_HavenBLKs
        write(*,*) "=> EIEi_HavenLats : ", EIEi_HavenLats
        write(*,*) "=> EIEi_HavenMLTs : ", EIEi_HavenMLTs
     endif

     allocate(EIEr3_HaveLats(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs), &
          stat=iError)
     if (iError /= 0) then
        write(*,*) "Error in allocating array EIEr3_HaveLats in Interface"
        stop
     endif

     allocate(EIEr3_HaveMlts(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs), &
          stat=iError)
     if (iError /= 0) then
        write(*,*) "Error in allocating array EIEr3_HaveMlts in Interface"
        stop
     endif

     allocate(EIEr3_HavePotential(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs), &
          stat=iError)
     if (iError /= 0) then
        write(*,*) "Error in allocating array EIEr3_HavePotential in Interface"
        stop
     endif

     allocate(EIEr3_HaveEFlux(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs), &
          stat=iError)
     if (iError /= 0) then
        write(*,*) "Error in allocating array EIEr3_HaveEFlux in Interface"
        stop
     endif

     allocate(EIEr3_HaveAveE(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs), &
          stat=iError)
     if (iError /= 0) then
        write(*,*) "Error in allocating array EIEr3_HaveAveE in Interface"
        stop
     endif

     call AMIE_GetLats(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs,&
          EIEr3_HaveLats,iError)

     call AMIE_GetMLTs(EIEi_HavenMlts,EIEi_HavenLats,EIEi_HavenBLKs,&
          EIEr3_HaveMLTs,iError)

     return

  endif

  if (.not.IsFound_EFieldModel) then
     iOutputError = ecEFieldModelNotFound_
  endif

  if (iDebugLevel > 3) write(*,*) "====> Done with EIE_Initialize"

end subroutine EIE_Initialize