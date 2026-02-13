#!/usr/bin/env python3

import re
import sys
import yaml
import subprocess
from pathlib import Path
from collections import defaultdict

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

# xschem units → microns
XSCHEM_TO_UM = 0.01

TOP_LEVEL_PORTS = {
    "ipin.sym",
    "opin.sym",
    "iopin.sym",
}

NET_LABEL_SYMBOLS = {
    "lab_pin.sym",
    "vdd.sym",
    "gnd.sym",
    "vss.sym",
}

IGNORED_SYMBOLS = {
    "title.sym",
}

# -------------------------------------------------------------------
# Regex patterns
# -------------------------------------------------------------------

# C {symbol.sym} x y rot mirror { properties }
COMPONENT_RE = re.compile(
    r"C\s+\{([^}]+)\}\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+\{([^}]*)\}",
    re.DOTALL,
)

PROPERTY_RE = re.compile(r"(\w+)\s*=\s*([^\s]+)")

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def parse_value(value: str):
    """Convert SPICE-style units to microns when numeric."""
    units = {"u": 1.0, "n": 1e-3, "p": 1e-6, "m": 1e6}
    last = value[-1]
    if last in units:
        try:
            return float(value[:-1]) * units[last]
        except ValueError:
            return value
    try:
        v = float(value)
        if abs(v) < 1e-2:
            return v * 1e6
        return v
    except ValueError:
        return value

def clean_number(value, ndigits=4):
    if isinstance(value, (int, float)):
        return round(value, ndigits)
    return value

def extract_component_name(symbol: str) -> str:
    return symbol.split("/")[-1].replace(".sym", "")

# -------------------------------------------------------------------
# Parse Xschem schematic
# -------------------------------------------------------------------

def parse_xschem_sch(filepath: Path):
    text = filepath.read_text()
    instances = {}
    placements = {}
    top_ports = {}

    for match in COMPONENT_RE.finditer(text):
        symbol, x, y, rot, mirror, props = match.groups()
        properties = dict(PROPERTY_RE.findall(props))

        name = properties.get("name")
        lab = properties.get("lab")
        sym = symbol.split("/")[-1]

        # Top-level ports
        if sym in TOP_LEVEL_PORTS and lab:
            top_ports[lab] = {
                "x": round(float(x) * XSCHEM_TO_UM, 4),
                "y": round(-float(y) * XSCHEM_TO_UM, 4),
            }
            continue

        # Ignore decorations
        if sym in NET_LABEL_SYMBOLS or sym in IGNORED_SYMBOLS:
            continue

        if not name:
            continue

        component = extract_component_name(symbol)
        settings = {
            k: clean_number(parse_value(v))
            for k, v in properties.items() if k != "name"
        }

        instances[name] = {"component": component}
        if settings:
            instances[name]["settings"] = settings

        placements[name] = {
            "x": round(float(x) * XSCHEM_TO_UM, 4),
            "y": round(-float(y) * XSCHEM_TO_UM, 4),
            "rotation": int(rot),
            "mirror": int(mirror),
        }

    return instances, placements, top_ports

# -------------------------------------------------------------------
# Parse SPICE netlist to map nets to instance pins
# -------------------------------------------------------------------

def parse_spice_netlist(filepath: Path):
    net_to_pins = defaultdict(list)
    spice_instances = {}

    for line in filepath.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("*") or not line[0].upper() == "X":
            continue
        tokens = line.split()
        name = tokens[0][1:]  # strip leading X
        nodes_raw = tokens[1:-1]  # everything between instance name and model
        model = tokens[-1]

        # Filter only tokens that are nets (ignore w=, l=, etc.)
        nets = [n for n in nodes_raw if "=" not in n]

        spice_instances[name] = {"nodes": nets, "model": model}

        # Map net → instance,pin (p1, p2, ...)
        for idx, net in enumerate(nets):
            pin_name = f"p{idx+1}"
            net_to_pins[net].append(f"{name},{pin_name}")

    return spice_instances, net_to_pins



# -------------------------------------------------------------------
# Map top-level ports to instance pins
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Map top-level ports to instance pins and external connections
# -------------------------------------------------------------------
# map_ports_to_instances()
def map_ports_to_instances(top_ports, net_to_pins):
    ports = {}
    connections = {}
    for net, pins in net_to_pins.items():
        if len(pins) > 1:
            # connect first pin to others
            first = pins[0]
            for other in pins[1:]:
                connections[first] = other

    for port_label, coords in top_ports.items():
        if port_label in net_to_pins:
            ports[port_label] = net_to_pins[port_label][0]  # pick one instance pin

    return ports, connections

# -------------------------------------------------------------------
# Generate routes from net_to_pins
# -------------------------------------------------------------------

def generate_routes(net_to_pins):
    routes = {}
    for net, pins in net_to_pins.items():
        if len(pins) > 1:
            # create a route name from net
            route_name = f"route_{net}"
            first_pin = pins[0]
            routes[route_name] = {
                "links": {
                    first_pin: pins[1]  # connect first pin to second pin; extendable if more
                },
                # NOTE: The `settings` section must be filled manually by the user.
                "settings": {
                    "cross_section": "strip",  # placeholder
                    "width": 1.0,              # placeholder
                    # add other waveguide or route parameters manually
                },
            }
    return routes

# -------------------------------------------------------------------
# Writer
# -------------------------------------------------------------------

def write_yaml(data, outfile: Path):
    with open(outfile, "w") as f:
        if "routes_comment" in data:
            f.write(f"# {data['routes_comment']}\n")
            del data["routes_comment"]
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise SystemExit(
            "Usage: generate_yaml.py <schematic.sch> [<netlist.spice>]"
        )

    sch_file = Path(sys.argv[1]).resolve()
    if not sch_file.exists():
        raise FileNotFoundError(f"Schematic not found: {sch_file}")

    spice_file = None
    if len(sys.argv) == 3:
        spice_file = Path(sys.argv[2]).resolve()
        if not spice_file.exists():
            raise FileNotFoundError(f"SPICE netlist not found: {spice_file}")

    # Parse schematic
    instances, placements, top_ports = parse_xschem_sch(sch_file)

    data = {
        "name": sch_file.stem,
        "instances": instances,
        "placements": placements,
    }

    if spice_file:
        spice_instances, net_to_pins = parse_spice_netlist(spice_file)
        ports, connections = map_ports_to_instances(top_ports, net_to_pins)
        if ports:
            data["ports"] = ports
        if connections:
            data["connections"] = connections

        # Automatically generate routes from nets
        routes = generate_routes(net_to_pins)
        if routes:
            data["routes"] = routes
            data["routes_comment"] = (
                "Routes are generated from nets. "
                "Please manually adjust `settings` for actual layout geometry."
            )

    out_file = sch_file.with_suffix(".pic.yml")
    write_yaml(data, out_file)
    print(f"Wrote {out_file}")




