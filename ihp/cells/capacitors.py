"""Capacitor components for IHP PDK."""

from math import floor

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from cni.tech import Tech

tech_name = "SG13_dev"
tech = Tech.get("SG13_dev").getTechParams()


@gf.cell
def cmim(
    width: float = 6.99,
    length: float = 6.99,
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
    epsilon = tech["epsilon1"]
    cont_size = tech["TV1_a"]
    cont_over = tech["Mim_d"]
    cont_dist = 0.84  # hardcoded in IHP PDK
    cap_density = 1.5

    # Layers
    layer_metal5: LayerSpec = "Metal5drawing"
    layer_mim: LayerSpec = "MIMdrawing"
    layer_via_mim: LayerSpec = "Vmimdrawing"
    layer_topmetal1: LayerSpec = "TopMetal1drawing"

    # how many vias?
    xanz = (width - cont_over - cont_over + cont_dist) // (
        cont_size + cont_dist
    ) + epsilon
    # width for vias
    w1 = xanz * (cont_size + cont_dist) - cont_dist + cont_over + cont_over
    # offset to first via
    xoffset = tog((width - w1) / 2)

    yanz = (length - cont_over - cont_over + cont_dist) // (
        cont_size + cont_dist
    ) + epsilon
    l1 = yanz * (cont_size + cont_dist) - cont_dist + cont_over + cont_over
    yoffset = tog((length - l1) / 2)

    ycont_cnt = cont_over + yoffset
    # draw vias
    while ycont_cnt + cont_size + cont_over <= length + epsilon:
        xcont_cnt = cont_over + xoffset
        while xcont_cnt + cont_size + cont_over <= width + epsilon:
            c.add_ref(
                gf.components.rectangle(
                    size=(cont_size, cont_size),
                    layer=layer_via_mim,
                )
            ).move((xcont_cnt, ycont_cnt))

            xcont_cnt = xcont_cnt + cont_size + cont_dist

        ycont_cnt = ycont_cnt + cont_size + cont_dist

    # TopMetal1
    xcont_cnt = xcont_cnt + tech["TV1_d"] - cont_dist
    ycont_cnt = ycont_cnt + tech["TV1_d"] - cont_dist

    # MIM dielectric layer
    c.add_ref(
        gf.components.rectangle(
            size=(width, length),
            layer=layer_mim,
        )
    )

    x1 = tech["Mim_d"] - tech["TV1_d"] + xoffset
    x2 = xcont_cnt
    y1 = tech["Mim_d"] - tech["TV1_d"] + yoffset
    y2 = ycont_cnt

    # Top plate (Metal5)
    c.add_ref(
        gf.components.rectangle(
            size=(x2 - x1, y2 - y1),
            layer=layer_topmetal1,
        )
    ).move((x1, y1))

    # Calculate capacitance
    capacitance = width * length * cap_density

    c.add_ref(
        gf.components.rectangle(
            size=(width + 2 * tech["Mim_c"], length + 2 * tech["Mim_c"]),
            layer=layer_metal5,
        )
    ).move((-tech["Mim_c"], -tech["Mim_c"]))

    # Add ports
    c.add_port(
        name="B",
        center=(width / 2, length / 2),
        width=min(
            width + 2 * tech["Mim_c"], length + 2 * tech["Mim_c"]
        ),  # because ports_on_short_side is True
        orientation=0,
        layer=layer_metal5,
        port_type="electrical",
    )

    c.add_port(
        name="T",
        center=((x2 + x1) / 2, (y2 + y1) / 2),
        width=min(x2 - x1, y2 - y1),  # because ports_on_short_side is True
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


def fix(value):
    if type(value) is float:
        return int(floor(value))
    else:
        return value


def tog(x: float) -> float:
    SG13_GRID = 0.005
    SG13_EPSILON = 0.001
    SG13_IGRID = 1.0 / SG13_GRID
    return fix(x * SG13_IGRID + SG13_EPSILON) * SG13_GRID


def contactArray(
    c: gf.Component,
    length: float,
    width: float,
    contactLayer: LayerSpec,
    xl: float,
    yl: float,
    ox: float,
    oy: float,
    ws: float,
    ds: float,
) -> None:
    """
    Distributes as many square contact of size ws, into a rectangle of (length, width), with distances >= ds.
    The distances are adjusted so that the outer contacts have fixed distances ox and oy from the sides of the rectangle.

    Parameters
    ----------
    c : gf.Component
        The GDSFactory component on which the array is placed.
    length : float
        Length (x-dimension) of the region which contains the pin array.
    width : float
        Width (y-dimension) of the region which contains the pin array.
    xl: float
        Minimum x-coordinate of the array that contains the pins.
    yl: float
        Minimum y-coordinate of the array that contains the pins.
    ox: float
        Distance from edge in x direction.
    oy: float
        Distance from edge in y direction.
    ws : float
        Dimension, x and y, of the individual square contact.
    ds: float
        Distance between first column from left edge, last column from right edge, first (bottom) row and bottom edge, and last (top) row and top edge.

    """
    eps = 0.001

    nx = floor((length - ox * 2 + ds) / (ws + ds) + eps)

    dsx = 0
    if nx == 1:
        dsx = 0
    else:
        dsx = (length - ox * 2 - ws * nx) / (nx - 1)

    ny = floor((width - oy * 2 + ds) / (ws + ds) + eps)

    dsy = 0
    if ny == 1:
        dsy = 0
    else:
        dsy = (width - oy * 2 - ws * ny) / (ny - 1)

    x = 0
    if nx == 1:
        x = (length - ws) / 2
    else:
        x = ox

    for _ in range(int(nx)):
        # for(i=1; i<=nx; i++) {
        y = 0
        if ny == 1:
            y = (width - ws) / 2
        else:
            y = oy

        for _ in range(int(ny)):
            # for(j=1; j<=ny; j++) {
            contact_ref = c << gf.components.rectangle(
                size=(ws, ws),
                layer=contactLayer,
            )
            contact_ref.move((tog(x) + xl, tog(y) + yl))

            y = y + ws + dsy

        x = x + ws + dsx


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
    contactArray(
        c=c,
        length=length,
        width=width,
        contactLayer=layer_via_mim,
        xl=0,
        yl=0,
        ox=via_extension,
        oy=via_extension,
        ws=via_size,
        ds=via_dist,
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
    contactArray(
        c=c,
        length=length + 2 * activ_external_extension,
        width=activ_external_extension - activ_internal_extension,
        contactLayer=layer_cont,
        xl=-activ_external_extension,
        yl=width + activ_internal_extension,
        ox=via_over,
        oy=via_over,
        ws=cont_size,
        ds=cont_dist,
    )
    # Bottom extension
    contactArray(
        c=c,
        length=length + 2 * activ_external_extension,
        width=activ_external_extension - activ_internal_extension,
        contactLayer=layer_cont,
        xl=-activ_external_extension,
        yl=-activ_external_extension,
        ox=via_over,
        oy=via_over,
        ws=cont_size,
        ds=cont_dist,
    )
    # Left extension
    contactArray(
        c=c,
        length=activ_external_extension - activ_internal_extension,
        width=width + 2 * activ_internal_extension,
        contactLayer=layer_cont,
        xl=-activ_external_extension,
        yl=-activ_internal_extension,
        ox=via_over,
        oy=via_over,
        ws=cont_size,
        ds=cont_dist,
    )
    # Right bottom extension
    contactArray(
        c=c,
        length=activ_external_extension - activ_internal_extension,
        width=width / 2 + activ_internal_extension - feed_width / 2,
        contactLayer=layer_cont,
        xl=length + activ_internal_extension,
        yl=-activ_internal_extension,
        ox=via_over,
        oy=via_over,
        ws=cont_size,
        ds=cont_dist,
    )
    # Right top extension
    contactArray(
        c=c,
        length=activ_external_extension - activ_internal_extension,
        width=width / 2 + activ_internal_extension - feed_width / 2,
        contactLayer=layer_cont,
        xl=length + activ_internal_extension,
        yl=width / 2 + feed_width / 2,
        ox=via_over,
        oy=via_over,
        ws=cont_size,
        ds=cont_dist,
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
    width = 9.5
    length = 8
    c0 = cells2.cmim(width=width, length=length)  # original
    c1 = cmim(width=width, length=length)  # New

    print(c0.ports)

    print(c1.ports)

    c_cmim = xor(c0, c1)
    c_cmim.draw_ports()
    c_cmim.show()

    # c0_rf = cells2.rfcmim(width=width, length=length)  # original
    # c1_rf = rfcmim(width=width, length=length)  # New
    # c_rfcmim = xor(c0_rf, c1_rf)
    # c_rfcmim.show()
