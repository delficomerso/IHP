"""Bondpad components for IHP PDK."""

import math
from typing import Literal

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import (
    LayerSpec,
)


@gf.cell
def bondpad(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    diameter: float = 80.0,
    top_metal: str = "TopMetal2drawing",
    bbox_layers: tuple[LayerSpec, ...] | None = ("Passivpillar", "dfpaddrawing"),
    bbox_offsets: tuple[float, ...] | None = (-2.1, 0),
) -> Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    Args:
        shape: Shape of the bondpad ("octagon", "square", or "circle").
        diameter: Diameter or size of the bondpad in micrometers.
        top_metal: Top metal layer name.
        bbox_layers: Additional layers for passivation openings.
        bbox_offsets: Offsets for each additional layer.

    Returns:
        Component with bondpad layout.
    """
    c = Component()

    # Grid alignment
    d = diameter

    # Create the main pad shape
    if shape == "square":
        # Square bondpad
        pad = gf.components.rectangle(
            size=(d, d),
            layer=top_metal,
            centered=True,
        )
        c.add_ref(pad)

    elif shape == "octagon":
        # Octagonal bondpad
        # Calculate octagon vertices
        side_length = gf.snap.snap_to_grid2x(d / (1 + math.sqrt(2)))
        pad = gf.c.octagon(side_length=side_length, layer=top_metal)
        c.add_ref(pad)

    elif shape == "circle":
        # Circular bondpad (approximated with polygon)
        pad = gf.components.circle(
            radius=d / 2,
            layer=top_metal,
        )
        c.add_ref(pad)

    else:
        raise ValueError(f"Unknown shape: {shape}")

    # Stack additional metal layers if required
    for layer, offset in zip(bbox_layers or [], bbox_offsets or []):
        if shape == "square":
            opening = gf.components.rectangle(
                size=(d + offset, d + offset),
                layer=layer,
                centered=True,
            )
            c.add_ref(opening)
        elif shape == "octagon":
            side_length = gf.snap.snap_to_grid2x(offset + d / (1 + math.sqrt(2)))
            opening = gf.c.octagon(side_length=side_length, layer=layer)
            c.add_ref(opening)
        elif shape == "circle":
            opening = gf.components.circle(
                radius=d / 2 + offset / 2,
                layer=layer,
            )
            c.add_ref(opening)

    # Add port at the center
    c.add_port(
        name="pad",
        center=(0, 0),
        width=d,
        orientation=0,
        layer=top_metal,
        port_type="electrical",
    )

    # Add metadata
    c.info["shape"] = shape
    c.info["diameter"] = diameter
    c.info["top_metal"] = top_metal
    return c


@gf.cell
def bondpad_array(
    n_pads: int = 4,
    pad_pitch: float = 100.0,
    pad_diameter: float = 80.0,
    shape: Literal["octagon", "square", "circle"] = "octagon",
) -> Component:
    """Create an array of bondpads.

    Args:
        n_pads: Number of bondpads.
        pad_pitch: Pitch between bondpad centers in micrometers.
        pad_diameter: Diameter of each bondpad in micrometers.
        shape: Shape of the bondpads.

    Returns:
        Component with bondpad array.
    """
    c = Component()

    for i in range(n_pads):
        pad = bondpad(
            shape=shape,
            diameter=pad_diameter,
        )
        pad_ref = c.add_ref(pad)
        pad_ref.movex(i * pad_pitch)

        # Add port for each pad
        c.add_port(
            name=f"pad_{i + 1}",
            center=(i * pad_pitch, 0),
            width=pad_diameter,
            orientation=0,
            layer=pad.ports["pad"].layer,
            port_type="electrical",
        )

    c.info["n_pads"] = n_pads
    c.info["pad_pitch"] = pad_pitch
    c.info["pad_diameter"] = pad_diameter

    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    c0 = fixed.bondpad()  # original
    c1 = bondpad(shape="octagon")  # new
    c = xor(c0, c1)
    c.show()

    # c2 = bondpad(shape="square", flip_chip=True)
    # c2.show()

    # c3 = bondpad_array(n_pads=6)
    # c3.show()
