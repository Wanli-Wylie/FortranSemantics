!====================================================
!  Module: geometry_mod
!  Depends on constants_mod
!  Geometric helper routines
!====================================================
module geometry_mod
    use constants_mod
    implicit none
 contains
    !-------------------------------------------------
    !  Return the area of a circle of given radius
    !-------------------------------------------------
    real function area_circle(radius) result(a)
       real, intent(in) :: radius
       a = pi * radius**2
    end function area_circle
 end module geometry_mod
 