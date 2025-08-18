!====================================================
!  physics.f90
!  Simple physics utilities (depends on several mods)
!====================================================
module physics_mod
   use constants_mod, only : constants
   use geometry_mod
   use vector_mod
   implicit none
contains
   real function force_pressure(p, r) result(F)
      real, intent(in) :: p      ! pressure (Pa)
      real, intent(in) :: r      ! piston radius (m)
      F = p * area_circle(r)
   end function force_pressure

   real function kinetic_energy(m, v) result(ke)
      real, intent(in) :: m      ! mass (kg)
      real, intent(in) :: v      ! speed (m s⁻¹)
      ke = 0.5 * m * v**2
   end function kinetic_energy

   real function potential_energy(m, h) result(pe)
      real, intent(in) :: m      ! mass (kg)
      real, intent(in) :: h      ! height (m)
      pe = m * constants%g * h
   end function potential_energy
end module physics_mod
