"""Capacitor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec


@gf.cell
def cmim(
    width: float = 5.0,
    length: float = 5.0,
    capacitance: float | None = None,
    model: str = "cmim",
    layer_metal4: LayerSpec = "Metal4drawing",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_cap_mark: LayerSpec = "MemCapdrawing",
    layer_nofill: LayerSpec = "Metal4nofill",
) -> Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        capacitance: Target capacitance in fF (optional).
        model: Device model name.
        layer_metal4: Bottom plate metal layer.
        layer_metal5: Top plate metal layer.
        layer_mim: MIM dielectric layer.
        layer_via4: Via layer for top plate connection.
        layer_topmetal1: Top metal layer for connections.
        layer_topvia1: Via to top metal layer.
        layer_cap_mark: Capacitor marker layer.
        layer_nofill: No metal filler layer.

    Returns:
        Component with MIM capacitor layout.
    """
    c = Component()

    # Design rules
    mim_min_size = 0.5
    plate_enclosure = 0.2
    via_enclosure = 0.1
    cont_size = 0.26
    cont_spacing = 0.36
    cap_density = 1.5  # fF/um^2 (example value)

    # Validate dimensions
    width = max(width, mim_min_size)
    length = max(length, mim_min_size)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate capacitance if not provided
    if capacitance is None:
        capacitance = width * length * cap_density

    # Bottom plate (Metal4)
    bottom_plate_width = width + 2 * plate_enclosure
    bottom_plate_length = length + 2 * plate_enclosure

    bottom_plate = gf.components.rectangle(
        size=(bottom_plate_length, bottom_plate_width),
        layer=layer_metal4,
        centered=True,
    )
    c.add_ref(bottom_plate)

    # MIM dielectric layer
    mim_layer = gf.components.rectangle(
        size=(length, width),
        layer=layer_mim,
        centered=True,
    )
    c.add_ref(mim_layer)

    # Top plate (Metal5)
    top_plate = gf.components.rectangle(
        size=(length, width),
        layer=layer_metal5,
        centered=True,
    )
    c.add_ref(top_plate)

    # Via array for top plate connection
    n_vias_x = int((length - 2 * via_enclosure - cont_size) / cont_spacing) + 1
    n_vias_y = int((width - 2 * via_enclosure - cont_size) / cont_spacing) + 1

    for i in range(n_vias_x):
        for j in range(n_vias_y):
            x = -length / 2 + via_enclosure + cont_size / 2 + i * cont_spacing
            y = -width / 2 + via_enclosure + cont_size / 2 + j * cont_spacing

            via = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_via4,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

    # Connection extensions for bottom plate
    # Left extension
    bottom_ext_left = gf.components.rectangle(
        size=(plate_enclosure + 1.0, 1.0),
        layer=layer_metal4,
    )
    bottom_ext_left_ref = c.add_ref(bottom_ext_left)
    bottom_ext_left_ref.move((-(bottom_plate_length / 2), -0.5))

    # Right extension for top plate
    top_ext_right = gf.components.rectangle(
        size=(1.0, 1.0),
        layer=layer_metal5,
    )
    top_ext_right_ref = c.add_ref(top_ext_right)
    top_ext_right_ref.move((length / 2, -0.5))

    # Via to connect top plate extension to TopMetal1
    top_via = gf.components.rectangle(
        size=(0.9, 0.9),
        layer=layer_topvia1,
        centered=True,
    )
    top_via_ref = c.add_ref(top_via)
    top_via_ref.move((length / 2 + 0.5, 0))

    top_metal = gf.components.rectangle(
        size=(1.2, 1.2),
        layer=layer_topmetal1,
        centered=True,
    )
    top_metal_ref = c.add_ref(top_metal)
    top_metal_ref.move((length / 2 + 0.5, 0))

    # Capacitor marker
    cap_mark = gf.components.rectangle(
        size=(bottom_plate_length + 0.5, bottom_plate_width + 0.5),
        layer=layer_cap_mark,
        centered=True,
    )
    c.add_ref(cap_mark)

    # No metal filler region
    no_fill = gf.components.rectangle(
        size=(bottom_plate_length + 1.0, bottom_plate_width + 1.0),
        layer=layer_nofill,
        centered=True,
    )
    c.add_ref(no_fill)

    # Add ports
    c.add_port(
        name="P1",
        center=(-(bottom_plate_length / 2 + 0.5), 0),
        width=1.0,
        orientation=180,
        layer=layer_metal4,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(length / 2 + 0.5, 0),
        width=1.0,
        orientation=0,
        layer=layer_topmetal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["capacitance_fF"] = capacitance
    c.info["area_um2"] = width * length

    return c


@gf.cell
def rfcmim(
    width: float = 10.0,
    length: float = 10.0,
    capacitance: float | None = None,
    model: str = "rfcmim",
    layer_metal3: LayerSpec = "Metal3drawing",
    layer_metal4: LayerSpec = "Metal4drawing",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_via4: LayerSpec = "Via4drawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_topvia1: LayerSpec = "TopVia1drawing",
    layer_rfpad: LayerSpec = "RFPaddrawing",
    layer_cap_mark: LayerSpec = "MemCapdrawing",
) -> Component:
    """Create an RF MIM capacitor with optimized layout.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        capacitance: Target capacitance in fF (optional).
        model: Device model name.
        layer_metal3: Ground shield metal layer.
        layer_metal4: Bottom plate metal layer.
        layer_metal5: Top plate metal layer.
        layer_mim: MIM dielectric layer.
        layer_via4: Via layer for top plate connection.
        layer_topmetal1: Top metal layer for connections.
        layer_topvia1: Via to top metal layer.
        layer_rfpad: RF pad marker layer.
        layer_cap_mark: Capacitor marker layer.

    Returns:
        Component with RF MIM capacitor layout.
    """
    c = Component()

    # Design rules for RF capacitor
    mim_min_size = 5.0  # Larger minimum for RF
    plate_enclosure = 0.3
    via_enclosure = 0.15
    cont_size = 0.26
    cont_spacing = 0.36
    cap_density = 1.5  # fF/um^2
    shield_enclosure = 2.0

    # Validate dimensions
    width = max(width, mim_min_size)
    length = max(length, mim_min_size)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate capacitance if not provided
    if capacitance is None:
        capacitance = width * length * cap_density

    # Ground shield (Metal3)
    shield_width = width + 2 * shield_enclosure
    shield_length = length + 2 * shield_enclosure

    ground_shield = gf.components.rectangle(
        size=(shield_length, shield_width),
        layer=layer_metal3,
        centered=True,
    )
    c.add_ref(ground_shield)

    # Bottom plate (Metal4)
    bottom_plate_width = width + 2 * plate_enclosure
    bottom_plate_length = length + 2 * plate_enclosure

    bottom_plate = gf.components.rectangle(
        size=(bottom_plate_length, bottom_plate_width),
        layer=layer_metal4,
        centered=True,
    )
    c.add_ref(bottom_plate)

    # MIM dielectric layer
    mim_layer = gf.components.rectangle(
        size=(length, width),
        layer=layer_mim,
        centered=True,
    )
    c.add_ref(mim_layer)

    # Top plate (Metal5)
    top_plate = gf.components.rectangle(
        size=(length, width),
        layer=layer_metal5,
        centered=True,
    )
    c.add_ref(top_plate)

    # Via array for top plate connection (denser for RF)
    n_vias_x = int((length - 2 * via_enclosure - cont_size) / cont_spacing) + 1
    n_vias_y = int((width - 2 * via_enclosure - cont_size) / cont_spacing) + 1

    for i in range(n_vias_x):
        for j in range(n_vias_y):
            x = -length / 2 + via_enclosure + cont_size / 2 + i * cont_spacing
            y = -width / 2 + via_enclosure + cont_size / 2 + j * cont_spacing

            via = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_via4,
                centered=True,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

    # RF pad connections
    # Bottom plate pad
    bottom_pad = gf.components.rectangle(
        size=(2.0, 2.0),
        layer=layer_metal4,
    )
    bottom_pad_ref = c.add_ref(bottom_pad)
    bottom_pad_ref.move((-(bottom_plate_length / 2 + 1.0), -1.0))

    # Top plate pad
    top_pad = gf.components.rectangle(
        size=(2.0, 2.0),
        layer=layer_topmetal1,
    )
    top_pad_ref = c.add_ref(top_pad)
    top_pad_ref.move((length / 2 + 1.0, -1.0))

    # Connect top plate to TopMetal1
    # Via stack from Metal5 to TopMetal1
    via5_array = gf.components.rectangle(
        size=(0.9, 0.9),
        layer=layer_topvia1,
        centered=True,
    )
    via5_ref = c.add_ref(via5_array)
    via5_ref.move((length / 2 + 2.0, 0))

    tm1_connect = gf.components.rectangle(
        size=(2.0, 1.0),
        layer=layer_topmetal1,
    )
    tm1_ref = c.add_ref(tm1_connect)
    tm1_ref.move((length / 2 + 1.0, -0.5))

    # RF pad marker
    rf_pad1 = gf.components.rectangle(
        size=(3.0, 3.0),
        layer=layer_rfpad,
        centered=True,
    )
    rf_pad1_ref = c.add_ref(rf_pad1)
    rf_pad1_ref.move((-(bottom_plate_length / 2 + 1.0), 0))

    rf_pad2 = gf.components.rectangle(
        size=(3.0, 3.0),
        layer=layer_rfpad,
        centered=True,
    )
    rf_pad2_ref = c.add_ref(rf_pad2)
    rf_pad2_ref.move((length / 2 + 2.0, 0))

    # Capacitor marker
    cap_mark = gf.components.rectangle(
        size=(shield_length, shield_width),
        layer=layer_cap_mark,
        centered=True,
    )
    c.add_ref(cap_mark)

    # Add ports
    c.add_port(
        name="P1",
        center=(-(bottom_plate_length / 2 + 1.0), 0),
        width=2.0,
        orientation=180,
        layer=layer_metal4,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(length / 2 + 2.0, 0),
        width=2.0,
        orientation=0,
        layer=layer_topmetal1,
        port_type="electrical",
    )

    c.add_port(
        name="GND",
        center=(0, -shield_width / 2),
        width=shield_length,
        orientation=270,
        layer=layer_metal3,
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

    PDK.activate()

    # Test the components
    c0 = cells2.cmim()  # original
    c1 = cmim()  # New
    # c = gf.grid([c0, c1], spacing=100)
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.rfcmim()  # original
    # c1 = rfcmim()  # New
    # # c = gf.grid([c0, c1], spacing=100)
    # c = xor(c0, c1)
    # c.show()
