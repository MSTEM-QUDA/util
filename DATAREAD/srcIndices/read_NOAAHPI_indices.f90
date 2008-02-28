!==============================================================================

subroutine read_NOAAHPI_Indices(iOutputError)

  use ModKind
  use ModIndices
  use ModTimeConvert, ONLY: time_real_to_int

  implicit none

  integer, intent(out) :: iOutputError

  integer :: ierror, year, month, i, j, npts, npts_hpi, k
  integer :: idir, input_coor_system, iday 
  logical :: done, found

  ! One line of input
  character (len=100) :: line

  real, dimension(6,MaxIndicesEntries) :: tmp

  real (Real8_), dimension(MaxIndicesEntries) :: ut_new, ut_keep, ut_tmp
  real, dimension(MaxIndicesEntries)   :: data_new, data_keep, data_tmp

  real :: xgse, ygse, zgse, xgsm, ygsm, zgsm
  real (Real8_) :: time_now

  integer, dimension(7) :: itime

  integer, external :: jday

  iOutputError = 0
  !-------------------------------------------------------------------------
  call init_mod_indices

  open(LunIndices_, file=NameOfIndexFile, status="old", iostat = ierror)

  if (ierror.ne.0) then
     iOutputError = 1
     return
  endif

  done = .false.

  npts_hpi = 0

  do while (.not.done)

     read(LunIndices_,'(a)', iostat = ierror ) line
     if (ierror.ne.0) done = .true.

     if(index(line,'Normalizing factor')>0)then
        call read_values
        call merge_hpi_data
     endif

  enddo

  close(LunIndices_)

  if (npts_hpi > 0) then

     tmp = 0.0

     do i=1,npts_hpi
        call time_real_to_int(ut_keep(i), itime)
        tmp(1:5,i) = itime(1:5)
        tmp(6,i) = data_keep(i)
     enddo

     call Insert_into_Indices_Array(tmp, hpi_)

     nIndices_V(hpi_norm_) = nIndices_V(hpi_) 

     do i=1,nIndices_V(hpi_norm_)

        IndexTimes_TV(i,hpi_norm_) = IndexTimes_TV(i,hpi_) 

        if (Indices_TV(i,hpi_) > 0) then
           Indices_TV(i,hpi_norm_) = &
                2.09 * ALOG(Indices_TV(i,hpi_)) * 1.0475
        endif
     enddo

  endif

contains 

  subroutine read_values

    logical :: done_inner
    real :: missing, missingPlusTol, missingMinusTol
    integer :: iYear

    done_inner = .false.

    tmp = 0.0

    missing = -1.0e32

    read(LunIndices_,'(a)', iostat = ierror ) line
    read(LunIndices_,'(i4)', iostat = ierror ) iYear

    if (ierror.eq.0) then

       done_inner = .false.

       i = 1

       do while (.not.done_inner)

          tmp(1,i) = iYear
          tmp(2,i) = 1
          read(LunIndices_,'(a10,f3.0,f2.0,f2.0,f8.1)', iostat = ierror ) &
               line,tmp(3:6,i)

          if (ierror /= 0) then
             done_inner = .true.
          else
             i = i + 1
          endif

       enddo

       npts = i-1

    end if

  end subroutine read_values

  subroutine merge_hpi_data

    use ModTimeConvert, ONLY: time_int_to_real

    itime = 0

    do i=1,npts 
       itime(1:5) = tmp(1:5,i)
       call time_int_to_real(itime, ut_new(i))
       data_new(i) = tmp(6,i)
    enddo

    if (npts_hpi == 0) then
       npts_hpi = npts
       ut_keep(1:npts) = ut_new(1:npts)
       data_keep(1:npts) = data_new(1:npts)
    else
              
       ut_tmp = ut_keep
       data_tmp = data_keep

       ut_keep = 0.0
       data_keep = 0.0

       j = 1
       i = 1
       k = 1

       do while (i <= npts .or. j <= npts_hpi)

          if (i > npts) then
             ut_keep(k) = ut_tmp(j) 
             data_keep(k) = data_tmp(j) 
             k = k + 1
             j = j + 1
          else
             if (j > npts_hpi) then
                ut_keep(k) = ut_new(i) 
                data_keep(k) = data_new(i) 
                k = k + 1
                i = i + 1
             else
                if (ut_tmp(j) < ut_new(i)) then
                   ut_keep(k) = ut_tmp(j) 
                   data_keep(k) = data_tmp(j) 
                   k = k + 1
                   j = j + 1
                else
                   ut_keep(k) = ut_new(i) 
                   data_keep(k) = data_new(i) 
                   k = k + 1
                   i = i + 1
                endif
             endif
          endif

       enddo

       npts_hpi = npts_hpi + npts

    endif

  end subroutine merge_hpi_data


end subroutine read_NOAAHPI_Indices

