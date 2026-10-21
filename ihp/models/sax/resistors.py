"""
SAX resistor models for IHP SG13G2.

Wraps sax.models.rf.impedance with IHP process sheet resistances
extracted from cornerRES.lib.
"""

from functools import partial

import jax
import sax
from sax.models.rf import impedance

from ihp.models.sax.constants import (
    DEFAULT_FREQUENCY,
    RSH_RHIGH,
    RSH_RPPD,
    RSH_RSIL,
    Z0_DEFAULT,
)

__all__ = ["resistor", "rsil", "rppd", "rhigh"]


@partial(jax.jit, inline=True)
def resistor(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    resistance: float = 100.0,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """
    Two-port resistor. Wrapper around ``sax.models.rf.impedance``.
    """
    return impedance(f=f, z=resistance, z0=z0)


@partial(jax.jit, inline=True)
def rsil(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    width: float = 0.5,
    length: float = 0.5,
    sheet_resistance: float = RSH_RSIL,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """
    Silicided polysilicon resistor (Rsh ~ 7 Ohm/sq).

    Args:
        f: Frequency in Hz.
        width: Drawn width in um (``dx`` in the PCell).
        length: Drawn length in um (``dy`` in the PCell).
        sheet_resistance: Override sheet resistance in Ohm/sq.
        z0: Reference impedance in Ohm.
    """
    return resistor(f=f, resistance=sheet_resistance * length / width, z0=z0)


@partial(jax.jit, inline=True)
def rppd(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    width: float = 0.5,
    length: float = 0.5,
    sheet_resistance: float = RSH_RPPD,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """
    P+ polysilicon resistor, unsalicided (Rsh ~ 260 Ohm/sq).

    Args:
        f: Frequency in Hz.
        width: Drawn width in um.
        length: Drawn length in um.
        sheet_resistance: Override sheet resistance in Ohm/sq.
        z0: Reference impedance in Ohm.
    """
    return resistor(f=f, resistance=sheet_resistance * length / width, z0=z0)


@partial(jax.jit, inline=True)
def rhigh(
    *,
    f: sax.FloatArrayLike = DEFAULT_FREQUENCY,
    width: float = 0.5,
    length: float = 0.96,
    sheet_resistance: float = RSH_RHIGH,
    z0: sax.ComplexLike = Z0_DEFAULT,
) -> sax.SDict:
    """
    High-resistance polysilicon resistor (Rsh ~ 1360 Ohm/sq).

    Args:
        f: Frequency in Hz.
        width: Drawn width in um.
        length: Drawn length in um.
        sheet_resistance: Override sheet resistance in Ohm/sq.
        z0: Reference impedance in Ohm.
    """
    return resistor(f=f, resistance=sheet_resistance * length / width, z0=z0)
