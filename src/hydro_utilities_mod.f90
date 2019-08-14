module hydro_utilities_mod
!---------------------------------------------------------------------------------
! Purpose:
!
! This module contains hydrodynamic utility subroutines in the model
!
!---------------------------------------------------------------------------------
   use data_type_mod

   implicit none
   public
   ! model control constants
   integer, parameter :: MAXITER = 100
   integer, parameter :: adaptive_mode = 101, fixed_mode = 102
   real(kind=8), parameter :: TOL_REL = 1.d-6
   real(kind=8), parameter :: INFTSML = 1.d-30
   ! physical constants 
   real(kind=8), parameter :: PI = 3.14159265d+0
   real(kind=8), parameter :: e = 2.71828183d+0
   real(kind=8), parameter :: Roul = 1028.0
   real(kind=8), parameter :: Roua = 1.225
   real(kind=8), parameter :: Karman = 0.41
   real(kind=8), parameter :: G = 9.8

contains
   subroutine Norm(matrix, dir, values)
      implicit none
      real(kind=8), intent(in)  :: matrix(:,:)
      integer, intent(in)   :: dir
      real(kind=8), intent(out) :: values(:)
      integer :: ii, nn

      nn = size(matrix,dir)
      if (dir==1) then
         do ii = 1, nn, 1
            values(ii) = max( abs(minval(matrix(ii,:))), &
               abs(maxval(matrix(ii,:))) )
         end do
      else if (dir==2) then
         do ii = 1, nn, 1
            values(ii) = max( abs(minval(matrix(:,ii))), &
               abs(maxval(matrix(:,ii))) )
         end do
      end if
   end subroutine

   subroutine Minimum(matrix, dir, values)
      implicit none
      real(kind=8), intent(in) :: matrix(:,:)
      integer, intent(in) :: dir
      real(kind=8), intent(out) :: values(:)
      integer :: ii, nn

      nn = size(matrix,dir)
      if (dir==1) then
         do ii = 1, nn, 1
            values(ii) = minval(matrix(ii,:))
         end do
      else if (dir==2) then
         do ii = 1, nn, 1
            values(ii) = minval(matrix(:,ii))
         end do
      end if
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Solve non-linear equation using Brent's method.
   ! https://rosettacode.org/wiki/Roots_of_a_function#Brent.27s_Method
   !
   !------------------------------------------------------------------------------
   subroutine NonLRBrents(NonLREQ, coefs, xbounds, tol, root)
      implicit none
      external :: NonLREQ
      real(kind=8), intent(in) :: coefs(:)
      real(kind=8), intent(in) :: xbounds(2)
      real(kind=8), intent(in) :: tol
      real(kind=8), intent(out) :: root
      real(kind=8) :: xa, xb, ya, yb
      real(kind=8) :: xc, yc, xd, ys
      integer :: iter
      logical :: mflag

      xa = xbounds(1)
      xb = xbounds(2)
      call NonLREQ(xa, coefs, ya)
      call NonLREQ(xb, coefs, yb)
      if (abs(ya)<1d-3 .or. abs(yb)<1d-3) then
         ! root at the boundary
         if (abs(ya)<=abs(yb)) then
            root = xa
         else
            root = xb
         end if
      else if (ya*yb>0) then
         ! root not available but set one
         if (abs(ya)<=abs(yb)) then
            root = xa
         else
            root = xb
         end if
         print *, "Root is not within xbounds"
      else
         if (abs(ya)<abs(yb)) then
            call swap(xa, xb)
            call swap(ya, yb)
         end if
         xc = xa
         yc = ya
         xd = 0.0 ! xd only used if mflag=false, not on first iteration
         mflag = .True.
         do iter = 1, MAXITER, 1
            ! stop if converged on root or error is less than tolerance
            if (abs(xb-xa)<tol) then
               exit
            end if
            if (ya /= yc .and. yb /= yc) then
               ! use inverse qudratic interpolation
               root = xa*yb*yc/((ya-yb)*(ya-yc)) + &
                  xb*ya*yc/((yb-ya)*(yb-yc)) + xc*ya*yb/((yc-ya)*(yc-yb))
            else
               ! secant method
               root = xb - yb*(xb-xa)/(yb-ya)
            end if
            ! check to see whether we can use the faster converging quadratic
            ! && secant methods or if we need to use bisection
            if ( ( root<(3.0*xa+xb)*0.25 .or. root>xb ) .or. &
                  ( mflag .and. abs(root-xb)>=abs(xb-xc)*0.5 ) .or. &
                  ( (.NOT. mflag) .and. abs(root-xb)>=abs(xc-xd)*0.5 ) .or. &
                  ( mflag .and. abs(xb-xc)<tol ) .or. &
                  ( (.NOT. mflag) .and. abs(xc-xd)<tol ) ) then
               ! bisection method
               root = 0.5 * (xa + xb)
               mflag = .True.
            else
               mflag = .False.
            end if
            call NonLREQ(root, coefs, ys)
            xd = xc  ! first time xd is being used
            xc = xb  ! set xc equal to upper bound
            yc = yb
            ! update the bounds
            if (ya*ys<0) then
               xb = root
               yb = ys
            else
               xa = root
               ya = ys
            end if
            if (abs(ya)<abs(yb)) then
               call swap(xa, xb)
               call swap(ya, yb)
            end if
         end do
      end if
   end subroutine

   subroutine swap(a, b)
      implicit none
      real(kind=8), intent(inout) :: a
      real(kind=8), intent(inout) :: b
      real(kind=8) :: c

      c = a
      a = b
      b = c
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Slope limiter for the 1D Finite Volume Semi-discrete Kurganov and
   !          Tadmor (KT) central scheme.
   !
   !------------------------------------------------------------------------------
   subroutine FVSKT_Superbee(uhydro, phi)
      implicit none
      real(kind=8), intent(in) :: uhydro(:,:)
      real(kind=8), intent(out) :: phi(:,:)
      real(kind=8) :: rr(size(uhydro,2))
      integer :: ii, NX

      NX = size(uhydro,1)
      do ii = 1, NX, 1
         if (ii==1 .or. ii==NX) then
            phi(ii,:) = 0.0d0
         else
            rr = (uhydro(ii,:)-uhydro(ii-1,:))/(uhydro(ii+1,:)-uhydro(ii,:))
            phi(ii,:) = max(0.0,min(2.0*rr,1.0),min(rr,2.0))
         end if
      end do
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Calculate cell edge state variables.
   !
   !------------------------------------------------------------------------------
   subroutine FVSKT_celledge(uhydro, phi, uhydroL, uhydroR)
      implicit none
      real(kind=8), intent(in) :: uhydro(:,:)
      real(kind=8), intent(in) :: phi(:,:)
      real(kind=8), intent(out) :: uhydroL(:,:)
      real(kind=8), intent(out) :: uhydroR(:,:)
      real(kind=8) :: duhydro(size(uhydro,2))
      integer :: ii, NX

      NX = size(uhydro,1)
      do ii = 1, NX, 1
         if (ii==1 .or. ii==NX) then
            uhydroL(ii,:) = uhydro(ii,:)
            uhydroR(ii,:) = uhydro(ii,:)
         else
            duhydro = 0.5*phi(ii,:)*(uhydro(ii+1,:)-uhydro(ii,:))
            uhydroL(ii,:) = uhydro(ii,:) - duhydro
            uhydroR(ii,:) = uhydro(ii,:) + duhydro
         end if
      end do
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Performs a binary search of a sorted one-dimensional array for a
   !          specified element.
   !
   !------------------------------------------------------------------------------
   subroutine BinarySearch(array, obj, idx)
      implicit none
      real(kind=8), intent(in) :: array(:)
      real(kind=8), intent(in) :: obj
      integer, intent(out) :: idx
      integer :: middle, first, last
      logical :: ascend

      first = 1
      last = size(array)
      ascend = (array(first)<array(last))
      do while (last>first)
         middle = (first+last)/2
         if (array(middle)==obj) then
            last = middle
            exit
         else if (array(middle)<obj) then
            if (ascend) then
               first = middle + 1
            else
               last = middle
            end if
         else
            if (ascend) then
               last = middle
            else
               first = middle + 1
            end if
         end if
      end do
      idx = last - 1
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Calculate ground roughness and bottom shear stress
   ! Chézy's coefficient vs manning's coefficient: Cz = h^(1/6) / n
   ! Chézy's coefficient vs Darcy-Weisbach friction factor: Cz = sqrt(8*G/f)
   ! From an empirical equation of Froehlich (2012; J. Irrigation and Drainage
   ! Engineering), Cz0 = sqrt(G)*(5.62*log10(h/1.7/D50) + 6.25
   ! From van Rijn's formula, Cz0 = 18*log10(12*h/3/D90)
   !
   !------------------------------------------------------------------------------
   subroutine UpdateGroundRoughness(forcings, h, params, Cz)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(out) :: Cz(:)
      real(kind=8), parameter :: Cb = 2.5d-3    ! bed drag coefficient (unitless)
      real(kind=8) :: cD0, ScD, alphaA, alphaD
      real(kind=8) :: betaA, betaD
      real(kind=8) :: asb, dsb, cD
      integer :: nx, ii

      nx = size(h)
      do ii = 1, nx, 1
         cD0 = params%cD0(forcings%pft(ii))
         ScD = params%ScD(forcings%pft(ii))
         alphaA = params%alphaA(forcings%pft(ii))
         betaA = params%betaA(forcings%pft(ii))
         alphaD = params%alphaD(forcings%pft(ii))
         betaD = params%betaD(forcings%pft(ii))
         asb = alphaA * forcings%Bag(ii)**betaA
         dsb = alphaD * forcings%Bag(ii)**betaD
         cD = cD0 + ScD * forcings%Bag(ii)
         Cz(ii) = params%Cz0*sqrt(2.0/(cD*asb*h(ii)+2.0*(1.0-asb*dsb)*Cb))
      end do
   end subroutine

   subroutine UpdateShearStress(forcings, h, U, Hwav, Uwav, params, tau)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: U(:)
      real(kind=8), intent(in) :: Hwav(:)
      real(kind=8), intent(in) :: Uwav(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(out) :: tau(:)
      real(kind=8) :: fcurr, fwave
      real(kind=8) :: tau_curr, tau_wave
      integer :: ii, nx

      nx = size(h)
      do ii = 1, nx, 1
         if (h(ii)>0) then
            ! bottom shear stress by currents
            fcurr = 0.24/(log(4.8*h(ii)/params%d50))**2
            tau_curr = 0.125*Roul*fcurr*U(ii)**2
            ! bottom shear stress by wave
            fwave = 1.39*(6.0*Uwav(ii)*forcings%Twav/PI/params%d50)**(-0.52)
            tau_wave = 0.5*fwave*Roul*Uwav(ii)**2
            tau(ii) = tau_curr*(1.0+1.2*(tau_wave/(tau_curr+tau_wave))**3.2)
         else
            tau(ii) = 0.0d0
         end if
      end do
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Calculate wave number.
   !          UpdateWaveNumber2() is much more efficient but less accurate.
   !
   !------------------------------------------------------------------------------
   subroutine WaveNumberEQ(kwav, coefs, fval)
      implicit none
      real(kind=8), intent(in) :: kwav
      real(kind=8), intent(in) :: coefs(2)
      real(kind=8), intent(out) :: fval
      real(kind=8) :: sigma, T, h

      T = coefs(1)
      h = coefs(2)
      sigma = 2.0*PI/T
      fval = sqrt(G*kwav*tanh(kwav*h)) - sigma
   end subroutine

   subroutine UpdateWaveNumber(forcings, h, kwav)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(out) :: kwav(:)
      real(kind=8) :: coefs(2), xbounds(2)
      real(kind=8) :: sigma
      integer :: ii, nx

      nx = size(h)
      sigma = 2.0*PI/forcings%Twav     ! wave frequency (dispersion)
      do ii = 1, nx, 1
         if (h(ii)>0) then
            xbounds = (/sigma**2/G, sigma/sqrt(G*h(ii))/)
            coefs = (/forcings%Twav, h(ii)/)
            call NonLRBrents(WaveNumberEQ, coefs, xbounds, 1d-4, kwav(ii))
         else
            kwav(ii) = 0.0d0
         end if
      end do
   end subroutine

   subroutine UpdateWaveNumber2(forcings, h, kwav)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(out) :: kwav(:)
      real(kind=8) :: coefs(2), xbounds(2)
      real(kind=8) :: sigma
      integer :: ii, nx

      nx = size(h)
      sigma = 2.0*PI/forcings%Twav     ! wave frequency (dispersion)
      if (h(1)>0) then
         xbounds = (/sigma**2/G, sigma/sqrt(G*h(1))/)
         coefs = (/forcings%Twav, h(1)/)
         call NonLRBrents(WaveNumberEQ, coefs, xbounds, 1d-4, kwav(1))
         do ii = 2, nx, 1
            if (h(ii)>0) then
               kwav(ii) = kwav(1)*sqrt(h(1)/max(0.1,h(ii)))
            else
               kwav(ii) = 0.0d0
            end if
         end do
      else
         kwav = 0.0d0
      end if
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Calculate wave depth breaking possibility.
   !          UpdateWaveBrkProb2() is much more efficient but less accurate.
   !
   !------------------------------------------------------------------------------
   subroutine BreakProbEQ(Qb, coefs, fval)
      implicit none
      real(kind=8), intent(in) :: Qb
      real(kind=8), intent(in) :: coefs(2)
      real(kind=8), intent(out) :: fval
      real(kind=8) :: Hrms, Hmax

      Hmax = coefs(1)
      Hrms = coefs(2)
      fval = (1-Qb)/log(Qb) + (Hrms/Hmax)**2
   end subroutine 

   subroutine UpdateWaveBrkProb(h, Hwav, params, Qb)
      implicit none
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: Hwav(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(out) :: Qb(:)
      real(kind=8) :: xbounds(2), coefs(2)
      real(kind=8) :: Hrms, Hmax
      integer :: ii, nx

      nx = size(h)
      do ii = 1, nx, 1
         if (h(ii)>0) then
            Hmax = params%fr * h(ii)
            Hrms = Hwav(ii)
            xbounds = (/1d-10, 1.0-1d-10/)
            coefs = (/Hmax, Hrms/)
            call NonLRBrents(BreakProbEQ, coefs, xbounds, 1d-4, Qb(ii))
         else
            Qb(ii) = 1.0d0
         end if
      end do
   end subroutine

   subroutine UpdateWaveBrkProb2(h, Hwav, params, rawQb, Qb)
      implicit none
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: Hwav(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(in) :: rawQb(:)
      real(kind=8), intent(out) :: Qb(:)
      real(kind=8) :: fHrms
      integer :: ii, nx, nQb, idx

      nQb = size(rawQb)
      nx = size(h)
      do ii = 1, nx, 1
         if (h(ii)>0) then
            fHrms = Hwav(ii) / (params%fr*h(ii))
            if (fHrms<=rawQb(1)) then
               Qb(ii) = 0.0d0
            else if (fHrms>=rawQb(nQb)) then
               Qb(ii) = 1.0d0
            else
               call BinarySearch(rawQb, fHrms, idx)
               Qb(ii) = 0.01*DBLE(idx) - 0.005
            end if
         else
            Qb(ii) = 1.0d0
         end if
      end do
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: Calculate wave sources and sinks.
   !
   !------------------------------------------------------------------------------
   subroutine UpdateWaveGeneration(forcings, h, kwav, Ewav, Swg)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: kwav(:)
      real(kind=8), intent(in) :: Ewav(:)
      real(kind=8), intent(out) :: Swg(:)
      real(kind=8), parameter :: Cd = 1.3d-3    ! drag coefficient for U10
      real(kind=8) :: sigma, alpha, beta
      real(kind=8) :: U10, Twav
      integer :: ii, nx

      nx = size(h)
      U10 = forcings%U10
      Twav = forcings%Twav
      sigma = 2.0*PI/Twav
      do ii = 1, nx, 1
         if (h(ii)>0) then
            alpha = 80.0*sigma*(Roua*Cd*U10/Roul/G/kwav(ii))**2
            beta = 5.0*Roua/Roul/Twav*(U10*kwav(ii)/sigma-0.9)
            Swg(ii) = alpha + beta * Ewav(ii)
         else
            Swg(ii) = 0.0d0
         end if
      end do
   end subroutine

   subroutine UpdateWaveBtmFriction(forcings, h, Hwav, kwav, Ewav, &
                                    Qb, params, Sbf)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: Hwav(:)
      real(kind=8), intent(in) :: kwav(:)
      real(kind=8), intent(in) :: Ewav(:)
      real(kind=8), intent(in) :: Qb(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(out) :: Sbf(:)
      real(kind=8) :: Cf, Twav
      integer :: ii, nx

      nx = size(h)
      Twav = forcings%Twav
      do ii = 1, nx, 1
         if (h(ii)>0) then
            Cf = 2.0*params%cbc*PI*Hwav(ii)/Twav/sinh(kwav(ii)*h(ii))
            Sbf(ii) = (1-Qb(ii))*2.0*Cf*kwav(ii)*Ewav(ii)/ &
               sinh(2.0*kwav(ii)*h(ii))
         else
            Sbf(ii) = 0.0d0
         end if
      end do
   end subroutine

   subroutine UpdateWaveWhiteCapping(forcings, Ewav, Swc)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: Ewav(:)
      real(kind=8), intent(out) :: Swc(:)
      real(kind=8), parameter :: gammaPM = 4.57d-3
      real(kind=8), parameter :: m = 2.0d0
      real(kind=8), parameter :: cwc = 3.33d-5
      real(kind=8) :: sigma

      sigma = 2.0*PI/forcings%Twav
      Swc = cwc*sigma*((Ewav*(sigma**4)/G**2/gammaPM)**m)*Ewav
   end subroutine

   subroutine UpdateWaveDepthBrking(forcings, h, Hwav, kwav, Ewav, &
                                    Qb, params, Sbrk)
      implicit none
      type(ForcingData), intent(in) :: forcings
      real(kind=8), intent(in) :: h(:)
      real(kind=8), intent(in) :: Hwav(:)
      real(kind=8), intent(in) :: kwav(:)
      real(kind=8), intent(in) :: Ewav(:)
      real(kind=8), intent(in) :: Qb(:)
      type(ModelParams), intent(in) :: params
      real(kind=8), intent(out) :: Sbrk(:)
      real(kind=8), parameter :: Cd = 1.3d-3    ! drag coefficient for U10
      real(kind=8) :: sigma, Hmax, alpha
      real(kind=8) :: U10, Twav
      integer :: ii, nx

      nx = size(h)
      Twav = forcings%Twav
      U10 = forcings%U10
      sigma = 2.0*PI/Twav
      do ii = 1, nx, 1
         if (h(ii)>0) then
            Hmax = params%fr * h(ii)
            alpha = 80.0*sigma*(Roua*Cd*U10/Roul/G/kwav(ii))**2
            Sbrk(ii) = 2.0*alpha/Twav*Qb(ii)*((Hmax/Hwav(ii))**2)*Ewav(ii)
         else
            Sbrk(ii) = 0.0d0
         end if
      end do
   end subroutine

   !------------------------------------------------------------------------------
   !
   ! Purpose: The 4th-order time step variable Runge-Kutta-Fehlberg method 
   !
   !------------------------------------------------------------------------------
   subroutine RK4Fehlberg(odeFunc, mem, invars, mode, tol, outvars, &
                          curstep, nextstep, outerr)
      implicit none
      external :: odeFunc
      type(RungeKuttaCache) :: mem     ! memory caches
      real(kind=8), intent(in) :: invars(:,:)
      integer, intent(in) :: mode
      real(kind=8), intent(in) :: tol(:)
      real(kind=8), intent(out) :: outvars(:,:)
      real(kind=8), intent(inout) :: curstep
      real(kind=8), intent(out) :: nextstep
      integer, intent(out) :: outerr
      ! local variables
      real(kind=8), dimension(size(tol)) :: dy, rdy, dyn
      real(kind=8), dimension(size(tol)) :: rel_tol
      real(kind=8), dimension(size(tol)) :: abs_rate
      real(kind=8), dimension(size(tol)) :: rel_rate
      real(kind=8) :: step, rate, delta
      logical  :: isLargeErr, isConstrainBroken
      integer  :: iter, ii, m

      m = size(tol)
      isLargeErr = .True.
      isConstrainBroken = .False.
      outerr = 0
      step = curstep
      iter = 1
      rel_tol = TOL_REL
      call odeFunc(invars, mem%K1)
      do while (isLargeErr .or. isConstrainBroken)
         if (iter>MAXITER) then
            outerr = 1
            return
         end if
         curstep = step
         mem%interim = invars + step*0.25*mem%K1
         call odeFunc(mem%interim, mem%K2)
         mem%interim = invars + step*(0.09375*mem%K1+0.28125*mem%K2)
         call odeFunc(mem%interim, mem%K3)
         mem%interim = invars + step*(0.87938*mem%K1-3.27720*mem%K2+ &
            3.32089*mem%K3)
         call odeFunc(mem%interim, mem%K4)
         mem%interim = invars + step*(2.03241*mem%K1-8.0*mem%K2+ &
            7.17349*mem%K3-0.20590*mem%K4)
         call odeFunc(mem%interim, mem%K5)
         mem%nxt4th = invars + step*(0.11574*mem%K1+0.54893*mem%K3+ &
            0.53533*mem%K4-0.2*mem%K5)
         if (mode==fixed_mode) then
            nextstep = step
            outvars = mem%nxt4th
            return
         end if
         mem%interim = invars + step*(-0.29630*mem%K1+2.0*mem%K2- &
            1.38168*mem%K3+0.45297*mem%K4-0.275*mem%K5)
         call odeFunc(mem%interim, mem%K6)
         mem%nxt5th = invars + step*(0.11852*mem%K1+0.51899*mem%K3+ &
            0.50613*mem%K4-0.18*mem%K5+0.03636*mem%K6)
         mem%rerr = (mem%nxt4th - mem%nxt5th) / (mem%nxt4th + INFTSML)
         call Norm(mem%rerr, 2, rdy)
         call Norm(mem%nxt4th-mem%nxt5th, 2, dy)
         call Minimum(mem%nxt4th, 2, dyn)
         ! check whether solution is converged
         isLargeErr = .False.
         isConstrainBroken = .False.
         do ii = 1, m, 1
            if (dy(ii)>tol(ii) .and. rdy(ii)>rel_tol(ii)) then
               isLargeErr = .True.
            end if
            if (dyn(ii)<-100*tol(ii)) then
               isConstrainBroken = .True.
            end if
         end do
         ! update time step
         if (isConstrainBroken) then
            step = 0.5*step
         else
            abs_rate = tol / (dy + INFTSML)
            rel_rate = rel_tol / (rdy + INFTSML)
            rate = max(minval(abs_rate), minval(rel_rate))
            delta = 0.84*rate**0.25
            if (delta<=0.1) then
               step = 0.1*step
            else if (delta>=4.0) then
               step = 4.0*step
            else
               step = delta*step
            end if
         end if
         iter = iter + 1
      end do
      nextstep = step
      outvars = mem%nxt4th
   end subroutine

end module hydro_utilities_mod