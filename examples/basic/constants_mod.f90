!====================================================
!  constants.f90
!  Basic mathematical / physical constants
!====================================================
module constants_mod
    implicit none
 
    ! Scalar constants
    real, parameter :: pi = 3.141592653589793
 
    ! Simple “struct” holding a few more constants
    type :: constants_t
       real :: ln2   = 0.693147180559945
       real :: e     = 2.718281828459045
       real :: g     = 9.80665              ! standard gravity (m s⁻²)
    end type constants_t
 
    ! One global instance
    type(constants_t), save :: constants = constants_t()
 end module constants_mod
 