!====================================================
!  vector.f90
!  Minimal 3-D vector container + math
!====================================================
module vector_mod
    implicit none
 
    type :: vector3_t
       real :: x, y, z
    end type vector3_t
 contains

    type(vector3_t) function plus(a, b) result(c)
       type(vector3_t), intent(in) :: a, b
       c%x = a%x + b%x
       c%y = a%y + b%y
       c%z = a%z + b%z
    end function plus

    real function magnitude(v) result(mag)
       type(vector3_t), intent(in) :: v
       mag = sqrt(v%x*v%x + v%y*v%y + v%z*v%z)
    end function magnitude
 
    real function inner_product(a, b) result(d)
       type(vector3_t), intent(in) :: a, b
       d = a%x*b%x + a%y*b%y + a%z*b%z
    end function inner_product
 
    type(vector3_t) function cross_product(a, b) result(c)
       type(vector3_t), intent(in) :: a, b
       c%x = a%y*b%z - a%z*b%y
       c%y = a%z*b%x - a%x*b%z
       c%z = a%x*b%y - a%y*b%x
    end function cross_product
 end module vector_mod
 