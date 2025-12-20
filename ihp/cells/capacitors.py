"""Capacitor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec, LayerSpecs

import math

from math import floor
from typing import List, Tuple

Rect = Tuple[float, float, float, float]

# Logic taken from original IHP rfcmim contact array
def add_contact_array(
    c,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    x_offset: float,
    y_offset: float,
    contact_size: float,
    contact_gap: float,
    layer_cont: LayerSpec = "Contdrawing",
    *,
    eps: float = 1e-9,
) -> List[Rect]:
    placed: List[Rect] = []

    width = x_max - x_min
    height = y_max - y_min

    if width <= 0 or height <= 0:
        return placed

    pitch_x = contact_size + contact_gap
    pitch_y = contact_size + contact_gap

    # how many columns fit (nx)
    nx = int(floor((width - 2 * x_offset + contact_gap) / pitch_x + eps))
    if nx <= 0:
        return placed

    # extra spacing between columns when more than one column fits
    if nx == 1:
        extra_space_x = 0.0
    else:
        extra_space_x = (width - 2 * x_offset - contact_size * nx) / (nx - 1)

    # how many rows fit (ny)
    ny = int(floor((height - 2 * y_offset + contact_gap) / pitch_y + eps))
    if ny <= 0:
        return placed

    # extra spacing between rows when more than one row fits
    if ny == 1:
        extra_space_y = 0.0
    else:
        extra_space_y = (height - 2 * y_offset - contact_size * ny) / (ny - 1)

    # initial x position *relative* to x_min
    if nx == 1:
        rel_x = (width - contact_size) / 2.0
    else:
        rel_x = x_offset

    # place columns
    for col in range(nx):
        # initial y position *relative* to y_min for each column
        if ny == 1:
            rel_y = (height - contact_size) / 2.0
        else:
            rel_y = y_offset

        for row in range(ny):
            x0 = x_min + rel_x
            y0 = y_min + rel_y
            x1 = x0 + contact_size
            y1 = y0 + contact_size

            # safety: ensure the contact fully fits into the box (mirror reference strictness)
            if x1 <= x_max + eps and y1 <= y_max + eps and x0 + eps >= x_min and y0 + eps >= y_min:
                add_rect(c, size=(contact_size, contact_size), layer=layer_cont, origin=(x0, y0))
                placed.append((x0, y0, x1, y1))

            # step to next row
            rel_y += contact_size + extra_space_y

        # step to next column
        rel_x += contact_size + extra_space_x

    return placed


def add_rect(component, size: tuple[float, float], layer: LayerSpec, origin: tuple[float, float], centered: bool = False):
    """Create rectangle, add ref to component and move to origin, return ref."""
    rect = gf.components.rectangle(size=size, layer=layer, centered=centered)
    ref = component.add_ref(rect)
    ref.move(origin)
    return ref

def place_vmim_grid(
    component,
    width: float,
    length: float,
    VMIM_EDGE_CLEARANCE: float = 0.34,
    VMIM_TILE_GAP: float = 0.84,
    VMIM_TILE_LENGTH: float = 0.42,
    GRID_STEP: float = 0.005,
    layer_vmim: LayerSpec = "Vmimdrawing"
):
    # Calculate how many tiles fit in X and Y
    tile_pitch = VMIM_TILE_GAP + VMIM_TILE_LENGTH
    n_tiles_x = int(
        max(
            math.floor((width - 2 * VMIM_EDGE_CLEARANCE + VMIM_TILE_GAP) / (tile_pitch)),
            0,
        )
    )
    n_tiles_y = int(
        max(
            math.floor((length - 2 * VMIM_EDGE_CLEARANCE + VMIM_TILE_GAP) / (tile_pitch)),
            0,
        )
    )

    # Compute occupied size of the tile array (including gaps and the edge overlaps)
    occupied_x = (n_tiles_x * (
        tile_pitch) - VMIM_TILE_GAP) + 2 * VMIM_EDGE_CLEARANCE if n_tiles_x > 0 else 0.0
    occupied_y = (n_tiles_y * (
        tile_pitch) - VMIM_TILE_GAP) + 2 * VMIM_EDGE_CLEARANCE if n_tiles_y > 0 else 0.0

    # Offsets to center tile array inside the MIM plate, snapped to grid
    x_offset = round(((width - occupied_x) / 2.0) / GRID_STEP) * GRID_STEP - 0.005
    y_offset = round(((length - occupied_y) / 2.0) / GRID_STEP) * GRID_STEP - 0.005

    x_start = VMIM_EDGE_CLEARANCE + x_offset
    y_start = VMIM_EDGE_CLEARANCE + y_offset

    # Draw Vmim grid
    for y_iter in range(n_tiles_y):
        y_current = y_start + y_iter * tile_pitch
        x_current = x_start
        for x_iter in range(n_tiles_x):
            add_rect(
                component,
                size=(VMIM_TILE_LENGTH, VMIM_TILE_LENGTH),
                layer=layer_vmim,
                origin=(x_current, y_current),
            )
            x_current = x_current + tile_pitch

    return x_start, y_start, n_tiles_x, n_tiles_y


def add_margin_ring(
    c,
    width: float,
    length: float,
    outer_margin: float,
    inner_margin: float,
    layer,
    metal_1_pad_length,
    cutout: bool = False,
):
    outer_x0 = -outer_margin
    outer_y0 = -outer_margin
    outer_x1 = width + outer_margin
    outer_y1 = length + outer_margin

    inner_x0 = -inner_margin
    inner_y0 = -inner_margin
    inner_x1 = width + inner_margin
    inner_y1 = length + inner_margin

    # top
    add_rect(
        c,
        size=(outer_x1 - outer_x0, outer_y1 - inner_y1),
        layer=layer,
        origin=(outer_x0, inner_y1),
    )

    # bottom
    add_rect(
        c,
        size=(outer_x1 - outer_x0, inner_y0 - outer_y0),
        layer=layer,
        origin=(outer_x0, outer_y0),
    )

    # left
    add_rect(
        c,
        size=(inner_x0 - outer_x0, inner_y1 - inner_y0),
        layer=layer,
        origin=(outer_x0, inner_y0),
    )

    # right
    if not cutout:
        add_rect(
            c,
            size=(outer_x1 - inner_x1, inner_y1 - inner_y0),
            layer=layer,
            origin=(inner_x1, inner_y0),
        )
    else:
        # lower right segment
        lower_h = (length - metal_1_pad_length) / 2.0 - inner_y0
        if lower_h > 0:
            add_rect(
                c,
                size=(outer_x1 - inner_x1, lower_h),
                layer=layer,
                origin=(inner_x1, inner_y0),
            )

        # upper right segment
        upper_h = inner_y1 - ((length + metal_1_pad_length) / 2.0)
        if upper_h > 0:
            add_rect(
                c,
                size=(outer_x1 - inner_x1, upper_h),
                layer=layer,
                origin=(inner_x1, (length + metal_1_pad_length) / 2.0),
            )


@gf.cell
def cmim(
    width: float = 6.99,
    length: float = 6.99,
    capacitance: float | None = None,
    model: str = "cmim",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_vmim: LayerSpec = "Vmimdrawing",
) -> Component:
    """Create an MIM (Metal-Insulator-Metal) capacitor.

    Args:
        width: MIM plate X-size (um). Scales the MIM/top-plate in X.
        length: MIM plate Y-size (um). Scales the MIM/top-plate in Y.
        capacitance: Optional (kept for compatibility; not used for geometry).
        model: Device model name stored in metadata.
        layer_metal5: Metal5 drawing layer.
        layer_mim: MIM dielectric layer.
        layer_topmetal1: TopMetal1 drawing layer.
        layer_vmim: Vmimdrawing (small tile) layer.

    Returns:
        MIM capacitor component.
    """
    c = Component()

    # Geometrical constants
    METAL_5_MIM_MARGIN = 0.6
    VMIM_EDGE_CLEARANCE = 0.34
    VMIM_TILE_LENGTH = 0.42
    VMIM_TILE_GAP = 0.84
    GRID_STEP = 0.005

    tile_pitch = VMIM_TILE_LENGTH + VMIM_TILE_GAP

    # Grid snapping
    length = round(length / GRID_STEP) * GRID_STEP
    width = round(width / GRID_STEP) * GRID_STEP

    # Calculate capacitance
    if capacitance is None:
        CAP_DENSITY = 1.54
        area = width * length
        capacitance = area * CAP_DENSITY

    # Draw MIM layer
    add_rect(c, size=(width, length), layer=layer_mim, origin=(0.0, 0.0))

    # Draw Metal5 bottom plate (bigger by METAL_5_MIM_MARGIN)
    metal_5_size_x = width + 2 * METAL_5_MIM_MARGIN
    metal_5_size_y = length + 2 * METAL_5_MIM_MARGIN
    add_rect(
        c,
        size=(metal_5_size_x, metal_5_size_y),
        layer=layer_metal5,
        origin=(-METAL_5_MIM_MARGIN, -METAL_5_MIM_MARGIN),
    )

    # Draw Vmim layer
    x_start, y_start, n_tiles_x, n_tiles_y = place_vmim_grid(
        c, width, length, VMIM_EDGE_CLEARANCE, VMIM_TILE_GAP, VMIM_TILE_LENGTH, GRID_STEP, layer_vmim)

    # Derive coordinates of top right corner
    metal_1_x2 = x_start + (n_tiles_x - 1) * tile_pitch + VMIM_TILE_LENGTH + VMIM_TILE_GAP / 2.0
    metal_1_y2 = y_start + (n_tiles_y - 1) * tile_pitch + VMIM_TILE_LENGTH + VMIM_TILE_GAP / 2.0

    # Derive coordinates of left bottom right corner
    metal_1_x1 = x_start - VMIM_TILE_GAP / 2.0
    metal_1_y1 = y_start - VMIM_TILE_GAP / 2.0

    # Draw TopMetal1 covering the tile-array area
    add_rect(
        c,
        size=(metal_1_x2 - metal_1_x1, metal_1_y2 - metal_1_y1),
        layer=layer_topmetal1,
        origin=(metal_1_x1, metal_1_y1),
    )

    # Add ports
    plus_center = ((metal_1_x1 + metal_1_x2) / 2.0, (metal_1_y1 + metal_1_y2) / 2.0)
    c.add_port(
        name="PLUS",
        center=plus_center,
        width=min(metal_1_x2 - metal_1_x1, metal_1_y2 - metal_1_y1),
        orientation=0,
        layer=layer_topmetal1,
        port_type="electrical",
    )

    minus_center = (-METAL_5_MIM_MARGIN + metal_5_size_x / 2.0, -METAL_5_MIM_MARGIN + metal_5_size_y / 2.0)
    c.add_port(
        name="MINUS",
        center=minus_center,
        width=min(metal_5_size_x, metal_5_size_y),
        orientation=180,
        layer=layer_metal5,
        port_type="electrical",
    )

    # Metadata
    c.info.update(
        {
            "model": model,
            "capacitance": capacitance,
            "mim_length": length,
            "mim_width": width,
            "vmim_tile_length": VMIM_TILE_LENGTH,
            "n_vmim_tiles": (n_tiles_x, n_tiles_y)
        }
    )

    return c


@gf.cell
def rfcmim(
    width: float = 7.0,
    length: float = 7.0,
    capacitance: float | None = None,
    model: str = "rfcmim",
    layer_activ: LayerSpec = "Activdrawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_metal5_pin: LayerSpec = "Metal5pin",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topmetal1_pin: LayerSpec = "TopMetal1pin",
    layer_vmim: LayerSpec = "Vmimdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_pwellblock: LayerSpec = "PWellblock",
    layers_no_qrc: LayerSpecs = (
        "Activnoqrc",
        "TopMetal1noqrc",
        "Metal1noqrc",
        "Metal2noqrc",
        "Metal3noqrc",
        "Metal4noqrc",
        "Metal5noqrc",
    ),
) -> Component:
    """
    Create an RF MIM capacitor (empty scaffold).

    Args:
        width: Capacitor width (dx) in micrometers.
        length: Capacitor length (dy) in micrometers.
        capacitance: Target capacitance in fF (optional).
        model: Model name for metadata.
        layer_activ: Active diffusion drawing layer.
        layer_mim: MIM dielectric layer.
        layer_metal1: Metal1 drawing layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_metal5: Metal5 drawing layer.
        layer_metal5_pin: Metal5 pin layer.
        layer_topmetal1: TopMetal1 drawing layer.
        layer_topmetal1_pin: TopMetal1 pin layer.
        layer_vmim: Vmim tile layer.
        layer_cont: Contact drawing layer.
        layer_psd: P-sub diffusion drawing layer.
        layer_pwellblock: P-well block mask.
        layers_no_qrc: No quantitative RC extraction layers

    Returns:
        Model of RF MIM capacitor
    """
    c = Component()

    # Geometrical constants
    MIM_METAL_5_MARGIN = 0.6
    MIM_METAL_1_MARGIN = 0.36
    MIM_PWELL_MARGIN = 3
    NO_QRC_PWELL_MARGIN = 2.6
    METAL_1_PAD_LENGTH = 3.0

    ACTIV_INNER_MARGIN = 3.6
    ACTIV_OUTER_MARGIN = 5.6
    PSD_INNER_MARGIN = 3.57
    PSD_OUTER_MARGIN = 5.63
    RING_INNER_MARGIN = 3.6
    RING_OUTER_MARGIN = 5.6

    CONTACT_SIZE = 0.16
    CONTACT_GAP = 0.18
    CONTACT_OFFSET_X = 0.36
    CONTACT_OFFSET_Y = 0.36

    VMIM_TILE_LENGTH = 0.42
    VMIM_EDGE_CLEARANCE = 0.78
    VMIM_TILE_GAP = 0.58

    # Grid snapping
    GRID_STEP = 0.005
    width = round(width / GRID_STEP) * GRID_STEP
    length = round(length / GRID_STEP) * GRID_STEP

    # Calculate capacitance
    if capacitance is None:
        CAP_DENSITY = 1.54
        area = length * width
        capacitance = area * CAP_DENSITY

    # MIM layer
    add_rect(c, (width, length), layer_mim, origin=(0, 0))

    # PWell block layer
    p_well_width = 2 * MIM_PWELL_MARGIN + width
    p_well_length = 2 * MIM_PWELL_MARGIN + length
    p_well_corner = (-MIM_PWELL_MARGIN, -MIM_PWELL_MARGIN)
    add_rect(c, (p_well_width, p_well_length), layer_pwellblock, origin=p_well_corner)

    # No QRC layers
    no_qrc_width = 2 * (MIM_PWELL_MARGIN + NO_QRC_PWELL_MARGIN) + width
    no_qrc_length = 2 * (MIM_PWELL_MARGIN + NO_QRC_PWELL_MARGIN) + length
    no_qrc_corner = (-MIM_PWELL_MARGIN - NO_QRC_PWELL_MARGIN, -MIM_PWELL_MARGIN - NO_QRC_PWELL_MARGIN)
    for layer in layers_no_qrc:
        add_rect(c, (no_qrc_width, no_qrc_length), layer, origin=no_qrc_corner)

    # Metal5 layer
    metal_5_width = 2 * MIM_METAL_5_MARGIN + width
    metal_5_length = 2 * MIM_METAL_5_MARGIN + length
    metal_5_corner = (-MIM_METAL_5_MARGIN, -MIM_METAL_5_MARGIN)
    add_rect(c, (metal_5_width, metal_5_length), layer_metal5, origin=metal_5_corner)

    metal5_feed_origin = (width + MIM_METAL_5_MARGIN, (length - METAL_1_PAD_LENGTH) / 2.0)
    metal5_feed_size = (RING_OUTER_MARGIN - MIM_METAL_5_MARGIN, METAL_1_PAD_LENGTH)
    add_rect(c, size=metal5_feed_size, layer=layer_metal5, origin=metal5_feed_origin)

    # Vmim layer
    add_contact_array(
        c,
        x_min=0.0,
        y_min=0.0,
        x_max=width,
        y_max=length,
        x_offset=VMIM_EDGE_CLEARANCE,
        y_offset=VMIM_EDGE_CLEARANCE,
        contact_size=VMIM_TILE_LENGTH,
        contact_gap=VMIM_TILE_GAP,
        layer_cont=layer_vmim,
    )

    # place_vmim_grid(c, width, length, VMIM_EDGE_CLEARANCE, VMIM_TILE_GAP, VMIM_TILE_LENGTH, GRID_STEP, layer_vmim)

    # Top Metal1 layer
    metal_1_width = width - 2 * MIM_METAL_1_MARGIN
    metal_1_length = length - 2 * MIM_METAL_1_MARGIN
    metal_1_corner = (MIM_METAL_1_MARGIN, MIM_METAL_1_MARGIN)
    metal_1_pad_width = MIM_PWELL_MARGIN + NO_QRC_PWELL_MARGIN + MIM_METAL_1_MARGIN
    metal_1_pad_corner = (- MIM_PWELL_MARGIN - NO_QRC_PWELL_MARGIN, (length - METAL_1_PAD_LENGTH)  / 2)

    add_rect(c, size=(metal_1_width, metal_1_length), layer=layer_topmetal1, origin=metal_1_corner)
    add_rect(c, size=(metal_1_pad_width, METAL_1_PAD_LENGTH), layer=layer_topmetal1, origin=metal_1_pad_corner)

    # Psd and activ layers
    add_margin_ring(
        c,
        width,
        length,
        outer_margin=PSD_OUTER_MARGIN,
        inner_margin=PSD_INNER_MARGIN,
        layer=layer_psd,
        metal_1_pad_length=METAL_1_PAD_LENGTH,
        cutout=False
    )

    add_margin_ring(
        c,
        width,
        length,
        outer_margin=ACTIV_OUTER_MARGIN,
        inner_margin=ACTIV_INNER_MARGIN,
        layer=layer_activ,
        metal_1_pad_length=METAL_1_PAD_LENGTH,
        cutout=True
    )

    # Metal1 layer
    add_margin_ring(
        c,
        width,
        length,
        outer_margin=RING_OUTER_MARGIN,
        inner_margin=RING_INNER_MARGIN,
        layer=layer_metal1,
        metal_1_pad_length=METAL_1_PAD_LENGTH,
        cutout=True
    )

    # Create Metal5 pin at the right
    metal5_feed_origin = (width +  RING_INNER_MARGIN, (length - METAL_1_PAD_LENGTH) / 2.0)
    metal5_feed_size = (RING_OUTER_MARGIN - RING_INNER_MARGIN, METAL_1_PAD_LENGTH)
    add_rect(c, size=metal5_feed_size, layer=layer_metal5, origin=metal5_feed_origin)
    add_rect(c, size=metal5_feed_size, layer=layer_metal5_pin, origin=metal5_feed_origin)

    # Metal1 pin
    metal1_pin_origin = (-RING_OUTER_MARGIN, -RING_OUTER_MARGIN)
    metal1_pin_size = (width + 2 * RING_OUTER_MARGIN, RING_OUTER_MARGIN - RING_INNER_MARGIN)
    add_rect(c, size=metal1_pin_size, layer=layer_metal1_pin, origin=metal1_pin_origin)

    # TopMetal1 pin
    top_metal1_origin = (-RING_OUTER_MARGIN, (length - METAL_1_PAD_LENGTH) / 2.0)
    top_metal1_size = (RING_OUTER_MARGIN - RING_INNER_MARGIN, METAL_1_PAD_LENGTH)
    add_rect(c, size=top_metal1_size, layer=layer_topmetal1_pin, origin=top_metal1_origin)

    # Cont layer
    # Right vertical – lower section
    add_contact_array(
        c,
        x_min=width + RING_INNER_MARGIN,
        y_min=-RING_INNER_MARGIN,
        x_max=width + RING_OUTER_MARGIN,
        y_max=(length - METAL_1_PAD_LENGTH) / 2.0,
        x_offset=CONTACT_OFFSET_X,
        y_offset=CONTACT_OFFSET_Y,
        contact_size=CONTACT_SIZE,
        contact_gap=CONTACT_GAP,
        layer_cont=layer_cont,
    )

    # Right vertical – upper section
    add_contact_array(
        c,
        x_min=width + RING_INNER_MARGIN,
        y_min=(length + METAL_1_PAD_LENGTH) / 2.0,
        x_max=width + RING_OUTER_MARGIN,
        y_max=length + RING_INNER_MARGIN,
        x_offset=CONTACT_OFFSET_X,
        y_offset=CONTACT_OFFSET_Y,
        contact_size=CONTACT_SIZE,
        contact_gap=CONTACT_GAP,
        layer_cont=layer_cont,
    )

    # Left vertical
    add_contact_array(
        c,
        x_min=-RING_OUTER_MARGIN,
        y_min=-RING_INNER_MARGIN,
        x_max=-RING_INNER_MARGIN,
        y_max=length + RING_INNER_MARGIN,
        x_offset=CONTACT_OFFSET_X,
        y_offset=CONTACT_OFFSET_Y,
        contact_size=CONTACT_SIZE,
        contact_gap=CONTACT_GAP,
        layer_cont=layer_cont,
    )

    # Top horizontal
    add_contact_array(
        c,
        x_min=-RING_OUTER_MARGIN,
        y_min=length + RING_INNER_MARGIN,
        x_max=width + RING_OUTER_MARGIN,
        y_max=length + RING_OUTER_MARGIN,
        x_offset=CONTACT_OFFSET_X,
        y_offset=CONTACT_OFFSET_Y,
        contact_size=CONTACT_SIZE,
        contact_gap=CONTACT_GAP,
        layer_cont=layer_cont,
    )

    # Bottom horizontal
    add_contact_array(
        c,
        x_min=-RING_OUTER_MARGIN,
        y_min=-RING_OUTER_MARGIN,
        x_max=width + RING_OUTER_MARGIN,
        y_max=-RING_INNER_MARGIN,
        x_offset=CONTACT_OFFSET_X,
        y_offset=CONTACT_OFFSET_Y,
        contact_size=CONTACT_SIZE,
        contact_gap=CONTACT_GAP,
        layer_cont=layer_cont,
    )

    # Add ports
    # Left port
    left_port_center = (- (RING_OUTER_MARGIN - 1.0), (length + METAL_1_PAD_LENGTH) / 2.0)
    c.add_port(
        name="P1",
        center=left_port_center,
        width=RING_OUTER_MARGIN - RING_INNER_MARGIN,
        orientation=180,
        layer=layer_topmetal1_pin,
        port_type="electrical",
    )

    # Right port
    right_port_center = (length + (RING_OUTER_MARGIN - 1.0), (length + METAL_1_PAD_LENGTH) / 2.0)
    c.add_port(
        name="P2",
        center=right_port_center,
        width=RING_OUTER_MARGIN - RING_INNER_MARGIN,
        orientation=0,
        layer=layer_metal5_pin,
        port_type="electrical",
    )

    # Bottom port
    bottom_port_center = (length / 2.0, - (RING_OUTER_MARGIN - 1.0))
    c.add_port(
        name="GND",
        center=bottom_port_center,
        width=2 * RING_OUTER_MARGIN + length,
        orientation=270,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["capacitance_fF"] = capacitance
    c.info["area_um2"] = width * length
    c.info["type"] = "rf_capacitor"

    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK, cells2
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    c0 = cells2.cmim()  # original
    c1 = cmim(width=6.99, length=6.99)  # New
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.rfcmim()  # original
    # c1 = rfcmim(width=7.0, length=7.0)  # New
    # c = xor(c0, c1)
    # c.show()
