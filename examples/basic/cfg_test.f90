!=========================================================
!  Module: cfg_test_mod
!  Purpose:
!    • Provide a rich mix of control-flow patterns
!    • Exercise common side-effect categories
!  Standard: Fortran 90 (obsolescent features kept intentionally)
!=========================================================
module CFG
    implicit none
    integer, save :: counter = 0      ! global state (side-effect target)
 
 contains
 !-------------------------------------------------------------------
 !  1) Pure, side-effect-free function (baseline for comparison)
 !-------------------------------------------------------------------
    pure function add(a, b) result(c)
       integer, intent(in) :: a, b
       integer             :: c
       c = a + b
    end function add
 
 !-------------------------------------------------------------------
 !  2) Recursive function with early RETURN and STOP (stdout I/O)
 !-------------------------------------------------------------------
    recursive function factorial(n) result(f)
       integer, intent(in) :: n
       integer             :: f
       if (n < 0) then
          print *, "Negative factorial!"
          stop 1                           ! program-level side effect
       else if (n == 0) then
          f = 1
          return                           ! early exit
       else
          f = n * factorial(n - 1)         ! recursion edge
       end if
    end function factorial
 
 !-------------------------------------------------------------------
 !  3) Loop construct using CYCLE / EXIT  (modifies global variable)
 !-------------------------------------------------------------------
    subroutine loop_demo(limit)
       integer, intent(in) :: limit
       integer :: i
       counter = 0
       do i = 1, limit
          if (mod(i, 2) == 0) then
             cycle                       ! forward jump to loop test
          else if (i > 10) then
             exit                        ! break out of loop
          end if
          counter = counter + 1          ! visible global mutation
       end do
       print *, "Odd values counted:", counter
    end subroutine loop_demo
 
 !-------------------------------------------------------------------
 !  4) Legacy jumps: computed GOTO + arithmetic IF
 !     (both are obsolescent but still valid F90)
 !-------------------------------------------------------------------
    subroutine goto_demo(idx)
       integer, intent(in) :: idx
       integer :: j
       j = idx
 
       ! ---- computed GOTO ------------------------------------------------
       goto (10, 20, 30, 40) j           ! multi-way branch
 10    print *, "branch 1"; goto 99
 20    print *, "branch 2"; goto 99
 30    print *, "branch 3"; goto 99
 40    print *, "branch 4"
 99    continue                          ! join point
 
       ! ---- arithmetic IF -------------------------------------------------
       if (j - 2) 110, 120, 130          ! three-way branch
 110   print *, "j < 2";  goto 140
 120   print *, "j == 2"; goto 140
 130   print *, "j > 2"
 140   continue
    end subroutine goto_demo
 
 !-------------------------------------------------------------------
 !  5) File I/O: OPEN → WRITE → CLOSE
 !-------------------------------------------------------------------
    subroutine file_io_demo(filename, n)
       character(len=*), intent(in) :: filename
       integer,          intent(in) :: n
       integer :: u, i
       u = 10
       open(unit=u, file=filename, status="replace", action="write")
       do i = 1, n
          write(u, "(I0)") i
       end do
       close(u)
    end subroutine file_io_demo
 
 !-------------------------------------------------------------------
 !  6) Heap side effects: ALLOCATE / DEALLOCATE
 !-------------------------------------------------------------------
    subroutine alloc_demo(n)
       integer, intent(in) :: n
       integer :: i
       real, allocatable   :: arr(:)
       allocate(arr(n))
       arr = [(real(i), i = 1, n)]
       print *, "first element =", arr(1)
       deallocate(arr)
    end subroutine alloc_demo
 
 !-------------------------------------------------------------------
 !  7) Elemental impure procedure (in-place mutation)
 !-------------------------------------------------------------------
    elemental subroutine impure_increment(x)
       integer, intent(inout) :: x
       x = x + 1
    end subroutine impure_increment
 
 !-------------------------------------------------------------------
 !  8) Structured SELECT CASE with default arm
 !-------------------------------------------------------------------
    subroutine branch_io(option)
       integer, intent(in) :: option
       select case (option)
       case (1)
          print *, "Option 1 selected"
       case (2:4)
          print *, "Option between 2 and 4"
       case default
          print *, "Other option"
       end select
    end subroutine branch_io
 
 end module CFG
 