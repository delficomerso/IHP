"""RF transistor components for IHP PDK.

Pure GDSFactory implementations of RF-MOSFET layouts that replicate the geometry
from the IHP PyCell library (cells2/ihp_pycell/rfmosfet_base_code.py). The RF
layout differs from standard FETs — it uses a bottom-to-top Y-axis orientation
with guard rings, gate rings, and Metal2 connections.
"""

import math

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from .fet_transistors import _add_rect, _even_dbu, _fix, _grid_fix

_EPSILON = 0.001  # local copy to avoid circular concerns


# ---------------------------------------------------------------------------
# RF-specific helper
# ---------------------------------------------------------------------------
def _metal_cont(
    c: Component,
    p1_x: float,
    p1_y: float,
    p2_x: float,
    p2_y: float,
    layer_metal: LayerSpec,
    layer_cont: LayerSpec,
    width: float,
    cont_size: float,
    cont_length: float,
    offset: float,
    cont_space: float,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
):
    """Place contacts along a line with a metal overlay rectangle.

    Replicates MetalCont() from geometry.py. Places sub-rectangles (contacts)
    along a vertical or horizontal line, plus a covering metal rectangle.

    Args:
        c: Component to add geometry to.
        p1_x, p1_y: Start point of the line (raw coordinates).
        p2_x, p2_y: End point of the line (raw coordinates).
        layer_metal: Metal layer for the covering rectangle (empty string to skip).
        layer_cont: Contact/via layer for sub-rectangles.
        width: Width of the metal strip.
        cont_size: Width of each contact square.
        cont_length: Length (height) of each contact square.
        offset: Margin from the ends of the line.
        cont_space: Spacing between contacts.
        shift_x: Additional X offset applied to all placed shapes.
        shift_y: Additional Y offset applied to all placed shapes.
    """
    sx, sy = shift_x, shift_y
    w2 = width / 2

    if p1_x == p2_x:
        # Vertical line
        x_left = p1_x - w2
        x_right = p1_x + w2
        if p1_y < p2_y:
            y_bot = p1_y
            y_top = p2_y
        else:
            y_bot = p2_y
            y_top = p1_y

        sw2 = cont_size / 2
        yl = p1_x - sw2
        xr = p1_x + sw2
        yges = y_top - y_bot - 2 * offset
        nrect = _fix(math.floor((yges + cont_space) / (cont_length + cont_space)))

        if nrect > 1:
            rsp = (yges - nrect * cont_length) / (nrect - 1)
            yy = y_bot + offset
            while yy + cont_length <= y_top - offset + 0.0001:
                _add_rect(
                    c,
                    layer_cont,
                    _grid_fix(sx + yl),
                    _grid_fix(sy + yy),
                    _grid_fix(sx + xr),
                    _grid_fix(sy + yy + cont_length),
                )
                yy = yy + cont_length + rsp
        elif nrect == 1:
            ymb = (y_top + y_bot - cont_length) / 2
            _add_rect(
                c,
                layer_cont,
                _grid_fix(sx + yl),
                _grid_fix(sy + ymb),
                _grid_fix(sx + xr),
                _grid_fix(sy + ymb + cont_length),
            )

    elif p1_y == p2_y:
        # Horizontal line
        y_bot = p1_y - w2
        y_top = p1_y + w2
        if p1_x < p2_x:
            x_left = p1_x
            x_right = p2_x
        else:
            x_left = p2_x
            x_right = p1_x

        sw2 = cont_size / 2
        yb = p1_y - sw2
        yt = p1_y + sw2
        xges = x_right - x_left - 2 * offset
        nrect = _fix(math.floor((xges + cont_space) / (cont_length + cont_space)))

        if nrect > 1:
            rsp = (xges - nrect * cont_length) / (nrect - 1)
            xx = x_left + offset
            while xx + cont_length <= x_right - offset + 0.0001:
                _add_rect(
                    c,
                    layer_cont,
                    _grid_fix(sx + xx),
                    _grid_fix(sy + yb),
                    _grid_fix(sx + xx + cont_length),
                    _grid_fix(sy + yt),
                )
                xx = xx + cont_length + rsp
        elif nrect == 1:
            xml = (x_left + x_right - cont_length) / 2
            _add_rect(
                c,
                layer_cont,
                _grid_fix(sx + xml),
                _grid_fix(sy + yb),
                _grid_fix(sx + xml + cont_length),
                _grid_fix(sy + yt),
            )
    else:
        return

    if layer_metal:
        _add_rect(
            c,
            layer_metal,
            _grid_fix(sx + x_left),
            _grid_fix(sy + y_bot),
            _grid_fix(sx + x_right),
            _grid_fix(sy + y_top),
        )


# ---------------------------------------------------------------------------
# Core RF-MOS layout engine
# ---------------------------------------------------------------------------
def _rf_mos_core(
    width: float,
    length: float,
    nf: int,
    cnt_rows: int = 1,
    met2_cont: bool = True,
    gat_ring: bool = True,
    guard_ring: str = "Yes",
    is_pmos: bool = False,
    is_hv: bool = False,
    layer_gatpoly: LayerSpec = "GatPolydrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal2: LayerSpec = "Metal2drawing",
    layer_via1: LayerSpec = "Via1drawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_thickgateox: LayerSpec = "ThickGateOxdrawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
) -> Component:
    """Core RF-MOS transistor layout matching IHP PyCell rfmosfet_base geometry.

    Constructs layout bottom-to-top: active region, gate fingers, S/D contacts,
    gate ring, guard ring, and substrate isolation layers.
    Exactly replicates rfmosfet_base_code.py genLayout().
    """
    c = Component()

    # -- Dimensions --
    ngi = nf
    W = _grid_fix(width / ngi)
    L = length
    # -- Hardcoded RF design rules (matching rfmosfet_base_code.py) --
    met1_w1 = 0.32
    contW = 0.16
    contS = 0.18
    metWidth = contW + 0.14  # 0.30
    viaW = 0.19
    if W < 1.52:
        viaS = 0.22
    else:
        viaS = 0.29

    # Channel distance, Active end pieces
    dc = (0.38 + 0.03) * cnt_rows - 0.03
    ec = (0.345 + 0.065) * cnt_rows - 0.065
    dce = 0.0
    if L < 0.14 and W >= 1:
        dce = 0.005
        dc = dc + dce * 2
        ec = ec + dce

    # metal1 gatring, guardring width
    wgat = 0.3
    wguard = 0.32
    wpsd = 0.38
    # activ-gatring distance hor/vert
    if cnt_rows > 2:
        dgatx = 0.17
    else:
        dgatx = 0.13
    dgaty = 0.235
    # gatring-guardring distance hor/vert
    dguard = 0.36

    # Active height
    hact = ec + ec + (ngi - 1) * dc + ngi * L

    # -- Compute origin offset --
    # The PyCell builds geometry centered on (0,0) then shifts to normalize.
    # We pre-compute the final bottom-left corner (xl, yb) of the outermost layer
    # and add (-xl, -yb) to all coordinates.
    xl = -dgatx - wgat - dguard - wguard
    yb = -dgaty - wgat - dguard - wguard
    xr = -xl + W
    yt = -yb + hact

    rfnmos = not is_pmos

    if rfnmos:
        d_psd = (wpsd - wguard) / 2
        xl_psd = xl - d_psd
        yb_psd = yb - d_psd
    else:
        xl_psd = xl
        yb_psd = yb

    # ThickGateOx extends further for HV
    if is_hv:
        d_tgo = 0.35 if rfnmos else 0.31
        xl_tgo = xl_psd - d_tgo
        yb_tgo = yb_psd - d_tgo
    else:
        xl_tgo = xl_psd
        yb_tgo = yb_psd

    # NWell for rfpmos extends further
    if not rfnmos:
        d_nw = 0.35 if is_hv else 0.31
        final_xl = xl_tgo - d_nw
        final_yb = yb_tgo - d_nw
    else:
        final_xl = xl_tgo
        final_yb = yb_tgo
    ox = -final_xl  # offset to add to all x coordinates
    oy = -final_yb  # offset to add to all y coordinates

    # -- Active --
    _add_rect(c, layer_activ, ox + 0, oy + 0, ox + W, oy + hact)

    # -- Gate fingers --
    y = ec
    gate_rects = []
    for _i in range(1, ngi + 1):
        _add_rect(
            c,
            layer_gatpoly,
            ox + (-dgatx),
            oy + y,
            ox + (W + dgatx),
            oy + (y + L),
        )
        gate_rects.append((y, y + L))
        y = y + dc + L

    if cnt_rows == 1:
        u = 0.075
    else:
        u = 0.36

    # Left/right vertical gatpoly stripes (connecting gate fingers)
    _add_rect(
        c,
        layer_gatpoly,
        ox + (-dgatx - wgat),
        oy + u,
        ox + (-dgatx),
        oy + (hact - u),
    )
    _add_rect(
        c,
        layer_gatpoly,
        ox + (W + dgatx),
        oy + u,
        ox + (W + dgatx + wgat),
        oy + (hact - u),
    )

    # -- Source/Drain metal + contacts (first finger region) --
    # Build S/D shapes for the first S/D region (below first gate)
    # These are then replicated for each gate finger via copying.

    # For cnt_rows > 1, there's a connecting metal strip
    sd_shapes = []  # Track shapes to be copied

    if cnt_rows > 1:
        sd_shapes.append((layer_metal1, 0.05, 0.015, W - 0.05, ec - 0.05 - dce))

    p1_x = 0.05
    p2_x = W - 0.05
    p1_y = 0.015 + metWidth * 0.5 - 0.01
    p2_y = p1_y
    for _i in range(1, cnt_rows + 1):
        _metal_cont(
            c,
            p1_x,
            p1_y,
            p2_x,
            p2_y,
            layer_metal1,
            layer_cont,
            metWidth - 0.02,
            contW,
            contW,
            0.05,
            contS,
            shift_x=ox,
            shift_y=oy,
        )
        sd_shapes.append(
            (
                "metal_cont",
                p1_x,
                p1_y,
                p2_x,
                p2_y,
                layer_metal1,
                layer_cont,
                metWidth - 0.02,
                contW,
                contW,
                0.05,
                contS,
            )
        )
        p1_y = p1_y + metWidth - 0.02 + 0.13
        p2_y = p1_y

    # Metal2 + Via1 for first S/D region
    if met2_cont:
        if cnt_rows > 1:
            sd_shapes.append((layer_metal2, 0.05, 0.015, W - 0.05, ec - 0.05 - dce))

        p1_x = 0.05
        p2_x = W - 0.05
        p1_y = 0.015 + metWidth * 0.5 - 0.01
        p2_y = p1_y
        for _i in range(1, cnt_rows + 1):
            _metal_cont(
                c,
                p1_x,
                p1_y,
                p2_x,
                p2_y,
                layer_metal2,
                layer_via1,
                viaW + 0.01,
                viaW,
                viaW,
                0.05,
                viaS,
                shift_x=ox,
                shift_y=oy,
            )
            sd_shapes.append(
                (
                    "metal_cont",
                    p1_x,
                    p1_y,
                    p2_x,
                    p2_y,
                    layer_metal2,
                    layer_via1,
                    viaW + 0.01,
                    viaW,
                    viaW,
                    0.05,
                    viaS,
                )
            )
            p1_y = p1_y + metWidth - 0.02 + 0.13
            p2_y = p1_y

    # Draw the first connecting metal strip if cnt_rows > 1
    if cnt_rows > 1:
        _add_rect(
            c,
            layer_metal1,
            ox + 0.05,
            oy + 0.015,
            ox + (W - 0.05),
            oy + (ec - 0.05 - dce),
        )
        if met2_cont:
            _add_rect(
                c,
                layer_metal2,
                ox + 0.05,
                oy + 0.015,
                ox + (W - 0.05),
                oy + (ec - 0.05 - dce),
            )

    # -- Copy S/D structures for subsequent gate fingers --
    # In the PyCell, all non-gate, non-active shapes are copied with
    # an offset of (dc + L) for each finger.
    y_step = dc + L
    for i in range(1, ngi + 1):
        y_offset = y_step * i

        # Copy cnt_rows > 1 metal strips
        if cnt_rows > 1:
            _add_rect(
                c,
                layer_metal1,
                ox + 0.05,
                oy + 0.015 + y_offset,
                ox + (W - 0.05),
                oy + (ec - 0.05 - dce) + y_offset,
            )
            if met2_cont:
                _add_rect(
                    c,
                    layer_metal2,
                    ox + 0.05,
                    oy + 0.015 + y_offset,
                    ox + (W - 0.05),
                    oy + (ec - 0.05 - dce) + y_offset,
                )

        # Copy metal+contact rows
        p1_x = 0.05
        p2_x = W - 0.05
        p1_y = 0.015 + metWidth * 0.5 - 0.01
        p2_y = p1_y
        for _j in range(1, cnt_rows + 1):
            _metal_cont(
                c,
                p1_x,
                p1_y + y_offset,
                p2_x,
                p2_y + y_offset,
                layer_metal1,
                layer_cont,
                metWidth - 0.02,
                contW,
                contW,
                0.05,
                contS,
                shift_x=ox,
                shift_y=oy,
            )
            if met2_cont:
                _metal_cont(
                    c,
                    p1_x,
                    p1_y + y_offset,
                    p2_x,
                    p2_y + y_offset,
                    layer_metal2,
                    layer_via1,
                    viaW + 0.01,
                    viaW,
                    viaW,
                    0.05,
                    viaS,
                    shift_x=ox,
                    shift_y=oy,
                )
            p1_y = p1_y + metWidth - 0.02 + 0.13
            p2_y = p1_y

    # -- Source pin --
    _add_rect(
        c,
        layer_metal1_pin,
        ox + 0.05,
        oy + 0.015,
        ox + (W - 0.05),
        oy + (ec - 0.05 - dce),
    )

    # -- Drain pin --
    _add_rect(
        c,
        layer_metal1_pin,
        ox + 0.05,
        oy + (0.015 + y_step),
        ox + (W - 0.05),
        oy + (ec - 0.05 + y_step - dce),
    )

    # Save port locations for S and D
    src_pin_x1 = ox + 0.05
    src_pin_y1 = oy + 0.015
    src_pin_x2 = ox + (W - 0.05)
    src_pin_y2 = oy + (ec - 0.05 - dce)
    drn_pin_x1 = ox + 0.05
    drn_pin_y1 = oy + (0.015 + y_step)
    drn_pin_x2 = ox + (W - 0.05)
    drn_pin_y2 = oy + (ec - 0.05 + y_step - dce)

    # -- Gate ring --
    if gat_ring:
        # Metal1 ring around gate area
        _add_rect(
            c,
            layer_metal1,
            ox + (-dgatx - wgat),
            oy + (-dgaty - wgat),
            ox + (-dgatx),
            oy + (hact + dgaty + wgat),
        )
        _add_rect(
            c,
            layer_metal1,
            ox + (W + dgatx),
            oy + (-dgaty - wgat),
            ox + (W + dgatx + wgat),
            oy + (hact + dgaty + wgat),
        )
        _add_rect(
            c,
            layer_metal1,
            ox + (-dgatx),
            oy + (-dgaty - wgat),
            ox + (W + dgatx),
            oy + (-dgaty),
        )
        _add_rect(
            c,
            layer_metal1,
            ox + (-dgatx),
            oy + (hact + dgaty),
            ox + (W + dgatx),
            oy + (hact + dgaty + wgat),
        )

    # -- Gate poly-metal1 contacts --
    u_cont = u + 0.02
    # Left side
    p1_x = -dgatx - wgat * 0.5
    p1_y_gc = u_cont
    p2_x = p1_x
    p2_y_gc = hact - u_cont
    _metal_cont(
        c,
        p1_x,
        p1_y_gc,
        p2_x,
        p2_y_gc,
        layer_metal1,
        layer_cont,
        viaW + 0.01,
        contW,
        contW,
        0.05,
        viaS,
        shift_x=ox,
        shift_y=oy,
    )
    # Gate pin on left side
    gat_pin_x1 = ox + (p1_x - 0.1)
    gat_pin_y1 = oy + p1_y_gc
    gat_pin_x2 = ox + (p2_x + 0.1)
    gat_pin_y2 = oy + p2_y_gc
    _add_rect(c, layer_metal1_pin, gat_pin_x1, gat_pin_y1, gat_pin_x2, gat_pin_y2)

    # Right side
    p1_x = W + dgatx + wgat * 0.5
    p2_x = p1_x
    _metal_cont(
        c,
        p1_x,
        p1_y_gc,
        p2_x,
        p2_y_gc,
        layer_metal1,
        layer_cont,
        viaW + 0.01,
        contW,
        contW,
        0.05,
        viaS,
        shift_x=ox,
        shift_y=oy,
    )

    # -- Guard ring --
    # Guard ring: Activ ring + Metal1 contacts
    if guard_ring != "No":
        # Bottom horizontal contact row
        p1_x_gr = xl
        p1_y_gr = yb + wguard * 0.5
        p2_x_gr = xr
        p2_y_gr = p1_y_gr
        _metal_cont(
            c,
            p1_x_gr,
            p1_y_gr,
            p2_x_gr,
            p2_y_gr,
            layer_metal1,
            layer_cont,
            met1_w1,
            contW,
            contW,
            0.08,
            contS,
            shift_x=ox,
            shift_y=oy,
        )
        # TIE pin (bottom)
        tie_pin_x1 = ox + p1_x_gr
        tie_pin_y1 = oy + (p1_y_gr - wguard / 4)
        tie_pin_x2 = ox + p2_x_gr
        tie_pin_y2 = oy + (p2_y_gr + wguard / 4)
        _add_rect(c, layer_metal1_pin, tie_pin_x1, tie_pin_y1, tie_pin_x2, tie_pin_y2)

        # Top horizontal contact row
        p1_y_gr = yt - wguard * 0.5
        p2_y_gr = p1_y_gr
        _metal_cont(
            c,
            p1_x_gr,
            p1_y_gr,
            p2_x_gr,
            p2_y_gr,
            layer_metal1,
            layer_cont,
            met1_w1,
            contW,
            contW,
            0.08,
            contS,
            shift_x=ox,
            shift_y=oy,
        )

    if guard_ring == "Yes":
        # Left vertical contact column
        p1_x_gr = xl + wguard * 0.5
        p2_x_gr = p1_x_gr
        p1_y_gr = yb + wguard
        p2_y_gr = yt - wguard
        _metal_cont(
            c,
            p1_x_gr,
            p1_y_gr,
            p2_x_gr,
            p2_y_gr,
            layer_metal1,
            layer_cont,
            met1_w1,
            contW,
            contW,
            0.11,
            contS,
            shift_x=ox,
            shift_y=oy,
        )

    if guard_ring == "Yes" or guard_ring == "U":
        # Right vertical contact column
        p1_x_gr = xr - wguard * 0.5
        p2_x_gr = p1_x_gr
        p1_y_gr = yb + wguard
        p2_y_gr = yt - wguard
        _metal_cont(
            c,
            p1_x_gr,
            p1_y_gr,
            p2_x_gr,
            p2_y_gr,
            layer_metal1,
            layer_cont,
            met1_w1,
            contW,
            contW,
            0.11,
            contS,
            shift_x=ox,
            shift_y=oy,
        )

    # Guard ring Activ (4 sides, overlapping for merge)
    _add_rect(c, layer_activ, ox + xl, oy + yb, ox + xr, oy + (yb + wguard))
    _add_rect(c, layer_activ, ox + xl, oy + yt, ox + xr, oy + (yt - wguard))
    _add_rect(
        c,
        layer_activ,
        ox + xl,
        oy + (yb + wguard),
        ox + (xl + wguard),
        oy + (yt - wguard),
    )
    _add_rect(
        c,
        layer_activ,
        ox + (xr - wguard),
        oy + (yb + wguard),
        ox + xr,
        oy + (yt - wguard),
    )

    # -- Substrate isolation layers --
    if rfnmos:
        # pSD ring around guard ring
        d = (wpsd - wguard) / 2
        psd_xl = xl - d
        psd_xr = xr + d
        psd_yb = yb - d
        psd_yt = yt + d
        _add_rect(
            c,
            layer_psd,
            ox + psd_xl,
            oy + psd_yb,
            ox + psd_xr,
            oy + (psd_yb + wpsd),
        )
        _add_rect(
            c,
            layer_psd,
            ox + psd_xl,
            oy + psd_yt,
            ox + psd_xr,
            oy + (psd_yt - wpsd),
        )
        _add_rect(
            c,
            layer_psd,
            ox + psd_xl,
            oy + (psd_yb + wpsd),
            ox + (psd_xl + wpsd),
            oy + (psd_yt - wpsd),
        )
        _add_rect(
            c,
            layer_psd,
            ox + (psd_xr - wpsd),
            oy + (psd_yb + wpsd),
            ox + psd_xr,
            oy + (psd_yt - wpsd),
        )
        cur_xl, cur_xr, cur_yb, cur_yt = psd_xl, psd_xr, psd_yb, psd_yt
    else:
        # rfpmos: pSD rect inside guard ring area
        _add_rect(
            c,
            layer_psd,
            ox + (xl + 0.5),
            oy + (yb + 0.6),
            ox + (xr - 0.5),
            oy + (yt - 0.6),
        )
        cur_xl, cur_xr, cur_yb, cur_yt = xl, xr, yb, yt

    # -- ThickGateOx for HV --
    if is_hv:
        if rfnmos:
            d = 0.35
        else:
            d = 0.31
        cur_xl = cur_xl - d
        cur_xr = cur_xr + d
        cur_yb = cur_yb - d
        cur_yt = cur_yt + d
        _add_rect(
            c,
            layer_thickgateox,
            ox + cur_xl,
            oy + cur_yb,
            ox + cur_xr,
            oy + cur_yt,
        )

    # -- NWell for rfpmos --
    if not rfnmos:
        if is_hv:
            d = 0.35
        else:
            d = 0.31
        cur_xl = cur_xl - d
        cur_xr = cur_xr + d
        cur_yb = cur_yb - d
        cur_yt = cur_yt + d
        _add_rect(
            c,
            layer_nwell,
            ox + cur_xl,
            oy + cur_yb,
            ox + cur_xr,
            oy + cur_yt,
        )

    # -- GDSFactory ports --
    m1_layer = (8, 0)  # Metal1 drawing

    # Source port
    s_cx = (src_pin_x1 + src_pin_x2) / 2
    s_cy = (src_pin_y1 + src_pin_y2) / 2
    s_w = src_pin_x2 - src_pin_x1
    c.add_port(
        name="S",
        center=(s_cx, s_cy),
        width=_even_dbu(s_w),
        orientation=270,
        layer=m1_layer,
    )

    # Drain port
    d_cx = (drn_pin_x1 + drn_pin_x2) / 2
    d_cy = (drn_pin_y1 + drn_pin_y2) / 2
    d_w = drn_pin_x2 - drn_pin_x1
    c.add_port(
        name="D",
        center=(d_cx, d_cy),
        width=_even_dbu(d_w),
        orientation=270,
        layer=m1_layer,
    )

    # Gate port
    g_cx = (gat_pin_x1 + gat_pin_x2) / 2
    g_cy = (gat_pin_y1 + gat_pin_y2) / 2
    g_h = gat_pin_y2 - gat_pin_y1
    c.add_port(
        name="G",
        center=(g_cx, g_cy),
        width=_even_dbu(g_h),
        orientation=180,
        layer=m1_layer,
    )

    # TIE port (guard ring)
    if guard_ring != "No":
        c.add_port(
            name="TIE",
            center=((tie_pin_x1 + tie_pin_x2) / 2, (tie_pin_y1 + tie_pin_y2) / 2),
            width=_even_dbu(tie_pin_y2 - tie_pin_y1),
            orientation=270,
            layer=m1_layer,
        )

    return c


# ---------------------------------------------------------------------------
# Public RF cell functions
# ---------------------------------------------------------------------------
@gf.cell
def rfnmos(
    width: float = 1.0,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
    cnt_rows: int = 1,
    met2_cont: bool = True,
    gat_ring: bool = True,
    guard_ring: str = "Yes",
    model: str = "sg13_lv_nmos",
) -> Component:
    """Create an RF NMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        cnt_rows: Number of contact rows.
        met2_cont: Include Metal2-to-contact connections.
        gat_ring: Include gate ring around the transistor.
        guard_ring: Guard ring type: "Yes", "No", "U", or "Top+Bottom".
        model: Device model name.

    Returns:
        Component with RF NMOS transistor layout.
    """
    c = _rf_mos_core(
        width,
        length,
        nf,
        cnt_rows,
        met2_cont,
        gat_ring,
        guard_ring,
        is_pmos=False,
        is_hv=False,
    )
    c.info["vlsir"] = {
        "model": "sg13_lv_nmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
            "rfmode": 1,
        },
    }
    return c


@gf.cell
def rfpmos(
    width: float = 1.0,
    length: float = 0.13,
    nf: int = 1,
    m: int = 1,
    cnt_rows: int = 1,
    met2_cont: bool = True,
    gat_ring: bool = True,
    guard_ring: str = "Yes",
    model: str = "sg13_lv_pmos",
) -> Component:
    """Create an RF PMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        cnt_rows: Number of contact rows.
        met2_cont: Include Metal2-to-contact connections.
        gat_ring: Include gate ring around the transistor.
        guard_ring: Guard ring type: "Yes", "No", "U", or "Top+Bottom".
        model: Device model name.

    Returns:
        Component with RF PMOS transistor layout.
    """
    c = _rf_mos_core(
        width,
        length,
        nf,
        cnt_rows,
        met2_cont,
        gat_ring,
        guard_ring,
        is_pmos=True,
        is_hv=False,
    )
    c.info["vlsir"] = {
        "model": "sg13_lv_pmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moslv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
            "rfmode": 1,
        },
    }
    return c


@gf.cell
def rfnmos_hv(
    width: float = 1.0,
    length: float = 0.45,
    nf: int = 1,
    m: int = 1,
    cnt_rows: int = 1,
    met2_cont: bool = True,
    gat_ring: bool = True,
    guard_ring: str = "Yes",
    model: str = "sg13_hv_nmos",
) -> Component:
    """Create a high-voltage RF NMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        cnt_rows: Number of contact rows.
        met2_cont: Include Metal2-to-contact connections.
        gat_ring: Include gate ring around the transistor.
        guard_ring: Guard ring type: "Yes", "No", "U", or "Top+Bottom".
        model: Device model name.

    Returns:
        Component with HV RF NMOS transistor layout.
    """
    c = _rf_mos_core(
        width,
        length,
        nf,
        cnt_rows,
        met2_cont,
        gat_ring,
        guard_ring,
        is_pmos=False,
        is_hv=True,
    )
    c.info["vlsir"] = {
        "model": "sg13_hv_nmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moshv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
            "rfmode": 1,
        },
    }
    return c


@gf.cell
def rfpmos_hv(
    width: float = 1.0,
    length: float = 0.40,
    nf: int = 1,
    m: int = 1,
    cnt_rows: int = 1,
    met2_cont: bool = True,
    gat_ring: bool = True,
    guard_ring: str = "Yes",
    model: str = "sg13_hv_pmos",
) -> Component:
    """Create a high-voltage RF PMOS transistor.

    Args:
        width: Total width of the transistor in micrometers.
        length: Gate length in micrometers.
        nf: Number of fingers.
        m: Multiplier (number of parallel devices).
        cnt_rows: Number of contact rows.
        met2_cont: Include Metal2-to-contact connections.
        gat_ring: Include gate ring around the transistor.
        guard_ring: Guard ring type: "Yes", "No", "U", or "Top+Bottom".
        model: Device model name.

    Returns:
        Component with HV RF PMOS transistor layout.
    """
    c = _rf_mos_core(
        width,
        length,
        nf,
        cnt_rows,
        met2_cont,
        gat_ring,
        guard_ring,
        is_pmos=True,
        is_hv=True,
    )
    c.info["vlsir"] = {
        "model": "sg13_hv_pmos",
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_moshv_mod.lib",
        "port_order": ["d", "g", "s", "b"],
        "port_map": {"D": "d", "G": "g", "S": "s"},
        "params": {
            "w": width * 1e-6,
            "l": length * 1e-6,
            "ng": nf,
            "m": m,
            "rfmode": 1,
        },
    }
    return c
