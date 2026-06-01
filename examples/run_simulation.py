"""Run a 24-hour transient thermal simulation of the Condor conductor.

Run inside the dolfinx environment (see README), e.g.::

    docker run --rm -v "${PWD}:/work" -w /work dolfinx/dolfinx:stable \
        bash -c "pip install -e . && python examples/run_simulation.py"

Produces ``conductor_temperature.xdmf`` (open in ParaView) and prints the peak
conductor temperature over the day.
"""

import numpy as np

from inthermo import CONDOR, load_fenics_api


def synthetic_day(n_steps=24 * 60, dt=60.0):
    """A synthetic 24 h profile at 1-minute resolution."""
    t = np.arange(n_steps) * dt
    hours = t / 3600.0
    # Diurnal ambient temperature: 15 C at night, 30 C mid-afternoon.
    t_amb = 22.5 - 7.5 * np.cos(2 * np.pi * (hours - 15) / 24)
    # Wind: light, gusty.
    wind = 1.0 + 0.5 * np.sin(2 * np.pi * hours / 6) ** 2
    # Solar bell curve, zero at night, peak ~1000 W/m^2 at noon.
    solar = np.clip(1000.0 * np.sin(np.pi * (hours - 6) / 12), 0.0, None)
    solar[(hours < 6) | (hours > 18)] = 0.0
    # Current: daytime loading ramp up to near ampacity.
    current = 500.0 + 350.0 * np.clip(np.sin(np.pi * (hours - 7) / 14), 0.0, None)
    return t, t_amb, wind, solar, current


def main():
    api = load_fenics_api()

    cm = api["generate_conductor_mesh"](CONDOR.geometry)

    t, t_amb, wind, solar, current = synthetic_day()
    inputs = api["SimulationInputs"](
        time=t,
        ambient_temperature=t_amb,
        wind_speed=wind,
        solar_radiation=solar,
        current=current,
    )

    solver = api["ConductorThermalSolver"](
        conductor_mesh=cm, config=CONDOR, initial_temperature=float(t_amb[0])
    )
    result = solver.solve(inputs, xdmf_path="conductor_temperature.xdmf")

    i_peak = int(np.nanargmax(result.max_temperature))
    print(f"Peak conductor temperature: {result.max_temperature[i_peak]:.1f} C "
          f"at t = {result.time[i_peak] / 3600:.1f} h")
    print(f"Final surface temperature:  {result.surface_temperature[-1]:.1f} C")
    print(f"Final core temperature:     {result.core_temperature[-1]:.1f} C")
    print("Wrote conductor_temperature.xdmf (open in ParaView).")


if __name__ == "__main__":
    main()
