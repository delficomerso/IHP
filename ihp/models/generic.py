"""S-parameter models for generic lumped components."""

from functools import partial

import jax
import jax.numpy as jnp
import sax
from jax.typing import ArrayLike


@partial(jax.jit, inline=True, static_argnames=("n_ports"))
def gamma_0_load(
    f: ArrayLike = jnp.array([5e9]),
    gamma_0: int | float | complex = 0,
    n_ports: int = 1,
) -> sax.SType:
    r"""Connection with given reflection coefficient.

    Args:
        f: Array of frequency points in Hz
        gamma_0: Reflection coefficient Γ₀
        n_ports: Number of ports

    Returns:
        sax.SType: S-parameters dictionary where :math:`S = \Gamma_0 I_\text{n\_ports}`
    """
    sdict = {
        (f"o{i}", f"o{i}"): jnp.full(len(f), gamma_0) for i in range(1, n_ports + 1)
    }
    sdict |= {
        (f"o{i}", f"o{j}"): jnp.zeros(len(f), dtype=complex)
        for i in range(1, n_ports + 1)
        for j in range(i + 1, n_ports + 1)
    }
    return sax.reciprocal(sdict)


@partial(jax.jit, inline=True, static_argnames=("n_ports"))
def short(
    f: ArrayLike = jnp.array([5e9]),
    n_ports: int = 1,
) -> sax.SType:
    r"""Electrical short connection.

    Args:
        f: Array of frequency points in Hz
        n_ports: Number of ports

    Returns:
        sax.SType: S-parameters dictionary where :math:`S = -I_\text{n\_ports}`
    """
    return gamma_0_load(f=f, gamma_0=-1, n_ports=n_ports)


@partial(jax.jit, inline=True, static_argnames=("n_ports"))
def open(
    f: ArrayLike = jnp.array([5e9]),
    n_ports: int = 1,
) -> sax.SType:
    r"""Electrical open connection.

    Args:
        f: Array of frequency points in Hz
        n_ports: Number of ports

    Returns:
        sax.SType: S-parameters dictionary where :math:`S = I_\text{n\_ports}`
    """
    return gamma_0_load(f=f, gamma_0=1, n_ports=n_ports)


@partial(jax.jit, inline=True)
def tee(f: ArrayLike = jnp.array([5e9])) -> sax.SType:
    """Ideal 3-port power divider/combiner (T-junction).

    Args:
        f: Array of frequency points in Hz

    Returns:
        sax.SType: S-parameters dictionary
    """
    sdict = {(f"o{i}", f"o{i}"): jnp.full(len(f), -1 / 3) for i in range(1, 4)}
    sdict |= {
        (f"o{i}", f"o{j}"): jnp.full(len(f), 2 / 3)
        for i in range(1, 4)
        for j in range(i + 1, 4)
    }
    return sax.reciprocal(sdict)


@partial(jax.jit, inline=True)
def single_impedance_element(
    z: int | float | complex = 50,
    z0: int | float | complex = 50,
) -> sax.SType:
    r"""Series impedance element.

    Args:
        z: Impedance in Ω
        z0: Reference impedance in Ω

    Returns:
        sax.SType: S-parameters dictionary
    """
    sdict = {
        ("o1", "o1"): z / (z + 2 * z0),
        ("o1", "o2"): 2 * z0 / (2 * z0 + z),
        ("o2", "o2"): z / (z + 2 * z0),
    }
    return sax.reciprocal(sdict)


@partial(jax.jit, inline=True)
def single_admittance_element(
    y: int | float | complex = 1 / 50,
) -> sax.SType:
    r"""Shunt admittance element.

    Args:
        y: Admittance

    Returns:
        sax.SType: S-parameters dictionary
    """
    sdict = {
        ("o1", "o1"): 1 / (1 + y),
        ("o1", "o2"): y / (1 + y),
        ("o2", "o2"): 1 / (1 + y),
    }
    return sax.reciprocal(sdict)


@partial(jax.jit, inline=True)
def resistor(
    f: ArrayLike = jnp.array([5e9]),
    resistance: float = 50.0,
    z0: int | float | complex = 50,
) -> sax.SType:
    """Ideal resistor S-parameter model.

    Args:
        f: Array of frequency points in Hz
        resistance: Resistance in Ω
        z0: Reference impedance in Ω

    Returns:
        sax.SType: S-parameters dictionary
    """
    _ = f  # frequency-independent
    return single_impedance_element(z=resistance, z0=z0)


@partial(jax.jit, inline=True)
def capacitor(
    f: ArrayLike = jnp.array([5e9]),
    capacitance: float = 1e-12,
    z0: int | float | complex = 50,
) -> sax.SType:
    """Ideal capacitor S-parameter model.

    Args:
        f: Array of frequency points in Hz
        capacitance: Capacitance in Farads
        z0: Reference impedance in Ω

    Returns:
        sax.SType: S-parameters dictionary
    """
    omega = 2 * jnp.pi * jnp.asarray(f)
    z_cap = 1 / (1j * omega * capacitance)
    return single_impedance_element(z=z_cap, z0=z0)


@partial(jax.jit, inline=True)
def inductor(
    f: ArrayLike = jnp.array([5e9]),
    inductance: float = 1e-9,
    z0: int | float | complex = 50,
) -> sax.SType:
    """Ideal inductor S-parameter model.

    Args:
        f: Array of frequency points in Hz
        inductance: Inductance in Henries
        z0: Reference impedance in Ω

    Returns:
        sax.SType: S-parameters dictionary
    """
    omega = 2 * jnp.pi * jnp.asarray(f)
    z_ind = 1j * omega * inductance
    return single_impedance_element(z=z_ind, z0=z0)
