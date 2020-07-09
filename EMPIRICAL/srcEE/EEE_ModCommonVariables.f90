!  Copyright (C) 2002 Regents of the University of Michigan, portions used with permission 
!  For more information, see http://csem.engin.umich.edu/tools/swmf
module EEE_ModCommonVariables

  use ModConst
  use ModMpi
  use ModUtilities, ONLY: CON_stop

  implicit none
  save

  !\
  ! Named indices for directions
  !/
  integer, parameter :: x_=1,y_=2,z_=3

  !\
  ! prefix for writing EEE output
  !/
  character(len=5), parameter :: prefix='EEE: '

  !\
  ! My processor number
  !/
  integer :: iProc = 0

  !\
  ! Physics variables global to EEE
  !/
  real :: g = 5./3., inv_g = 3./5., gm1 = 2./3., inv_gm1 = 3./2.
  real :: Gbody = -cGravitation*mSun*cProtonMass/(cBoltzmann*1.5e6)

  ! Named indexes for I/O variable units
  integer, parameter :: nIoUnit = 15

  integer, parameter :: UnitX_           = 1
  integer, parameter :: UnitU_           = 2
  integer, parameter :: UnitRho_         = 3
  integer, parameter :: UnitT_           = 4
  integer, parameter :: UnitN_           = 5
  integer, parameter :: UnitP_           = 6
  integer, parameter :: UnitB_           = 7
  integer, parameter :: UnitRhoU_        = 8
  integer, parameter :: UnitEnergyDens_  = 9
  integer, parameter :: UnitPoynting_    = 10
  integer, parameter :: UnitJ_           = 11
  integer, parameter :: UnitElectric_    = 12
  integer, parameter :: UnitTemperature_ = 13
  integer, parameter :: UnitDivB_        = 14
  integer, parameter :: UnitAngle_       = 15

  ! Conversion between units: e.g. VarSi = VarNo*No2Si_V(UnitVar_)
  ! The following should always be true: No2Si_V*Si2Io_V = No2Io_V
  real, dimension(nIoUnit) :: &
       Io2Si_V, Si2Io_V, Io2No_V, No2Io_V, Si2No_V, No2Si_V


  ! Switch on CME (boundary and/or initial conditions)
  logical:: UseCme = .false.
  
  ! Use Gibbson-Law, Titov-Demoulin, spheromak flux ropes
  logical:: UseGL  = .false., UseTD = .false., UseSpheromak = .false.
  ! Use Titov-Demoulin 2014
  logical:: UseTD14 = .false.

  ! Logicals to add the CMEs
  logical:: DoAddGL = .false., DoAddTD = .false., DoAddSpheromak = .false.
  logical:: DoAddTD14 = .false.

  ! Use shear-flow boundary condition, use arcade magnetic field
  logical:: UseShearFlow = .false., UseArch = .false.

  ! Use CMS nonlinear force free model
  logical:: UseCms = .false.

  ! Add flux rope as an initial condition or apply boundary conditions only
  logical:: DoAddFluxRope = .false.

  ! CME location and orientation
  real :: LongitudeCme = 0.0, LatitudeCme = 0.0, OrientationCme = 0.0
  !
  ! Starting time when the dynamic strapping field starts to be applied 
  ! is stored, to calculate the effect of displacement of moving charges
  real    :: StartTime = -1.0

end module EEE_ModCommonVariables
