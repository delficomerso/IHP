"""Resistor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec


@gf.cell
def rsil(
    width: float = 0.5,
    length: float = 0.5,
    resistance: float | None = None,
    model: str = "rsil",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_res_mark: LayerSpec = "RESdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
) -> Component:
    """Create a silicided polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_res_mark: Resistor marker layer.
        layer_block: Blocking layer.

    Returns:
        Component with silicided poly resistor layout.
    """
    c = Component()

    # Default parameters
    rsil_min_width = 0.4
    rsil_min_length = 0.5
    sheet_resistance = 7.0
    gate_poly_end_extension_width = 0.35

    # Contact parameters
    cont_width = 0.16
    cont_length = 0.36
    cont_space_x = 0.07
    cont_space_y = 0.12

    # Metal layer parameters
    metal_contact_margin = 0.05

    # Blocking layer parameters
    block_width = 1.56
    block_length = 0.86

    # Validate dimensions
    width = max(width, rsil_min_width)
    length = max(length, rsil_min_length)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate resistance if not provided
    if resistance is None:
        n_squares = length / width
        resistance = n_squares * sheet_resistance

    # Create resistor body (polysilicon)
    body_layers = [layer_poly, layer_heat, layer_res_mark]
    for layer in body_layers:
        res_body = gf.components.rectangle(
            size=(length, width),
            layer=layer,
            centered=True,
        )
        res_body_ref = c.add_ref(res_body)
        res_body_ref.move((length / 2, width / 2))

    # End contact regions (gate polysilicon extensions)
    upper_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    upper_ref = c.add_ref(upper_contact)
    upper_ref.move((0, width))

    lower_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    lower_ref = c.add_ref(lower_contact)
    lower_ref.move((0, -gate_poly_end_extension_width))

    # Contact regions
    cont_upper = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_upper_ref = c.add_ref(cont_upper)
    cont_upper_ref.move((cont_space_x, width + cont_space_y))

    cont_lower = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_lower_ref = c.add_ref(cont_lower)
    cont_lower_ref.move((cont_space_x, - cont_width - cont_space_y))

    # Metal layer regions
    metal_length = cont_length + 2 * metal_contact_margin
    metal_width = cont_width + 2 * metal_contact_margin
    metal_space_x = cont_space_x - metal_contact_margin
    metal_space_y = cont_space_y - metal_contact_margin

    metal_layers = [layer_metal1_pin, layer_metal1]

    for layer in metal_layers:
        metal_upper = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_upper_ref = c.add_ref(metal_upper)
        metal_upper_ref.move((metal_space_x, width + metal_space_y))

        metal_lower = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_lower_ref = c.add_ref(metal_lower)
        metal_lower_ref.move((metal_space_x, - metal_width - metal_space_y))

    # Add blocking layers
    block = gf.components.rectangle(
        size=(block_length, block_width),
        layer=layer_block,
    )
    block_ref = c.add_ref(block)
    block_ref.move(((length - block_length) / 2, (width - block_width) / 2))

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + gate_poly_end_extension_width / 2), 0),
        width=cont_width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical")

    c.add_port(
        name="P2",
        center=(length / 2 + gate_poly_end_extension_width / 2, 0),
        width=cont_width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical")

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["resistance"] = resistance
    c.info["sheet_resistance"] = sheet_resistance
    c.info["n_squares"] = length / width

    return c


@gf.cell
def rppd(
    width: float = 0.5,
    length: float = 0.5,
    resistance: float | None = None,
    model: str = "rsil",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_pSD: LayerSpec = "pSDdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
    layer_sal_block: LayerSpec = "SalBlockdrawing",
) -> Component:
    """Create a P+ polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_pSD: PSD layer.
        layer_block: Blocking layer.
        layer_sal_block: Salicide block layer.

    Returns:
        Component with P+ resistor layout.
    """
    c = Component()

    # Default parameters
    rppd_min_width = 0.4
    rppd_min_length = 0.5
    sheet_resistance = 300.0
    gate_poly_end_extension_width = 0.43

    # Contact parameters
    cont_width = 0.16
    cont_length = 0.36
    cont_space_x = 0.07
    cont_space_y = 0.20

    # Metal layer parameters
    metal_contact_margin_x = 0.05
    metal_contact_margin_y = 0.07

    # Blocking layer parameters
    block_width = 1.72
    block_length = 0.86
    block_2_width = 0.50
    block_2_length = 0.90

    # Validate dimensions
    width = max(width, rppd_min_width)
    length = max(length, rppd_min_length)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate resistance if not provided
    if resistance is None:
        n_squares = length / width
        resistance = n_squares * sheet_resistance

    # Create resistor body (polysilicon)
    body_layers = [layer_poly, layer_heat]
    for layer in body_layers:
        res_body = gf.components.rectangle(
            size=(length, width),
            layer=layer,
            centered=True,
        )
        res_body_ref = c.add_ref(res_body)
        res_body_ref.move((length / 2, width / 2))

    # End contact regions (gate polysilicon extensions)
    upper_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    upper_ref = c.add_ref(upper_contact)
    upper_ref.move((0, width))

    lower_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    lower_ref = c.add_ref(lower_contact)
    lower_ref.move((0, -gate_poly_end_extension_width))

    # Contact regions
    cont_upper = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_upper_ref = c.add_ref(cont_upper)
    cont_upper_ref.move((cont_space_x, width + cont_space_y))

    cont_lower = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_lower_ref = c.add_ref(cont_lower)
    cont_lower_ref.move((cont_space_x, - cont_width - cont_space_y))

    # Metal layer regions
    metal_length = cont_length + 2 * metal_contact_margin_x
    metal_width = cont_width + 2 * metal_contact_margin_y
    metal_space_x = cont_space_x - metal_contact_margin_x
    metal_space_y = cont_space_y - metal_contact_margin_y

    metal_layers = [layer_metal1_pin, layer_metal1]

    for layer in metal_layers:
        metal_upper = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_upper_ref = c.add_ref(metal_upper)
        metal_upper_ref.move((metal_space_x, width + metal_space_y))

        metal_lower = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_lower_ref = c.add_ref(metal_lower)
        metal_lower_ref.move((metal_space_x, - metal_width - metal_space_y))

    # Add blocking layers
    blocks_1_layers = [layer_block, layer_pSD]
    for layer in blocks_1_layers:
        block = gf.components.rectangle(
            size=(block_length, block_width),
            layer=layer,
        )
        block_ref = c.add_ref(block)
        block_ref.move(((length - block_length) / 2, (width - block_width) / 2))

    blocks_2_layers = [layer_block, layer_sal_block]
    for layer in blocks_2_layers:
        block_2 = gf.components.rectangle(
            size=(block_2_length, block_2_width),
            layer=layer,
        )
        block_2_ref = c.add_ref(block_2)
        block_2_ref.move(((length - block_2_length) / 2, (width - block_2_width) / 2))

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + gate_poly_end_extension_width / 2), 0),
        width=cont_width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical")

    c.add_port(
        name="P2",
        center=(length / 2 + gate_poly_end_extension_width / 2, 0),
        width=cont_width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical")

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["resistance"] = resistance
    c.info["sheet_resistance"] = sheet_resistance
    c.info["n_squares"] = length / width

    return c


@gf.cell
def rhigh(
    width: float = 0.96,
    length: float = 0.5,
    resistance: float | None = None,
    model: str = "rsil",
    layer_poly: LayerSpec = "PolyResdrawing",
    layer_heat: LayerSpec = "HeatResdrawing",
    layer_gate: LayerSpec = "GatPolydrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_pSD: LayerSpec = "pSDdrawing",
    layer_nSD: LayerSpec = "nSDdrawing",
    layer_block: LayerSpec = "EXTBlockdrawing",
    layer_sal_block: LayerSpec = "SalBlockdrawing",
) -> Component:
    """Create a high-resistance polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_heat: Thermal resistor marker.
        layer_gate: Gate polysilicon layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_metal1_pin: Metal1 pin layer.
        layer_pSD: PSD layer.
        layer_nSD: NSD layer
        layer_block: Blocking layer.
        layer_sal_block: Salicide block layer.

    Returns:
        Component with high-resistance poly resistor layout.
    """
    c = Component()

    # Default parameters
    rppd_min_width = 0.4
    rppd_min_length = 0.5
    sheet_resistance = 300.0
    gate_poly_end_extension_width = 0.43

    # Contact parameters
    cont_width = 0.16
    cont_length = 0.36
    cont_space_x = 0.07
    cont_space_y = 0.20

    # Metal layer parameters
    metal_contact_margin_x = 0.05
    metal_contact_margin_y = 0.05

    # Blocking layer parameters
    block_width = 2.18
    block_length = 0.86
    block_2_width = 0.96
    block_2_length = 0.90

    # Validate dimensions
    width = max(width, rppd_min_width)
    length = max(length, rppd_min_length)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate resistance if not provided
    if resistance is None:
        n_squares = length / width
        resistance = n_squares * sheet_resistance

    # Create resistor body (polysilicon)
    body_layers = [layer_poly, layer_heat]
    for layer in body_layers:
        res_body = gf.components.rectangle(
            size=(length, width),
            layer=layer,
            centered=True,
        )
        res_body_ref = c.add_ref(res_body)
        res_body_ref.move((length / 2, width / 2))

    # End contact regions (gate polysilicon extensions)
    upper_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    upper_ref = c.add_ref(upper_contact)
    upper_ref.move((0, width))

    lower_contact = gf.components.rectangle(
        size=(length, gate_poly_end_extension_width),
        layer=layer_gate,
    )
    lower_ref = c.add_ref(lower_contact)
    lower_ref.move((0, -gate_poly_end_extension_width))

    # Contact regions
    cont_upper = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_upper_ref = c.add_ref(cont_upper)
    cont_upper_ref.move((cont_space_x, width + cont_space_y))

    cont_lower = gf.components.rectangle(
        size=(cont_length, cont_width),
        layer=layer_contact,
    )
    cont_lower_ref = c.add_ref(cont_lower)
    cont_lower_ref.move((cont_space_x, - cont_width - cont_space_y))

    # Metal layer regions
    metal_length = cont_length + 2 * metal_contact_margin_x
    metal_width = cont_width + 2 * metal_contact_margin_y
    metal_space_x = cont_space_x - metal_contact_margin_x
    metal_space_y = cont_space_y - metal_contact_margin_y

    metal_layers = [layer_metal1_pin, layer_metal1]

    for layer in metal_layers:
        metal_upper = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_upper_ref = c.add_ref(metal_upper)
        metal_upper_ref.move((metal_space_x, width + metal_space_y))

        metal_lower = gf.components.rectangle(
            size=(metal_length, metal_width),
            layer=layer,
        )
        metal_lower_ref = c.add_ref(metal_lower)
        metal_lower_ref.move((metal_space_x, - metal_width - metal_space_y))

    # Add blocking layers
    blocks_1_layers = [layer_block, layer_pSD, layer_nSD]
    for layer in blocks_1_layers:
        block = gf.components.rectangle(
            size=(block_length, block_width),
            layer=layer,
        )
        block_ref = c.add_ref(block)
        block_ref.move(((length - block_length) / 2, (width - block_width) / 2))

    blocks_2_layers = [layer_block, layer_sal_block]
    for layer in blocks_2_layers:
        block_2 = gf.components.rectangle(
            size=(block_2_length, block_2_width),
            layer=layer,
        )
        block_2_ref = c.add_ref(block_2)
        block_2_ref.move(((length - block_2_length) / 2, (width - block_2_width) / 2))

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + gate_poly_end_extension_width / 2), 0),
        width=cont_width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical")

    c.add_port(
        name="P2",
        center=(length / 2 + gate_poly_end_extension_width / 2, 0),
        width=cont_width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical")

    # Add metadata
    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["resistance"] = resistance
    c.info["sheet_resistance"] = sheet_resistance
    c.info["n_squares"] = length / width

    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    c0 = fixed.rsil()  # original
    c1 = rsil()  # New
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.rppd()  # original
    # c1 = rppd()  # New
    # c = xor(c0, c1)
    # c.show()

    # c0 = fixed.rhigh()  # original
    # c1 = rhigh()  # New
    # c = xor(c0, c1)
    # c.show()
