"""S-parameter models for IHP transmission lines."""

from typing import Any, TypedDict, Unpack

import jax.numpy as jnp
import sax
from gdsfactory.typings import CrossSectionSpec
from jax.typing import ArrayLike
from skrf import Frequency

from ihp.models.media import cross_section_to_media


class StraightModelKwargs(TypedDict, total=False):
    """Type definition for straight model keyword arguments."""

    f: ArrayLike
    length: int | float
    cross_section: CrossSectionSpec


def straight(
    f: ArrayLike = jnp.array([5e9]),
    length: int | float = 1000,
    cross_section: CrossSectionSpec = "strip",
) -> sax.SType:
    """S-parameter model for a straight transmission line.

    Uses scikit-rf analytical microstrip model.

    Args:
        f: Array of frequency points in Hz
        length: Physical length in µm
        cross_section: The cross-section of the transmission line.

    Returns:
        sax.SType: S-parameters dictionary
    """
    media = cross_section_to_media(cross_section)
    skrf_media = media(frequency=Frequency.from_f(f, unit="Hz"))
    transmission_line = skrf_media.line(d=length, unit="um")
    sdict = {
        ("o1", "o1"): jnp.array(transmission_line.s[:, 0, 0]),
        ("o1", "o2"): jnp.array(transmission_line.s[:, 0, 1]),
        ("o2", "o2"): jnp.array(transmission_line.s[:, 1, 1]),
    }
    return sax.reciprocal(sdict)


def bend_circular(
    *args: Any,
    **kwargs: Unpack[StraightModelKwargs],
) -> sax.SType:
    """S-parameter model for a circular bend, delegated to :func:`straight`.

    Args:
        *args: Positional arguments forwarded to :func:`straight`.
        **kwargs: Keyword arguments forwarded to :func:`straight`.

    Returns:
        sax.SType: S-parameters dictionary
    """
    return straight(*args, **kwargs)


def bend_euler(
    *args: Any,
    **kwargs: Unpack[StraightModelKwargs],
) -> sax.SType:
    """S-parameter model for an Euler bend, delegated to :func:`straight`.

    Args:
        *args: Positional arguments forwarded to :func:`straight`.
        **kwargs: Keyword arguments forwarded to :func:`straight`.

    Returns:
        sax.SType: S-parameters dictionary
    """
    return straight(*args, **kwargs)


def bend_s(
    *args: Any,
    **kwargs: Unpack[StraightModelKwargs],
) -> sax.SType:
    """S-parameter model for an S-bend, delegated to :func:`straight`.

    Args:
        *args: Positional arguments forwarded to :func:`straight`.
        **kwargs: Keyword arguments forwarded to :func:`straight`.

    Returns:
        sax.SType: S-parameters dictionary
    """
    return straight(*args, **kwargs)


def straight_metal(
    *args: Any,
    **kwargs: Unpack[StraightModelKwargs],
) -> sax.SType:
    """S-parameter model for metal routing, delegated to :func:`straight`.

    Args:
        *args: Positional arguments forwarded to :func:`straight`.
        **kwargs: Keyword arguments forwarded to :func:`straight`.

    Returns:
        sax.SType: S-parameters dictionary
    """
    return straight(*args, **kwargs)
