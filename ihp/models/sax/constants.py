"""
IHP SG13G2 process constants for SAX frequency-domain models.

Values are extracted from the IHP SG13G2 PDK SPICE model libraries
and technology parameters.

References:
    IHP SG13G2 PDK: https://github.com/IHP-GmbH/IHP-Open-PDK
"""

# ---------------------------------------------------------------------------
# Simulation defaults
# ---------------------------------------------------------------------------
DEFAULT_FREQUENCY: float = 5e9  # Hz
Z0_DEFAULT: float = 50.0  # Ω — default reference impedance

# ---------------------------------------------------------------------------
# Resistor sheet resistances (Ω/square, nominal corner)
# Source: cornerRES.lib
# ---------------------------------------------------------------------------
RSH_RSIL: float = 7.0  # Silicided polysilicon
RSH_RPPD: float = 260.0  # P+ polysilicon (unsalicided)
RSH_RHIGH: float = 1360.0  # High-resistance polysilicon

# ---------------------------------------------------------------------------
# MIM capacitor parameters
# Source: cornerCAP.lib, tech.py
# ---------------------------------------------------------------------------
CMIM_CASPEC: float = 1.5  # fF/um^2 — area capacitance
CMIM_CPSPEC: float = 0.04  # fF/um — perimeter capacitance
CMIM_LWD: float = 0.01  # um — line-width delta
CMIM_SERIES_R: float = 0.055  # Ohm — top plate series resistance

RFCMIM_CASPEC: float = 1.5  # fF/um^2
RFCMIM_CPSPEC: float = 0.04  # fF/um
RFCMIM_LWD: float = 0.01  # um

# ---------------------------------------------------------------------------
# CMOM finger capacitor parameters
# Source: capacitors.py cmom_extractor
# ---------------------------------------------------------------------------
CMOM_FRINGE_FACTOR: float = 0.2
CMOM_DIELECTRIC_CONSTANT: float = 3.8  # SiO2

# Metal layer thicknesses (um) — Source: tech.py get_layer_stack()
CMOM_LAYER_THICKNESS: dict[str, float] = {
    "Metal1": 0.42,
    "Metal2": 0.49,
    "Metal3": 0.49,
    "Metal4": 0.49,
    "Metal5": 0.49,
}
