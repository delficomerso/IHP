"""Models for IHP transmission line media (microstrip on SiO2/Si)."""

from functools import cache, partial
from typing import Protocol, cast

import gdsfactory as gf
import skrf
from gdsfactory.cross_section import CrossSection
from gdsfactory.typings import CrossSectionSpec
from skrf.media import Media, MLine

from ihp.tech import LAYER_STACK

# IHP SG13G2 process constants
# SiO2 relative permittivity (intermetal dielectric)
EP_R_SIO2 = 3.9
# TopMetal2: 3.0 µm thick aluminum
# Height above Si substrate: accumulate through BEOL stack
# z_topmetal2 ≈ 10.24 µm from layer stack


class MediaCallable(Protocol):
    """Typing protocol for functions returning skrf Media from a frequency."""

    def __call__(self, *, frequency: skrf.Frequency) -> Media:
        """Call with frequency keyword argument and return Media object."""
        ...


def _get_layer_height(layer_key: str) -> float:
    """Get zmin of a layer from the IHP layer stack in µm."""
    layer = LAYER_STACK.layers[layer_key]
    return cast(float, layer.zmin)


def _get_layer_thickness(layer_key: str) -> float:
    """Get thickness of a layer from the IHP layer stack in µm."""
    layer = LAYER_STACK.layers[layer_key]
    return cast(float, layer.thickness)


@cache
def microstrip_media_skrf(
    width: float = 2.0,
    height: float | None = None,
    t: float | None = None,
    ep_r: float = EP_R_SIO2,
) -> MediaCallable:
    """Create a microstrip media object using scikit-rf.

    Models a microstrip transmission line on the IHP SiO2/Si substrate.
    Default parameters correspond to TopMetal2 routing.

    Args:
        width: Width of the conductor in µm.
        height: Dielectric height (conductor to ground plane) in µm.
            Defaults to TopMetal2 zmin (height above substrate).
        t: Conductor thickness in µm. Defaults to TopMetal2 thickness.
        ep_r: Relative permittivity of the dielectric (SiO2 = 3.9).

    Returns:
        MediaCallable: A callable returning skrf MLine media for a given frequency.
    """
    if height is None:
        height = _get_layer_height("topmetal2")
    if t is None:
        t = _get_layer_thickness("topmetal2")

    return partial(
        MLine,
        w=width * 1e-6,  # µm -> m
        h=height * 1e-6,  # µm -> m
        t=t * 1e-6,  # µm -> m
        ep_r=ep_r,
        rho=2.65e-8,  # Aluminum resistivity [Ω·m]
        tand=0,  # Lossless dielectric for now
    )


def cross_section_to_media(cross_section: CrossSectionSpec) -> MediaCallable:
    """Convert a gdsfactory cross-section to a microstrip MediaCallable.

    Extracts the width from the cross-section and uses IHP process defaults
    for dielectric height and metal thickness.

    Args:
        cross_section: A gdsfactory cross-section specification.

    Returns:
        MediaCallable: A callable returning skrf Media for a given frequency.
    """
    xs: CrossSection
    if isinstance(cross_section, CrossSection):
        xs = cross_section
    elif callable(cross_section):
        xs = cast(CrossSection, cross_section())
    else:
        xs = gf.get_cross_section(cross_section)

    width = xs.width
    return microstrip_media_skrf(width=width)
