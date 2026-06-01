# Datasheet and Simulation Profile: Condor ACSR Cable (220 kV / 50 Hz)

This document contains all the structural, mechanical, electrical, and environmental parameters required to build a 2D transient thermal CFD model for the "Condor" power line conductor.

---

## 1. Conductor Specification (From Nexans Datasheet)

### General Information
* [cite_start]**Manufacturer:** Nexans [cite: 1]
* [cite_start]**Conductor Type:** Bare Aluminum Conductor Steel Reinforced - CAA (Serie KCMIL) / ACSR [cite: 2]
* [cite_start]**Designation/Code Name:** Condor [cite: 2]
* [cite_start]**Manufacturing Standard:** ABNT NBR 7270/88 [cite: 9]
* [cite_start]**Geometry Configuration:** Concentric circular stranded conductor consisting of an inner steel core surrounded by layers of aluminum wires[cite: 7, 15, 16].

### Dimensional Properties
* [cite_start]**Total Nominal Diameter ($D_{\text{outer}}$):** $27.72\text{ mm}$ ($0.02772\text{ m}$) [cite: 30]
* **Steel Core Diameter ($D_{\text{steel}}$):** $9.24\text{ mm}$ ($0.00924\text{ m}$) [cite: 30]
* **Total Nominal Cross-Sectional Area:** $454.48\text{ mm}^2$ [cite: 30]
* [cite_start]**Aluminum Cross-Sectional Area ($A_{\text{alu}}$):** $402.33\text{ mm}^2$ ($4.0233 \times 10^{-4}\text{ m}^2$) [cite: 30]
* **Number of Aluminum Wires:** 54 (Wire diameter: $3.08\text{ mm}$) [cite: 30]
* [cite_start]**Number of Steel Wires:** 7 (Wire diameter: $3.08\text{ mm}$) [cite: 30]
* [cite_start]**Total Number of Wires:** 61 [cite: 30]
* **Geometric Mean Radius (GMR):** $0.01123\text{ m}$ [cite: 30]

### Material Weights
* [cite_start]**Aluminum Weight (Approx.):** $1114.7\text{ kg/km}$ [cite: 30]
* [cite_start]**Steel Weight (Approx.):** $407.63\text{ kg/km}$ [cite: 30]
* **Total Cable Weight (Approx.):** $1522\text{ kg/km}$ [cite: 30]

---

## 2. Updated Grid & Electrical Specifications

The power line has been updated from the baseline datasheet values to operate under a specific grid layout:

* **Nominal Grid Voltage:** $220\text{ kV}$
* **Grid Frequency:** $50\text{ Hz}$ *(Note: Datasheet metrics were originally rated for 60 Hz)* [cite: 30]
* [cite_start]**Maximum Baseline Ampacity:** $900.0\text{ A}$ [cite: 30]

### Corrected Resistance Parameters for 50 Hz
Due to the modification from $60\text{ Hz}$ to $50\text{ Hz}$, the skin effect is less prominent. The adjusted operational values at $75^\circ\text{C}$ are:

* [cite_start]**DC Resistance at $20^\circ\text{C}$ (Max):** $0.072\ \Omega/\text{km}$ [cite: 30]
* **AC Resistance at $60\text{ Hz}$ ($75^\circ\text{C}$):** $0.087\ \Omega/\text{km}$ *(Datasheet baseline)* [cite: 30]
* **AC Resistance at $50\text{ Hz}$ ($75^\circ\text{C}$):** $\approx 0.085\ \Omega/\text{km}$ ($8.5 \times 10^{-5}\ \Omega/\text{m}$) *(Adjusted for 50 Hz simulation use)*
* **Inductive Reactance ($X_L$ at $50\text{ Hz}$):** $0.2822\ \Omega/\text{km}$ *(Scaled from 0.3386)* [cite: 30]
* **Capacitive Reactance ($X_C$ at $50\text{ Hz}$):** $0.2450\ \text{M}\Omega\cdot\text{km}$ *(Scaled from 0.2042)* [cite: 30]

---

## 3. Solid Material Properties for Thermal Analysis

To run a transient multi-domain heat simulation, the following macroscopic materials profiles must be mapped into the FEniCSx geometry domains:

| Property | [cite_start]Aluminum Layer (1350-H19) [cite: 16, 30] | [cite_start]Steel Core (Galvanized) [cite: 12, 18] |
| :--- | :--- | :--- |
| **Thermal Conductivity ($k$)** | $205.0\text{ W/m}\cdot\text{K}$ | $50.0\text{ W/m}\cdot\text{K}$ |
| **Density ($\rho$)** | $2700.0\text{ kg/m}^3$ | $7850.0\text{ kg/m}^3$ |
| **Specific Heat Capacity ($C_p$)** | $900.0\text{ J/kg}\cdot\text{K}$ | $480.0\text{ J/kg}\cdot\text{K}$ |
| **Solar Absorptivity ($\alpha$)** | $0.5$ | *N/A (Internal)* |

---

## 4. Mathematical Modeling & Physics Boundary Conditions

The AI agent must implement a 2D transient Heat Equation across two distinct subdomains:

$$\rho C_p \frac{\partial T}{\partial t} - \nabla \cdot (k \nabla T) = q(t)$$

### Heat Generation (Joule Effect)
Heat is generated exclusively in the Aluminum layer. 
* **Aluminum Subdomain ($q_{\text{alu}}$):** $\frac{I(t)^2 \cdot R_{\text{AC, 50Hz}}}{A_{\text{alu}}}$
* **Steel Subdomain ($q_{\text{steel}}$):** $0$ (Assuming no current flows through the structural core).

### Outer Boundary Condition ($r = R_{\text{outer}}$)
The outer boundary balances heat dissipation and external environmental loads over time:

$$-k_{\text{alu}} \frac{\partial T}{\partial n} = q_{\text{conv}}(t) - q_{\text{solar}}(t)$$

1. **Convection Loss:** $q_{\text{conv}}(t) = h(v_{\text{wind}}(t)) \cdot \left(T - T_{\text{amb}}(t)\right)$
   * The convective heat transfer coefficient ($h$) should be updated dynamically based on the incoming wind speed variable using empirical equations (such as the IEEE 738 standard).
2. **Solar Radiation Heat Gain:** $q_{\text{solar}}(t) = \frac{\alpha_{\text{solar}} \cdot Q_{\text{solar}}(t)}{\pi \cdot D_{\text{outer}}}$ (Distributed flux across the perimeter surface).

---

## 5. Input Data Streams Needed for Time Loop

The simulation step execution relies on processing an external input data sequence array over time. Ensure the following time-profile vectors are provided:
1. **Time Array ($t$):** Array of increments (e.g., $\Delta t = 60\text{ s}$).
2. **Ambient Temperature Profile ($T_{\text{amb}}(t)$):** In $^{\circ}\text{C}$.
3. **Wind Speed Profile ($v_{\text{wind}}(t)$):** In $\text{m/s}$.
4. **Solar Radiation Flux Profile ($Q_{\text{solar}}(t)$):** In $\text{W/m}^2$.
5. **Electrical Current Load Profile ($I(t)$):** In Amperes ($\text{A}$).