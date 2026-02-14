"""Bipolar transistor components for IHP PDK."""

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec


@gf.cell
def npn13G2(
    emitter_width: float = 0.07,
    emitter_length: float = 0.9,
    model: str = "npn13G2",
    m: int = 1,
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_pwell: LayerSpec = "PWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_trans: LayerSpec = "TRANSdrawing",
) -> Component:
    """Create an NPN13G2 bipolar transistor.

    Args:
        emitter_width: Emitter width in micrometers.
        emitter_length: Emitter length in micrometers.
        model: Device model name.
        m: Multiplier (number of parallel devices).
        layer_nwell: N-Well layer.
        layer_pwell: P-Well layer.
        layer_activ: Active area layer.
        layer_psd: P+ source/drain doping layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_trans: Transistor marker layer.

    Returns:
        Component with NPN bipolar transistor layout.
    """
    c = Component()

    # Design rules
    emitter_min_width = 0.07
    emitter_min_length = 0.84
    base_enclosure = 0.1
    collector_enclosure = 0.6
    cont_size = 0.16
    cont_spacing = 0.18
    cont_enc_active = 0.07
    cont_enc_metal = 0.06
    nwell_enclosure = 0.31

    # Validate and adjust dimensions
    em_width = max(emitter_width, emitter_min_width)
    em_length = max(emitter_length, emitter_min_length)

    # Grid snap
    grid = 0.005
    em_width = round(em_width / grid) * grid
    em_length = round(em_length / grid) * grid

    # Calculate component dimensions
    base_width = em_width + 2 * base_enclosure
    base_length = em_length + 2 * base_enclosure
    collector_width = base_width + 2 * collector_enclosure
    collector_length = base_length + 2 * collector_enclosure

    # Collector N-Well (outermost)
    nwell = gf.components.rectangle(
        size=(
            collector_length + 2 * nwell_enclosure,
            collector_width + 2 * nwell_enclosure,
        ),
        layer=layer_nwell,
        centered=True,
    )
    c.add_ref(nwell)

    # Collector active region (N+ ring)
    collector_ring_outer = gf.components.rectangle(
        size=(collector_length, collector_width),
        layer=layer_activ,
        centered=True,
    )
    collector_ring_inner = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_activ,
        centered=True,
    )
    collector = gf.boolean(
        collector_ring_outer, collector_ring_inner, "A-B", layer=layer_activ
    )
    c.add_ref(collector)

    # N+ implant for collector
    nsd_collector = gf.boolean(
        collector_ring_outer, collector_ring_inner, "A-B", layer=layer_nsd
    )
    c.add_ref(nsd_collector)

    # Base P-Well
    pwell = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_pwell,
        centered=True,
    )
    c.add_ref(pwell)

    # Base active region (P+ ring)
    base_ring_outer = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_activ,
        centered=True,
    )
    base_ring_inner = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_activ,
        centered=True,
    )
    base = gf.boolean(base_ring_outer, base_ring_inner, "A-B", layer=layer_activ)
    c.add_ref(base)

    # P+ implant for base
    psd_base = gf.boolean(base_ring_outer, base_ring_inner, "A-B", layer=layer_psd)
    c.add_ref(psd_base)

    # Emitter active region (N+)
    emitter = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_activ,
        centered=True,
    )
    c.add_ref(emitter)

    # N+ implant for emitter
    nsd_emitter = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_nsd,
        centered=True,
    )
    c.add_ref(nsd_emitter)

    # Add contacts for emitter
    n_cont_x = int((em_length - cont_size) / cont_spacing) + 1
    n_cont_y = int((em_width - cont_size) / cont_spacing) + 1

    for i in range(n_cont_x):
        for j in range(n_cont_y):
            x = -em_length / 2 + cont_enc_active + i * cont_spacing
            y = -em_width / 2 + cont_enc_active + j * cont_spacing

            cont = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
            )
            cont_ref = c.add_ref(cont)
            cont_ref.move((x, y))

    # Emitter metal
    emitter_metal = gf.components.rectangle(
        size=(
            em_length - 2 * cont_enc_active + 2 * cont_enc_metal,
            em_width - 2 * cont_enc_active + 2 * cont_enc_metal,
        ),
        layer=layer_metal1,
        centered=True,
    )
    c.add_ref(emitter_metal)

    # Add base contacts (ring around emitter)
    base_cont_y = base_width / 2 - base_enclosure / 2
    for i in range(4):  # Simplified: 4 contacts on each side
        if i % 2 == 0:  # Top and bottom
            x = 0
            y = base_cont_y if i == 0 else -base_cont_y
        else:  # Left and right
            x = base_cont_y if i == 1 else -base_cont_y
            y = 0

        cont = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_cont,
            centered=True,
        )
        cont_ref = c.add_ref(cont)
        cont_ref.move((x, y))

        # Base metal contact
        m1 = gf.components.rectangle(
            size=(cont_size + 2 * cont_enc_metal, cont_size + 2 * cont_enc_metal),
            layer=layer_metal1,
            centered=True,
        )
        m1_ref = c.add_ref(m1)
        m1_ref.move((x, y))

    # Add collector contacts (outer ring)
    coll_cont_y = collector_width / 2 - collector_enclosure / 2
    for i in range(4):  # Simplified: 4 contacts on each side
        if i % 2 == 0:  # Top and bottom
            x = 0
            y = coll_cont_y if i == 0 else -coll_cont_y
        else:  # Left and right
            x = coll_cont_y if i == 1 else -coll_cont_y
            y = 0

        cont = gf.components.rectangle(
            size=(cont_size, cont_size),
            layer=layer_cont,
            centered=True,
        )
        cont_ref = c.add_ref(cont)
        cont_ref.move((x, y))

        # Collector metal contact
        m1 = gf.components.rectangle(
            size=(cont_size + 2 * cont_enc_metal, cont_size + 2 * cont_enc_metal),
            layer=layer_metal1,
            centered=True,
        )
        m1_ref = c.add_ref(m1)
        m1_ref.move((x, y))

    # Transistor marker layer
    trans_marker = gf.components.rectangle(
        size=(collector_length, collector_width),
        layer=layer_trans,
        centered=True,
    )
    c.add_ref(trans_marker)

    # Add ports
    c.add_port(
        name="E",
        center=(0, 0),
        width=em_width,
        orientation=0,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="B",
        center=(0, base_width / 2),
        width=cont_size,
        orientation=90,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="C",
        center=(collector_length / 2, 0),
        width=cont_size,
        orientation=0,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["emitter_width"] = emitter_width
    c.info["emitter_length"] = emitter_length
    c.info["m"] = m
    c.info["type"] = "npn"

    # VLSIR Simulation Metadata
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_hbt_mod.lib",
        "port_order": ["c", "b", "e"],
        "port_map": {"C": "c", "B": "b", "E": "e"},
        "params": {"we": emitter_width * 1e-6, "le": emitter_length * 1e-6, "m": m},
    }

    return c


@gf.cell
def npn13G2L(
    emitter_width: float = 0.07,
    emitter_length: float = 1.26,
    model: str = "npn13G2l",  # Lowercase l to match SPICE
    m: int = 1,
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_pwell: LayerSpec = "PWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_trans: LayerSpec = "TRANSdrawing",
) -> Component:
    """Create an NPN13G2L (low-current) bipolar transistor.

    Args:
        emitter_width: Emitter width in micrometers.
        emitter_length: Emitter length in micrometers.
        model: Device model name.
        m: Multiplier (number of parallel devices).
        layer_nwell: N-Well layer.
        layer_pwell: P-Well layer.
        layer_activ: Active area layer.
        layer_psd: P+ source/drain doping layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_trans: Transistor marker layer.

    Returns:
        Component with NPN bipolar transistor layout.
    """
    return npn13G2(
        emitter_width=emitter_width,
        emitter_length=emitter_length,
        model=model,
        m=m,
        layer_nwell=layer_nwell,
        layer_pwell=layer_pwell,
        layer_activ=layer_activ,
        layer_psd=layer_psd,
        layer_nsd=layer_nsd,
        layer_cont=layer_cont,
        layer_metal1=layer_metal1,
        layer_trans=layer_trans,
    )


@gf.cell
def npn13G2V(
    emitter_width: float = 0.12,
    emitter_length: float = 0.9,
    model: str = "npn13G2v",  # lower-case v to match SPICE
    m: int = 1,
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_pwell: LayerSpec = "PWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_trans: LayerSpec = "TRANSdrawing",
) -> Component:
    """Create an NPN13G2V (varactor) bipolar transistor.

    Args:
        emitter_width: Emitter width in micrometers.
        emitter_length: Emitter length in micrometers.
        model: Device model name.
        m: Multiplier (number of parallel devices).
        layer_nwell: N-Well layer.
        layer_pwell: P-Well layer.
        layer_activ: Active area layer.
        layer_psd: P+ source/drain doping layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_trans: Transistor marker layer.

    Returns:
        Component with NPN bipolar transistor layout.
    """
    return npn13G2(
        emitter_width=emitter_width,
        emitter_length=emitter_length,
        model=model,
        m=m,
        layer_nwell=layer_nwell,
        layer_pwell=layer_pwell,
        layer_activ=layer_activ,
        layer_psd=layer_psd,
        layer_nsd=layer_nsd,
        layer_cont=layer_cont,
        layer_metal1=layer_metal1,
        layer_trans=layer_trans,
    )


@gf.cell
def pnpMPA(
    emitter_width: float = 0.4,
    emitter_length: float = 0.4,
    model: str = "pnpMPA",
    m: int = 1,
    layer_nwell: LayerSpec = "NWelldrawing",
    layer_pwell: LayerSpec = "PWelldrawing",
    layer_activ: LayerSpec = "Activdrawing",
    layer_psd: LayerSpec = "pSDdrawing",
    layer_nsd: LayerSpec = "nSDdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_metal1_pin: LayerSpec = "Metal1pin",
    layer_trans: LayerSpec = "TRANSdrawing",
) -> Component:
    """Create a PNP MPA bipolar transistor.

    Args:
        emitter_width: Emitter width in micrometers.
        emitter_length: Emitter length in micrometers.
        model: Device model name.
        m: Multiplier (number of parallel devices).
        layer_nwell: N-Well layer.
        layer_pwell: P-Well layer.
        layer_activ: Active area layer.
        layer_psd: P+ source/drain doping layer.
        layer_nsd: N+ source/drain doping layer.
        layer_cont: Contact layer.
        layer_metal1: Metal1 layer.
        layer_trans: Transistor marker layer.

    Returns:
        Component with PNP bipolar transistor layout.
    """
    c = Component()

    # Design rules
    emitter_min_size = 0.4
    base_enclosure = 0.15
    collector_enclosure = 0.8
    cont_size = 0.16
    cont_spacing = 0.18
    cont_enc_active = 0.07
    cont_enc_metal = 0.06
    pwell_enclosure = 0.31

    # Validate and adjust dimensions
    em_width = max(emitter_width, emitter_min_size)
    em_length = max(emitter_length, emitter_min_size)

    # Grid snap
    grid = 0.005
    em_width = round(em_width / grid) * grid
    em_length = round(em_length / grid) * grid

    # Calculate component dimensions
    base_width = em_width + 2 * base_enclosure
    base_length = em_length + 2 * base_enclosure
    collector_width = base_width + 2 * collector_enclosure
    collector_length = base_length + 2 * collector_enclosure

    # Collector P-Well (outermost)
    pwell = gf.components.rectangle(
        size=(
            collector_length + 2 * pwell_enclosure,
            collector_width + 2 * pwell_enclosure,
        ),
        layer=layer_pwell,
        centered=True,
    )
    c.add_ref(pwell)

    # Collector active region (P+ ring)
    collector_ring_outer = gf.components.rectangle(
        size=(collector_length, collector_width),
        layer=layer_activ,
        centered=True,
    )
    collector_ring_inner = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_activ,
        centered=True,
    )
    collector = gf.boolean(
        collector_ring_outer, collector_ring_inner, "A-B", layer=layer_activ
    )
    c.add_ref(collector)

    # P+ implant for collector
    psd_collector = gf.boolean(
        collector_ring_outer, collector_ring_inner, "A-B", layer=layer_psd
    )
    c.add_ref(psd_collector)

    # Base N-Well
    nwell = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_nwell,
        centered=True,
    )
    c.add_ref(nwell)

    # Base active region (N+ ring)
    base_ring_outer = gf.components.rectangle(
        size=(base_length, base_width),
        layer=layer_activ,
        centered=True,
    )
    base_ring_inner = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_activ,
        centered=True,
    )
    base = gf.boolean(base_ring_outer, base_ring_inner, "A-B", layer=layer_activ)
    c.add_ref(base)

    # N+ implant for base
    nsd_base = gf.boolean(base_ring_outer, base_ring_inner, "A-B", layer=layer_nsd)
    c.add_ref(nsd_base)

    # Emitter active region (P+)
    emitter = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_activ,
        centered=True,
    )
    c.add_ref(emitter)

    # P+ implant for emitter
    psd_emitter = gf.components.rectangle(
        size=(em_length, em_width),
        layer=layer_psd,
        centered=True,
    )
    c.add_ref(psd_emitter)

    # Add contacts for emitter
    n_cont_x = int((em_length - cont_size) / cont_spacing) + 1
    n_cont_y = int((em_width - cont_size) / cont_spacing) + 1

    for i in range(n_cont_x):
        for j in range(n_cont_y):
            x = -em_length / 2 + cont_enc_active + i * cont_spacing
            y = -em_width / 2 + cont_enc_active + j * cont_spacing

            cont = gf.components.rectangle(
                size=(cont_size, cont_size),
                layer=layer_cont,
            )
            cont_ref = c.add_ref(cont)
            cont_ref.move((x, y))

    # Emitter metal
    emitter_metal = gf.components.rectangle(
        size=(
            em_length - 2 * cont_enc_active + 2 * cont_enc_metal,
            em_width - 2 * cont_enc_active + 2 * cont_enc_metal,
        ),
        layer=layer_metal1,
        centered=True,
    )
    c.add_ref(emitter_metal)

    # Transistor marker layer
    trans_marker = gf.components.rectangle(
        size=(collector_length, collector_width),
        layer=layer_trans,
        centered=True,
    )
    c.add_ref(trans_marker)

    # Add ports
    c.add_port(
        name="E",
        center=(0, 0),
        width=em_width,
        orientation=0,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="B",
        center=(0, base_width / 2),
        width=cont_size,
        orientation=90,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    c.add_port(
        name="C",
        center=(collector_length / 2, 0),
        width=cont_size,
        orientation=0,
        layer=layer_metal1_pin,
        port_type="electrical",
    )

    # Add metadata
    c.info["model"] = model
    c.info["emitter_width"] = emitter_width
    c.info["emitter_length"] = emitter_length
    c.info["m"] = m
    c.info["type"] = "pnp"

    # VLSIR Simulation Metadata
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "SUBCKT",
        "spice_lib": "sg13g2_hbt_mod.lib",
        "port_order": ["c", "b", "e"],
        "port_map": {"C": "c", "B": "b", "E": "e"},
        "params": {"we": emitter_width * 1e-6, "le": emitter_length * 1e-6, "m": m},
    }

    return c


if __name__ == "__main__":
    # Test the components
    # c1 = npn13G2(emitter_width=0.07, emitter_length=0.9)
    # c1.show()

    # c2 = pnpMPA(emitter_width=0.4, emitter_length=0.4)
    # c2.show()

    from gdsfactory.difftest import xor

    from ihp import PDK
    from ihp.cells import fixed

    PDK.activate()

    # Test the components
    c0 = fixed.npn13G2()  # original
    c1 = npn13G2()  # New
    # c = gf.grid([c0, c1], spacing=100)
    c = xor(c0, c1)
    c.show()
