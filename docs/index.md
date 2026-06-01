# inthermo

Transient 2-D thermal model of an ACSR overhead-line conductor (Nexans
**Condor**, 220 kV / 50 Hz), solved with [FEniCSx](https://fenicsproject.org/).

The conductor cross-section is modelled as two concentric solid domains — a
galvanized **steel core** inside an **aluminum annulus** — governed by the
transient heat equation

$$\rho C_p \frac{\partial T}{\partial t} - \nabla \cdot (k \nabla T) = q(t)$$

with Joule heating in the aluminum and a combined convective + solar boundary
condition on the outer surface.

```{toctree}
:maxdepth: 2
:caption: Contents

installation
physics
usage
api
```

## At a glance

- **Layered design** — `parameters` and `forcing` are pure NumPy (run and test
  anywhere); `mesh` and `solver` require FEniCSx and are loaded lazily.
- **Validated** with dolfinx 0.10: a 24-hour synthetic run peaks at ~67 °C and
  the cross-section stays near-isothermal (core/surface within ~0.02 °C), as
  expected for a small high-conductivity conductor.
- See {doc}`installation` to get a runtime, {doc}`physics` for the model, and
  {doc}`usage` for a worked example.
