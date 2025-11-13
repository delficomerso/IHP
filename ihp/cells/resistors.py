"""Resistor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec


@gf.cell
def rsil(
    width: float = 0.8,
    length: float = 0.5,
    resistance: float | None = None,
    model: str = "rsil",
    layer_poly: LayerSpec = "GatPolydrawing",
    layer_salblock: LayerSpec = "SalBlockdrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_res_mark: LayerSpec = "RESdrawing",
) -> Component:
    """Create a silicided polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_salblock: Salicide block layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_res_mark: Resistor marker layer.

    Returns:
        Component with silicided poly resistor layout.
    """
    c = Component()

    # Design rules
    rsil_min_width = 0.4
    rsil_min_length = 0.8
    sheet_resistance = 7.0  # ohms/square (example)
    cont_size = 0.16
    cont_enc = 0.07
    metal_enc = 0.06
    end_extension = 0.4

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
    res_body = gf.components.rectangle(
        size=(length, width),
        layer=layer_poly,
        centered=True,
    )
    c.add_ref(res_body)

    # Silicide blocking layer
    sil_block = gf.components.rectangle(
        size=(length + 0.2, width + 0.2),
        layer=layer_salblock,
        centered=True,
    )
    c.add_ref(sil_block)

    # End contact regions (polysilicon extensions)
    # Left contact region
    left_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    left_ref = c.add_ref(left_contact)
    left_ref.move((-(length / 2 + end_extension), -width / 2))

    # Right contact region
    right_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    right_ref = c.add_ref(right_contact)
    right_ref.move((length / 2, -width / 2))

    # Contacts at ends
    n_cont_y = int((width - cont_size) / (cont_size + 0.18)) + 1

    for i in range(n_cont_y):
        y_pos = -width / 2 + cont_enc + i * (cont_size + 0.18)

        # Left contact
        cont_left = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_contact,
        )
        cont_left_ref = c.add_ref(cont_left)
        cont_left_ref.move((-(length / 2 + end_extension / 2) - cont_size / 2, y_pos))

        # Right contact
        cont_right = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_contact,
        )
        cont_right_ref = c.add_ref(cont_right)
        cont_right_ref.move(((length / 2 + end_extension / 2) - cont_size / 2, y_pos))

    # Metal1 connections
    # Left metal
    m1_left = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_left_ref = c.add_ref(m1_left)
    m1_left_ref.move(
        (-(length / 2 + end_extension + metal_enc), -width / 2 - metal_enc)
    )

    # Right metal
    m1_right = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_right_ref = c.add_ref(m1_right)
    m1_right_ref.move((length / 2 - metal_enc, -width / 2 - metal_enc))

    # Resistor marker
    res_mark = gf.components.rectangle(
        size=(length + 2 * end_extension + 0.5, width + 0.5),
        layer=layer_res_mark,
        centered=True,
    )
    c.add_ref(res_mark)

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + end_extension), 0),
        width=width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(length / 2 + end_extension, 0),
        width=width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

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
    width: float = 0.8,
    length: float = 10.0,
    resistance: float | None = None,
    model: str = "rppd",
    layer_poly: LayerSpec = "GatPolydrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_polyres: LayerSpec = "PolyResdrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_res_mark: LayerSpec = "RESdrawing",
) -> Component:
    """Create a P+ polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_poly: Polysilicon layer.
        layer_psd: P+ source/drain doping layer.
        layer_polyres: Poly resistor marker layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_res_mark: Resistor marker layer.

    Returns:
        Component with P+ poly resistor layout.
    """
    c = Component()

    # Design rules
    rppd_min_width = 0.4
    rppd_min_length = 0.8
    sheet_resistance = 300.0  # ohms/square (high resistance)
    cont_size = 0.16
    cont_enc = 0.07
    metal_enc = 0.06
    end_extension = 0.4

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
    res_body = gf.components.rectangle(
        size=(length, width),
        layer=layer_poly,
        centered=True,
    )
    c.add_ref(res_body)

    # P+ doping layer
    p_doping = gf.components.rectangle(
        size=(length + 2 * end_extension, width + 0.2),
        layer=layer_psd,
        centered=True,
    )
    c.add_ref(p_doping)

    # RPPD marker layer
    rppd_mark = gf.components.rectangle(
        size=(length, width),
        layer=layer_polyres,
        centered=True,
    )
    c.add_ref(rppd_mark)

    # End contact regions
    # Left contact region
    left_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    left_ref = c.add_ref(left_contact)
    left_ref.move((-(length / 2 + end_extension), -width / 2))

    # Right contact region
    right_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    right_ref = c.add_ref(right_contact)
    right_ref.move((length / 2, -width / 2))

    # Contacts at ends
    n_cont_y = int((width - cont_size) / (cont_size + 0.18)) + 1

    for i in range(n_cont_y):
        y_pos = -width / 2 + cont_enc + i * (cont_size + 0.18)

        # Left contact
        cont_left = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_contact,
        )
        cont_left_ref = c.add_ref(cont_left)
        cont_left_ref.move((-(length / 2 + end_extension / 2) - cont_size / 2, y_pos))

        # Right contact
        cont_right = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_contact,
        )
        cont_right_ref = c.add_ref(cont_right)
        cont_right_ref.move(((length / 2 + end_extension / 2) - cont_size / 2, y_pos))

    # Metal1 connections
    # Left metal
    m1_left = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_left_ref = c.add_ref(m1_left)
    m1_left_ref.move(
        (-(length / 2 + end_extension + metal_enc), -width / 2 - metal_enc)
    )

    # Right metal
    m1_right = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_right_ref = c.add_ref(m1_right)
    m1_right_ref.move((length / 2 - metal_enc, -width / 2 - metal_enc))

    # Resistor marker
    res_mark = gf.components.rectangle(
        size=(length + 2 * end_extension + 0.5, width + 0.5),
        layer=layer_res_mark,
        centered=True,
    )
    c.add_ref(res_mark)

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + end_extension), 0),
        width=width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(length / 2 + end_extension, 0),
        width=width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

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
    width: float = 1.4,
    length: float = 20.0,
    resistance: float | None = None,
    model: str = "rhigh",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_poly: LayerSpec = "GatPolydrawing",
    layer_polyres: LayerSpec = "PolyResdrawing",
    layer_contact: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_res_mark: LayerSpec = "RESdrawing",
) -> Component:
    """Create a high-resistance polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        resistance: Target resistance in ohms (optional).
        model: Device model name.
        layer_nwell: N-well isolation layer.
        layer_poly: Polysilicon layer.
        layer_polyres: Poly resistor marker layer.
        layer_contact: Contact layer.
        layer_metal1: Metal1 layer.
        layer_res_mark: Resistor marker layer.

    Returns:
        Component with high-resistance poly resistor layout.
    """
    c = Component()

    # Design rules
    rhigh_min_width = 1.4
    rhigh_min_length = 5.0
    sheet_resistance = 1350.0  # ohms/square (very high resistance)
    cont_size = 0.16
    cont_enc = 0.07
    metal_enc = 0.06
    end_extension = 0.8
    isolation_enc = 0.5

    # Validate dimensions
    width = max(width, rhigh_min_width)
    length = max(length, rhigh_min_length)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate resistance if not provided
    if resistance is None:
        n_squares = length / width
        resistance = n_squares * sheet_resistance

    # N-Well for isolation
    nwell = gf.components.rectangle(
        size=(
            length + 2 * end_extension + 2 * isolation_enc,
            width + 2 * isolation_enc,
        ),
        layer=layer_nwell,
        centered=True,
    )
    c.add_ref(nwell)

    # Create resistor body (polysilicon)
    res_body = gf.components.rectangle(
        size=(length, width),
        layer=layer_poly,
        centered=True,
    )
    c.add_ref(res_body)

    # High resistance marker
    rhigh_mark = gf.components.rectangle(
        size=(length + 0.2, width + 0.2),
        layer=layer_polyres,
        centered=True,
    )
    c.add_ref(rhigh_mark)

    # End contact regions
    # Left contact region
    left_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    left_ref = c.add_ref(left_contact)
    left_ref.move((-(length / 2 + end_extension), -width / 2))

    # Right contact region
    right_contact = gf.components.rectangle(
        size=(end_extension, width),
        layer=layer_poly,
    )
    right_ref = c.add_ref(right_contact)
    right_ref.move((length / 2, -width / 2))

    # Contacts at ends (larger contacts for high resistance)
    n_cont_x = 2  # Multiple contacts in X for better connection
    n_cont_y = int((width - cont_size) / (cont_size + 0.18)) + 1

    for i in range(n_cont_x):
        for j in range(n_cont_y):
            x_offset = i * (cont_size + 0.18)
            y_pos = -width / 2 + cont_enc + j * (cont_size + 0.18)

            # Left contacts
            cont_left = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_contact,
            )
            cont_left_ref = c.add_ref(cont_left)
            cont_left_ref.move(
                (-(length / 2 + end_extension - cont_enc - x_offset), y_pos)
            )

            # Right contacts
            cont_right = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_contact,
            )
            cont_right_ref = c.add_ref(cont_right)
            cont_right_ref.move(
                (length / 2 + end_extension - cont_enc - cont_size - x_offset, y_pos)
            )

    # Metal1 connections (wider for lower contact resistance)
    # Left metal
    m1_left = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_left_ref = c.add_ref(m1_left)
    m1_left_ref.move(
        (-(length / 2 + end_extension + metal_enc), -width / 2 - metal_enc)
    )

    # Right metal
    m1_right = gf.components.rectangle(
        size=(end_extension + 2 * metal_enc, width + 2 * metal_enc),
        layer=layer_metal1,
    )
    m1_right_ref = c.add_ref(m1_right)
    m1_right_ref.move((length / 2 - metal_enc, -width / 2 - metal_enc))

    # Resistor marker
    res_mark = gf.components.rectangle(
        size=(length + 2 * end_extension + 1.0, width + 1.0),
        layer=layer_res_mark,
        centered=True,
    )
    c.add_ref(res_mark)

    # Add ports
    c.add_port(
        name="P1",
        center=(-(length / 2 + end_extension), 0),
        width=width,
        orientation=180,
        layer=layer_metal1,
        port_type="electrical",
    )

    c.add_port(
        name="P2",
        center=(length / 2 + end_extension, 0),
        width=width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )

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
