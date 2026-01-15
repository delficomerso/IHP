"""VLSIR-Compatible Components, Generated with Claude Code"""

import gdsfactory as gf

# Common port layer for schematic-only elements
SCHEM_LAYER = (250, 0)

@gf.cell
def resistor(resistance: float = 1e3, model: str = "rpoly") -> gf.Component:
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "resistor"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "RESISTOR",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"r": resistance}
    }
    return c


@gf.cell
def capacitor(capacitance: float = 1e-12, model: str = "cpoly") -> gf.Component:
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "capacitor"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "CAPACITOR",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"c": capacitance}
    }
    return c


@gf.cell
def inductor(inductance: float = 1e-9, model: str = "lind") -> gf.Component:
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "inductor"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "INDUCTOR",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"l": inductance}
    }
    return c


@gf.cell
def mos(
    w: float = 1e-6,
    l: float = 100e-9,
    nf: int = 1,
    model: str = "nmos",
    spice_lib: str | None = None,
) -> gf.Component:
    c = gf.Component()
    c.add_port(name="D", center=(0, 1), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="G", center=(-1, 0), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="S", center=(0, -1), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.add_port(name="B", center=(1, 0), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.info["model"] = "mos"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "MOS",
        "spice_lib": spice_lib,
        "port_order": ["D", "G", "S", "B"],
        "port_map" : {},
        "params": {"w": w, "l": l, "nf": nf}
    }
    return c


@gf.cell
def diode(model: str = "diol", area: float = 1e-12, pj: float = 1e-6) -> gf.Component:
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "diode"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "DIODE",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"area": area, "pj": pj}
    }
    return c


@gf.cell
def bipolar(
    model: str = "npn",
    spice_lib: str | None = None,
    area: float = 1.0,
) -> gf.Component:
    c = gf.Component()
    c.add_port(name="C", center=(0, 1), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.add_port(name="B", center=(-1, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="E", center=(0, -1), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="S", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)  # substrate
    c.info["model"] = "bipolar"
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "BIPOLAR",
        "spice_lib": spice_lib,
        "port_order": ["C", "B", "E", "S"],
        "port_map" : {},
        "params": {"area": area}
    }
    return c


@gf.cell
def vsource(dc: float = 0.0, ac: float = 0.0) -> gf.Component:
    """Voltage Source"""
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "vsource"
    c.info["vlsir"] = {
        "model": "vsource",
        "spice_type": "VSOURCE",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"dc": dc, "ac": ac}
    }
    return c


@gf.cell
def isource(dc: float = 0.0, ac: float = 0.0) -> gf.Component:
    """Current Source"""
    c = gf.Component()
    c.add_port(name="p", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "isource"
    c.info["vlsir"] = {
        "model": "isource",
        "spice_type": "ISOURCE",
        "spice_lib": None,
        "port_order": ["p", "n"],
        "port_map" : {},
        "params": {"dc": dc, "ac": ac}
    }
    return c


@gf.cell
def vcvs(gain: float = 1.0) -> gf.Component:
    """Voltage-controlled voltage source."""
    c = gf.Component()
    c.add_port(name="p_out", center=(0, 1), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.add_port(name="n_out", center=(0, -1), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="p_ctrl", center=(-1, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n_ctrl", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "vcvs"
    c.info["vlsir"] = {
        "model": "vcvs",
        "spice_type": "VCVS",
        "spice_lib": None,
        "port_order": ["p_out", "n_out", "p_ctrl", "n_ctrl"],
        "port_map" : {},
        "params": {"gain": gain}
    }
    return c


@gf.cell
def vccs(gm: float = 1e-3) -> gf.Component:
    """Voltage-controlled current source."""
    c = gf.Component()
    c.add_port(name="p_out", center=(0, 1), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.add_port(name="n_out", center=(0, -1), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="p_ctrl", center=(-1, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n_ctrl", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "vccs"
    c.info["vlsir"] = {
        "model": "vccs",
        "spice_type": "VCCS",
        "spice_lib": None,
        "port_order": ["p_out", "n_out", "p_ctrl", "n_ctrl"],
        "port_map" : {},
        "params": {"gm": gm}
    }
    return c


@gf.cell
def cccs(gain: float = 1.0) -> gf.Component:
    """Current-controlled current source."""
    c = gf.Component()
    c.add_port(name="p_out", center=(0, 1), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.add_port(name="n_out", center=(0, -1), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="p_ctrl", center=(-1, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n_ctrl", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "cccs"
    c.info["vlsir"] = {
        "model": "cccs",
        "spice_type": "CCCS",
        "spice_lib": None,
        "port_order": ["p_out", "n_out", "p_ctrl", "n_ctrl"],
        "port_map" : {},
        "params": {"gain": gain}
    }
    return c


@gf.cell
def ccvs(rm: float = 1e3) -> gf.Component:
    """Current-controlled voltage source."""
    c = gf.Component()
    c.add_port(name="p_out", center=(0, 1), width=0.1, orientation=90, layer=SCHEM_LAYER)
    c.add_port(name="n_out", center=(0, -1), width=0.1, orientation=270, layer=SCHEM_LAYER)
    c.add_port(name="p_ctrl", center=(-1, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n_ctrl", center=(1, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "ccvs"
    c.info["vlsir"] = {
        "model": "ccvs",
        "spice_type": "CCVS",
        "spice_lib": None,
        "port_order": ["p_out", "n_out", "p_ctrl", "n_ctrl"],
        "params": {"rm": rm}
    }
    return c


@gf.cell
def tline(z0: float = 50.0, td: float = 1e-9) -> gf.Component:
    """Transmission line."""
    c = gf.Component()
    c.add_port(name="p1", center=(0, 0), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="n1", center=(0, -1), width=0.1, orientation=180, layer=SCHEM_LAYER)
    c.add_port(name="p2", center=(2, 0), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.add_port(name="n2", center=(2, -1), width=0.1, orientation=0, layer=SCHEM_LAYER)
    c.info["model"] = "tline"
    c.info["vlsir"] = {
        "model": "tline",
        "spice_type": "TLINE",
        "spice_lib": None,
        "port_order": ["p1", "n1", "p2", "n2"],
        "params": {"z0": z0, "td": td}
    }
    return c


@gf.cell
def subckt(
    model: str,
    ports: list[str],
    spice_lib: str | None = None,
    params: dict | None = None,
) -> gf.Component:
    """Generic subcircuit wrapper."""
    c = gf.Component()
    
    c.info["model"] = model
    for i, port_name in enumerate(ports):
        c.add_port(
            name=port_name,
            center=(i, 0),
            width=0.1,
            orientation=0 if i % 2 else 180,
            layer=SCHEM_LAYER,
        )
    c.info["vlsir"] = {
        "model": model,
        "spice_type": "SUBCKT",
        "spice_lib": spice_lib,
        "port_order": ports,
        "params": params or {}
    }
    
    return c