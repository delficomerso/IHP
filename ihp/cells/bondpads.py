"""Bondpad components for IHP PDK."""

import math
from typing import Literal

import gdsfactory as gf
from gdsfactory import Component


@gf.cell
def bondpad(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    stack_metals: bool = True,
    flip_chip: bool = False,
    diameter: float = 68.0,
    top_metal: str = "TopMetal2drawing",
    bottom_metal: str = "Metal1",
    passivation_open: str = "dfpaddrawing",
    ubm_layer=(155, 0),
) -> Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    Args:
        shape: Shape of the bondpad ("octagon", "square", or "circle").
        stack_metals: Stack all metal layers from bottom to top.
        flip_chip: Enable flip-chip configuration.
        diameter: Diameter or size of the bondpad in micrometers.
        top_metal: Top metal layer name.
        bottom_metal: Bottom metal layer name.
        passivation_open: Passivation opening layer name.
        ubm_layer: Under-bump metallization layer.

    Returns:
        Component with bondpad layout.
    """
    c = Component()

    # Grid alignment
    grid = 0.01
    d = round(diameter / grid) * grid

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

    # Add passivation opening
    if shape == "square":
        opening = gf.components.rectangle(
            size=(d * 0.85, d * 0.85),
            layer=passivation_open,
            centered=True,
        )
        c.add_ref(opening)
    elif shape == "octagon":
        scale = 0.85
        side_length = gf.snap.snap_to_grid2x(scale * d / (1 + math.sqrt(2)))
        opening = gf.c.octagon(side_length=side_length, layer=passivation_open)
        c.add_ref(opening)
    elif shape == "circle":
        opening = gf.components.circle(
            radius=d / 2 * 0.85,
            layer=passivation_open,
        )
        c.add_ref(opening)

    # Add flip-chip bumps if requested
    if flip_chip:
        # Add under-bump metallization (UBM)
        if shape == "circle":
            ubm = gf.components.circle(
                radius=d / 2 * 0.7,
                layer=ubm_layer,
            )
            c.add_ref(ubm)
        else:
            ubm = gf.components.rectangle(
                size=(d * 0.7, d * 0.7),
                layer=ubm_layer,
                centered=True,
            )
            c.add_ref(ubm)

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
    c.info["stack_metals"] = stack_metals
    c.info["flip_chip"] = flip_chip
    c.info["top_metal"] = top_metal
    c.info["bottom_metal"] = bottom_metal
    return c


@gf.cell
def bondpad_array(
    n_pads: int = 4,
    pad_pitch: float = 100.0,
    pad_diameter: float = 68.0,
    shape: Literal["octagon", "square", "circle"] = "octagon",
    stack_metals: bool = True,
) -> Component:
    """Create an array of bondpads.

    Args:
        n_pads: Number of bondpads.
        pad_pitch: Pitch between bondpad centers in micrometers.
        pad_diameter: Diameter of each bondpad in micrometers.
        shape: Shape of the bondpads.
        stack_metals: Stack all metal layers.

    Returns:
        Component with bondpad array.
    """
    c = Component()

    for i in range(n_pads):
        pad = bondpad(
            shape=shape,
            stack_metals=stack_metals,
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
    from ihp import cells

    # Test the components
    c0 = bondpad(shape="octagon")
    c1 = cells.bondpad()

    c = gf.grid([c0, c1], spacing=100)
    c.show()

    # c2 = bondpad(shape="square", flip_chip=True)
    # c2.show()

    # c3 = bondpad_array(n_pads=6)
    # c3.show()
