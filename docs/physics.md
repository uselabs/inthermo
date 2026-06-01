# Physical model

The full datasheet specification is in `src/inthermo/gemini_info.md`; this page
summarises the equations the code solves and how they map onto the modules.

## Governing equation

A 2-D transient heat equation is solved on the conductor cross-section:

$$\rho C_p \frac{\partial T}{\partial t} - \nabla \cdot (k \nabla T) = q(t)$$

The domain has two solid subdomains with distinct, piecewise-constant
properties (mapped as DG-0 fields keyed off the mesh cell tags in
{py:mod}`inthermo.solver`):

| Property | Aluminum (1350-H19) | Steel core (galvanized) |
| :-- | :-- | :-- |
| Thermal conductivity $k$ | 205 W·m⁻¹·K⁻¹ | 50 W·m⁻¹·K⁻¹ |
| Density $\rho$ | 2700 kg·m⁻³ | 7850 kg·m⁻³ |
| Specific heat $C_p$ | 900 J·kg⁻¹·K⁻¹ | 480 J·kg⁻¹·K⁻¹ |

## Heat generation (Joule effect)

Current flows only in the aluminum, so the volumetric source is

$$q_{\text{alu}} = \frac{I(t)^2\, R_{\text{AC}}}{A_{\text{alu}}}, \qquad q_{\text{steel}} = 0$$

with $R_{\text{AC}}$ the per-unit-length AC resistance at 50 Hz. Implemented by
{py:func}`inthermo.forcing.joule_volumetric_heat`.

## Outer boundary condition

On the outer surface ($r = R_{\text{outer}}$), conduction balances convective
loss against solar gain:

$$-k\,\frac{\partial T}{\partial n} = q_{\text{conv}}(t) - q_{\text{solar}}(t)$$

### Convection

A Robin term $q_{\text{conv}} = h\,(T - T_{\text{amb}})$, with the film
coefficient $h$ from the IEEE Std 738 forced/natural correlations, evaluated at
the film temperature and recomputed each step from the wind speed and the
previous surface temperature (keeping each time step linear). Implemented by
{py:func}`inthermo.forcing.ieee738_convection_coefficient`.

### Solar gain

A horizontal cylinder of diameter $D$ intercepts $\alpha\,Q_{\text{solar}}\,D$
watts per metre of length; spread over the perimeter $\pi D$ the surface flux is

$$q_{\text{solar}} = \frac{\alpha\,Q_{\text{solar}}}{\pi}$$

```{note}
The datasheet writes $q_{\text{solar}} = \alpha Q / (\pi D)$, which is
dimensionally W·m⁻³. The code uses the dimensionally consistent **surface
flux** $\alpha Q / \pi$ (W·m⁻²); see
{py:func}`inthermo.forcing.solar_surface_flux`.
```

## Time integration & inputs

Time stepping is backward Euler; each step is a single linear solve. The model
is driven by five aligned time series (see
{py:class}`inthermo.solver.SimulationInputs`):

1. time array $t$
2. ambient temperature $T_{\text{amb}}(t)$
3. wind speed $v_{\text{wind}}(t)$
4. solar flux $Q_{\text{solar}}(t)$
5. current load $I(t)$
