"""Capacitor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec


@gf.cell
def cmim(
    width: float = 5.0,
    length: float = 5.0,
) -> Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.

    Returns:
        Component with MIM capacitor layout.
    """
    c = Component()

    # Design rules
    mim_min_size = 0.5
    via_dim = 0.42  # Extracted from PDK
    via_spacing = 2 * via_dim  # Extracted from PDK
    via_extension = via_dim  # Extracted from PDK
    bottom_plate_extension = 0.6  # Extracted from PDK
    cap_density = 1.5  # fF/um^2 (example value)

    # Layers
    layer_metal5: LayerSpec = "Metal5drawing"
    layer_mim: LayerSpec = "MIMdrawing"
    layer_via_mim: LayerSpec = "Vmimdrawing"
    layer_topmetal1: LayerSpec = "TopMetal1drawing"

    # Validate dimensions
    width = max(width, mim_min_size)
    length = max(length, mim_min_size)

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Calculate capacitance
    capacitance = width * length * cap_density

    # Bottom plate (Metal4)
    bottom_plate_width = width + 2 * bottom_plate_extension
    bottom_plate_length = length + 2 * bottom_plate_extension

    bottom_plate = c << gf.components.rectangle(
        size=(bottom_plate_width, bottom_plate_length),
        layer=layer_metal5,
    )
    bottom_plate.xmin = -bottom_plate_extension
    bottom_plate.ymin = -bottom_plate_extension

    # MIM dielectric layer
    c.add_ref(
        gf.components.rectangle(
            size=(width, length),
            layer=layer_mim,
        )
    )

    # The top plate is an extension of the via array, so we create it after the vias.
    # First, the number of vias needs to be defined. They are squares of via_dim, and spacing via_spacing.
    # Let's assume we have a grid of n_x by n_y vias. The top plate will extend this array by via_extension on each side.
    # So the length of the top plate will be:
    # L_top = n_x*via_dim + (n_x-1)*via_spacing + 2*via_extension = 3*n_x*via_dim, for spacing = 2*via_dim and extension = via_dim.
    # The PDK gives the maximum vias for which the top plate dimensions do not exceed the insulator dimensions by more than 0.115um.

    # Via array for top plate connection
    n_vias_x = 1
    n_vias_y = 1

    top_electrode_width = 3 * n_vias_x * via_dim
    top_electrode_length = 3 * n_vias_y * via_dim

    # This condition was found empirically to match the PDK layout
    while top_electrode_width + 3 * via_dim < width + 0.115:
        n_vias_x += 1
        top_electrode_width = 3 * n_vias_x * via_dim
    while top_electrode_length + 3 * via_dim < length + 0.115:
        n_vias_y += 1
        top_electrode_length = 3 * n_vias_y * via_dim

    for i in range(n_vias_x):
        for j in range(n_vias_y):
            # The bottom left corner of the top electrode is at (width - top_electrode_width)/2 - 0.005, (length - top_electrode_length)/2 - 0.005
            x = (
                (width - top_electrode_width) / 2
                - 0.005
                + via_extension
                + i * (via_dim + via_spacing)
            )
            y = (
                (length - top_electrode_length) / 2
                - 0.005
                + via_extension
                + j * (via_dim + via_spacing)
            )

            via = gf.components.rectangle(
                size=(via_dim, via_dim),
                layer=layer_via_mim,
            )
            via_ref = c.add_ref(via)
            via_ref.move((x, y))

    # Top plate (Metal5)
    top_plate = c << gf.components.rectangle(
        size=(top_electrode_width, top_electrode_length),
        layer=layer_topmetal1,
    )
    top_plate.xmin = (width - top_electrode_width) / 2 - 0.005
    top_plate.ymin = (length - top_electrode_length) / 2 - 0.005

    # Add ports
    c.add_port(
        name="B",
        center=(width / 2, length / 2),
        width=width + 2 * bottom_plate_extension,
        orientation=0,
        layer=layer_metal5,
        port_type="electrical",
    )

    c.add_port(
        name="T",
        center=(top_plate.x, top_plate.y),
        width=top_electrode_width,
        orientation=180,
        layer=layer_topmetal1,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = "cmim"
    c.info["width"] = width
    c.info["length"] = length
    c.info["capacitance_fF"] = capacitance
    c.info["area_um2"] = width * length

    return c


def spacing_update_order(n_spacings: int, n_increments: int) -> list[int]:
    """
    The function determines which spacing slots (indices) should receive
    increments. The last spacing always gets incremented first.
    Then the middle, depending on whether the number of increments is odd or even.
    The largest step (gap) between increments is calculated.
    If the middle was increased, then the next increases start happening one step away.
    If the middle was not increased, then the increases start step//2 away from it.

    Parameters
    ----------
    n_spacings : int
        Total number of spacing elements, equal to the number of pins -1.
    n_increments : int
        Number of spacing increments to distribute, in order for the distance from the edges to be fixed on all sides.

    Returns
    -------
    list[int]
        List of spacing indices indicating where increments should be applied.
    """
    if n_increments == 0:
        return []

    chosen = [n_spacings - 1]
    if n_increments == 1:
        return chosen

    n_increments -= 1
    odd = n_spacings % 2 == 1

    # Centers in index space
    if odd:
        left = right = n_spacings // 2
    else:
        left = n_spacings // 2 - 1
        right = left + 1

    center_appended = False
    # Optional center
    if n_increments % 2 == 1:
        chosen.append(left)
        n_increments -= 1
        center_appended = True
        if n_increments == 0:
            return chosen

    k = n_increments // 2

    # Maximum step IGNORING index 0
    step = min(left // k, (n_spacings - 1 - right) // k)
    step = max(step, 1)

    # Try normal symmetric placement
    def generate(start_offset):
        indices = []
        for j in range(k):
            l_idx = left - (start_offset + j * step)
            r_idx = right + (start_offset + j * step)
            indices.extend([l_idx, r_idx])
        return indices

    if center_appended:
        start_offset = step
    else:
        start_offset = step // 2
    # Mode A: start at ±step
    candidates = generate(start_offset=start_offset)
    if all(i != 0 for i in candidates):
        chosen.extend(candidates)
        return chosen

    # Guaranteed fallback (should never fail in valid geometry)
    for j in range(1, k + 1):
        chosen.append(left - j)
        chosen.append(right + j)

    return chosen


def pin_placement(
    c: gf.Component,
    length: float,
    width: float,
    pin_dimension: float,
    pin_spacing_x: float,
    pin_spacing_y: float,
    pin_extension: float,
    bottom_left_x: float,
    bottom_left_y: float,
    pin_layer: LayerSpec,
) -> None:
    """
    This function places a 2D pin array on a rectangle within a component's layer,
    so that the distance of the external rows and columns from the edges is fixed.
    First, the number of pins of specified dimension, spacing, and distance from edges are defined.

    The goal is for all external rows and columns to have a fixed distance from the edges.
    So the next step is to increase, separately, the spacings in x and y direction, in order to bring the last row and column closer to the edge.

    Finally, if there is still space left, some of the spacings are increased by 0.005 until the goal is met.

    Parameters
    ----------
    c : gf.Component
        The GDSFactory component on which the array is placed.
    length : float
        Length (x-dimension) of the region which contains the pin array.
    width : float
        Width (y-dimension) of the region which contains the pin array.
    pin_dimension : float
        Dimension, x and y, of the individual square pin.
    pin_spacing_x: float
        Distance between the right edge of pin in column n, with the left edge of pin in column n+1.
    pin_spacing_y: float
        Distance between the top edge of pin in row m, with the bottom edge of pin in column m+1.
    pin_extension: float
        Distance between first column from left edge, last column from right edge, first (bottom) row and bottom edge, and last (top) row and top edge.
    bottom_left_x: float
        Minimum x-coordinate of the array that contains the pins.
    bottom_left_y: float
        Minimum y-coordinate of the array that contains the pins.

    """
    n_pin_x = 1
    n_pin_y = 1

    pin_array_length = (
        n_pin_x * pin_dimension + (n_pin_x - 1) * pin_spacing_x + 2 * pin_extension
    )
    pin_array_width = (
        n_pin_y * pin_dimension + (n_pin_y - 1) * pin_spacing_y + 2 * pin_extension
    )

    while pin_array_length + pin_dimension + pin_spacing_x <= length:
        n_pin_x += 1
        pin_array_length = (
            n_pin_x * pin_dimension + (n_pin_x - 1) * pin_spacing_x + 2 * pin_extension
        )
    # As long as the expansion is still within the limits
    while pin_array_length + (n_pin_x - 1) * 0.005 <= length:
        pin_spacing_x += 0.005
        pin_array_length = (
            n_pin_x * pin_dimension + (n_pin_x - 1) * pin_spacing_x + 2 * pin_extension
        )

    while pin_array_width + pin_dimension + pin_spacing_y <= width:
        n_pin_y += 1
        pin_array_width = (
            n_pin_y * pin_dimension + (n_pin_y - 1) * pin_spacing_y + 2 * pin_extension
        )
    while pin_array_width + (n_pin_y - 1) * 0.005 <= width:
        pin_spacing_y += 0.005
        pin_array_width = (
            n_pin_y * pin_dimension + (n_pin_y - 1) * pin_spacing_y + 2 * pin_extension
        )

    slack_x = round(length - pin_array_length, 3)
    slack_y = round(width - pin_array_width, 3)

    step = 0.005
    n_spacings_x = n_pin_x - 1
    spacings_x = [pin_spacing_x] * n_spacings_x
    n_spacings_y = n_pin_y - 1
    spacings_y = [pin_spacing_y] * n_spacings_y

    steps_x = int(round(slack_x / step))
    order_x = spacing_update_order(n_spacings_x, steps_x)
    idx = 0
    for _ in range(steps_x):
        spacings_x[order_x[idx]] += step
        idx = (idx + 1) % len(order_x)
    steps_y = int(round(slack_y / step))
    order_y = spacing_update_order(n_spacings_y, steps_y)
    idx = 0
    for _ in range(steps_y):
        spacings_y[order_y[idx]] += step
        idx = (idx + 1) % len(order_y)

    spacings_x.insert(0, 0)  # First via has no spacing before it
    spacings_y.insert(0, 0)  # First via has no spacing before it

    for i in range(n_pin_x):
        for j in range(n_pin_y):
            x = (
                bottom_left_x
                + pin_extension
                + i * pin_dimension
                + sum(spacings_x[: i + 1])
            )
            y = (
                bottom_left_y
                + pin_extension
                + j * pin_dimension
                + sum(spacings_y[: j + 1])
            )
            pin = gf.components.rectangle(
                size=(pin_dimension, pin_dimension),
                layer=pin_layer,
            )
            pin_ref = c.add_ref(pin)
            pin_ref.move((x, y))


@gf.cell
def rfcmim(
    width: float = 6.99,
    length: float = 6.99,
    capacitance: float | None = None,
    feed_width: float = 3,
) -> Component:
    """Create an RF MIM capacitor with optimized layout.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        capacitance: Target capacitance in fF (optional).
        feed_width: Width of the port for both plates of the capacitor.

    Returns:
        Component with RF MIM capacitor layout.
    """
    c = Component()

    # Design rules for RF capacitor
    via_size = 0.42  # Extracted from PDK
    via_dist = 0.42  # Extracted from PDK
    via_extension = 0.78  # Extracted from PDK
    cont_size = 0.16  # Contact dimension from PDK
    cont_dist = 0.18  # Contact spacing from PDK
    # tm_over = 0.42

    mim_over = 0.6
    via_over = 0.36  # Contact extension from PDK

    psd_extra_extension = 0.03  # Additional extension for pSD layer
    pwell_extension = 3.0
    activ_external_extension = 5.6
    activ_internal_extension = 3.6
    caspec = 1.5e-15  # Value from cni.sg13g2.json
    cpspec = 4.0e-17  # Value from cni.sg13g2.json
    lwd = 0.01  # um. Value from cni.sg13g2.json

    layer_activ: LayerSpec = "Activdrawing"
    layer_activ_noqrc: LayerSpec = "Activnoqrc"
    layer_cont: LayerSpec = "Contdrawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_metal1_noqrc: LayerSpec = "Metal1noqrc"
    layer_metal1_pin: LayerSpec = "Metal1pin"
    layer_metal2_noqrc: LayerSpec = "Metal2noqrc"
    layer_psd: LayerSpec = "pSDdrawing"
    layer_metal3_noqrc: LayerSpec = "Metal3noqrc"
    layer_mim: LayerSpec = "MIMdrawing"
    layer_pwellblock: LayerSpec = "PWellblock"
    layer_metal4_noqrc: LayerSpec = "Metal4noqrc"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_metal5: LayerSpec = "Metal5drawing"
    layer_metal5_noqrc: LayerSpec = "Metal5noqrc"
    layer_metal5_pin: LayerSpec = "Metal5pin"
    layer_topmetal1: LayerSpec = "TopMetal1drawing"
    layer_topmetal1_noqrc: LayerSpec = "TopMetal1noqrc"
    layer_topmetal1_pin: LayerSpec = "TopMetal1pin"
    layer_via_mim: LayerSpec = "Vmimdrawing"

    # Grid snap
    grid = 0.005
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # Capacitance Calculation
    leff = length + lwd
    weff = width + lwd
    capacitance = leff * weff * caspec + 2.0 * (leff + weff) * cpspec

    # The top plate is an extension of the via array, so we create it after the vias.
    # First, the number of vias needs to be defined. They are squares of via_dim, and spacing via_spacing.
    # Let's assume we have a grid of n_x by n_y vias. The top plate will extend this array by via_extension on each side.
    # So the length of the top plate will be:
    # L_top = n_x*via_dim + (n_x-1)*via_spacing + 2*via_extension = 3*n_x*via_dim, for spacing = 2*via_dim and extension = via_dim.
    # The PDK gives the maximum vias for which the top plate dimensions do not exceed the insulator dimensions by more than 0.115um.

    # 1 Vias
    pin_placement(
        c,
        length,
        width,
        via_size,
        via_dist,
        via_dist,
        via_extension,
        0,
        0,
        layer_via_mim,
    )

    # 2 MIM dielectric layer
    c.add_ref(
        gf.components.rectangle(
            size=(length, width),
            layer=layer_mim,
        )
    )
    # 3 TopMetal1 internal
    top_metal1_internal = c << gf.components.rectangle(
        size=(length - 2 * via_over, width - 2 * via_over),
        layer=layer_topmetal1,
    )
    top_metal1_internal.xmin = via_over
    top_metal1_internal.ymin = via_over

    # 4 Metal5 internal
    metal5_internal = c << gf.components.rectangle(
        size=(length + 2 * mim_over, width + 2 * mim_over),
        layer=layer_metal5,
    )
    metal5_internal.xmin = -mim_over
    metal5_internal.ymin = -mim_over

    # 5 PWellblock
    pwell = c << gf.components.rectangle(
        size=(length + 2 * pwell_extension, width + 2 * pwell_extension),
        layer=layer_pwellblock,
    )
    pwell.xmin = -pwell_extension
    pwell.ymin = -pwell_extension

    # 6 More TopMetal1
    top_metal1_line = c << gf.components.rectangle(
        size=(activ_external_extension + via_over, feed_width),
        layer=layer_topmetal1,
    )
    top_metal1_line.xmin = -activ_external_extension
    top_metal1_line.ymin = width / 2 - feed_width / 2

    top_metal1_pin = c << gf.components.rectangle(
        size=(activ_external_extension - activ_internal_extension, feed_width),
        layer=layer_topmetal1_pin,
    )
    top_metal1_pin.xmin = -activ_external_extension
    top_metal1_pin.ymin = width / 2 - feed_width / 2

    # Noqrc layers
    activ_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_activ_noqrc,
    )
    activ_noqrc.xmin = -activ_external_extension
    activ_noqrc.ymin = -activ_external_extension

    metal1_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_metal1_noqrc,
    )
    metal1_noqrc.xmin = -activ_external_extension
    metal1_noqrc.ymin = -activ_external_extension

    metal2_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_metal2_noqrc,
    )
    metal2_noqrc.xmin = -activ_external_extension
    metal2_noqrc.ymin = -activ_external_extension

    metal3_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_metal3_noqrc,
    )
    metal3_noqrc.xmin = -activ_external_extension
    metal3_noqrc.ymin = -activ_external_extension

    metal4_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_metal4_noqrc,
    )
    metal4_noqrc.xmin = -activ_external_extension
    metal4_noqrc.ymin = -activ_external_extension

    metal5_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_metal5_noqrc,
    )
    metal5_noqrc.xmin = -activ_external_extension
    metal5_noqrc.ymin = -activ_external_extension

    top_metal1_noqrc = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            width + 2 * activ_external_extension,
        ),
        layer=layer_topmetal1_noqrc,
    )
    top_metal1_noqrc.xmin = -activ_external_extension
    top_metal1_noqrc.ymin = -activ_external_extension

    c.add_polygon(
        [
            (-activ_internal_extension, -activ_internal_extension),
            (-activ_internal_extension, width + activ_internal_extension),
            (length + activ_internal_extension, width + activ_internal_extension),
            (length + activ_internal_extension, width / 2 + feed_width / 2),
            (length + activ_external_extension, width / 2 + feed_width / 2),
            (length + activ_external_extension, width + activ_external_extension),
            (-activ_external_extension, width + activ_external_extension),
            (-activ_external_extension, -activ_external_extension),
            (length + activ_external_extension, -activ_external_extension),
            (length + activ_external_extension, width / 2 - feed_width / 2),
            (length + activ_internal_extension, width / 2 - feed_width / 2),
            (length + activ_internal_extension, -activ_internal_extension),
        ],
        layer=layer_activ,
    )

    metal5_pin = c << gf.components.rectangle(
        size=(activ_external_extension - activ_internal_extension, feed_width),
        layer=layer_metal5_pin,
    )
    metal5_pin.xmin = length + activ_internal_extension
    metal5_pin.ymin = width / 2 - feed_width / 2

    c.add_polygon(
        [
            (
                -activ_external_extension - psd_extra_extension,
                width + activ_internal_extension - psd_extra_extension,
            ),
            (
                -activ_external_extension - psd_extra_extension,
                -activ_external_extension - psd_extra_extension,
            ),
            (
                length + activ_external_extension + psd_extra_extension,
                -activ_external_extension - psd_extra_extension,
            ),
            (
                length + activ_external_extension + psd_extra_extension,
                width + activ_external_extension + psd_extra_extension,
            ),
            (
                -activ_external_extension - psd_extra_extension,
                width + activ_external_extension + psd_extra_extension,
            ),
            (
                -activ_external_extension - psd_extra_extension,
                width + activ_internal_extension - psd_extra_extension,
            ),
            (
                length + activ_internal_extension - psd_extra_extension,
                width + activ_internal_extension - psd_extra_extension,
            ),
            (
                length + activ_internal_extension - psd_extra_extension,
                -activ_internal_extension + psd_extra_extension,
            ),
            (
                -activ_internal_extension + psd_extra_extension,
                -activ_internal_extension + psd_extra_extension,
            ),
            (
                -activ_internal_extension + psd_extra_extension,
                width + activ_internal_extension - psd_extra_extension,
            ),
        ],
        layer=layer_psd,
    )

    c.add_polygon(
        [
            (-activ_internal_extension, -activ_internal_extension),
            (-activ_internal_extension, width + activ_internal_extension),
            (length + activ_internal_extension, width + activ_internal_extension),
            (length + activ_internal_extension, width / 2 + feed_width / 2),
            (length + activ_external_extension, width / 2 + feed_width / 2),
            (length + activ_external_extension, width + activ_external_extension),
            (-activ_external_extension, width + activ_external_extension),
            (-activ_external_extension, -activ_external_extension),
            (length + activ_external_extension, -activ_external_extension),
            (length + activ_external_extension, width / 2 - feed_width / 2),
            (length + activ_internal_extension, width / 2 - feed_width / 2),
            (length + activ_internal_extension, -activ_internal_extension),
        ],
        layer=layer_metal1,
    )

    # Top extension
    pin_placement(
        c,
        length + 2 * activ_external_extension,
        activ_external_extension - activ_internal_extension,
        cont_size,
        cont_dist,
        cont_dist,
        via_over,
        -activ_external_extension,
        width + activ_internal_extension,
        layer_cont,
    )
    # Bottom extension
    pin_placement(
        c,
        length + 2 * activ_external_extension,
        activ_external_extension - activ_internal_extension,
        cont_size,
        cont_dist,
        cont_dist,
        via_over,
        -activ_external_extension,
        -activ_external_extension,
        layer_cont,
    )

    # Left extension
    pin_placement(
        c,
        activ_external_extension - activ_internal_extension,
        width + 2 * activ_internal_extension,
        cont_size,
        cont_dist,
        cont_dist,
        via_over,
        -activ_external_extension,
        -activ_internal_extension,
        layer_cont,
    )
    # Right bottom extension
    pin_placement(
        c,
        activ_external_extension - activ_internal_extension,
        width / 2 + activ_internal_extension - feed_width / 2,
        cont_size,
        cont_dist,
        cont_dist,
        via_over,
        length + activ_internal_extension,
        -activ_internal_extension,
        layer_cont,
    )
    # Right top extension
    pin_placement(
        c,
        activ_external_extension - activ_internal_extension,
        width / 2 + activ_internal_extension - feed_width / 2,
        cont_size,
        cont_dist,
        cont_dist,
        via_over,
        length + activ_internal_extension,
        width / 2 + feed_width / 2,
        layer_cont,
    )

    # ----------------
    # Metal 1 pin
    # ----------------
    metal1_pin = c << gf.components.rectangle(
        size=(
            length + 2 * activ_external_extension,
            activ_external_extension - activ_internal_extension,
        ),
        layer=layer_metal1_pin,
    )
    metal1_pin.xmin = -activ_external_extension
    metal1_pin.ymin = -activ_external_extension

    c.add_polygon(
        [
            (length + mim_over, width / 2 + feed_width / 2),
            (length + mim_over, width / 2 - feed_width / 2),
            (length + activ_external_extension, width / 2 - feed_width / 2),
            (length + activ_external_extension, width / 2 + feed_width / 2),
        ],
        layer=layer_metal5,
    )

    # Add ports
    c.add_port(
        name="TIE",
        center=(
            length / 2,
            -activ_internal_extension / 2 - activ_external_extension / 2,
        ),
        width=activ_external_extension - activ_internal_extension,
        orientation=180,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="MINUS",
        center=(
            length + activ_internal_extension / 2 + activ_external_extension / 2,
            width / 2,
        ),
        width=feed_width / 2,
        orientation=0,
        layer=layer_metal5_pin,
        port_type="electrical",
    )

    c.add_port(
        name="PLUS",
        center=(
            -activ_internal_extension / 2 - activ_external_extension / 2,
            width / 2,
        ),
        width=feed_width / 2,
        orientation=180,
        layer=layer_topmetal1_pin,
        port_type="electrical",
    )

    c.add_label("rfcmim", layer=layer_text, position=(length / 2, width + 2.0))
    c.add_label(
        "MINUS",
        layer=layer_text,
        position=(
            length + activ_external_extension / 2 + activ_internal_extension / 2,
            width / 2,
        ),
    )
    c.add_label(
        "PLUS",
        layer=layer_text,
        position=(
            -activ_external_extension / 2 - activ_internal_extension / 2,
            width / 2,
        ),
    )
    c.add_label(
        "TIE",
        layer=layer_text,
        position=(
            length / 2,
            -activ_external_extension / 2 - activ_internal_extension / 2,
        ),
    )
    c.add_label(
        f"C={round(capacitance * 1e15)}f", layer=layer_text, position=(length / 2, -2.0)
    )

    # Add metadata
    c.info["model"] = "rfcmim"
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
    width = 6.99
    length = 6.99
    # c0 = cells2.cmim(width=width, length=length)  # original
    # c1 = cmim(width=width, length=length)  # New
    # # c = gf.grid([c0, c1], spacing=100)

    # c_cmim = xor(c0, c1)
    # c_cmim.show()

    c0_rf = cells2.rfcmim(width=width, length=length)  # original
    c1_rf = rfcmim(width=width, length=length)  # New
    c_rfcmim = xor(c0_rf, c1_rf)
    c_rfcmim.show()
