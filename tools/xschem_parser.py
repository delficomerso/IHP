#!/usr/bin/env python3
"""
XSchem Schematic File Parser

A pure Python parser for xschem .sch files that extracts components,
wires, ports, and connections without requiring the xschem C library.

Author: Python wrapper implementation
License: GPL-2.0-or-later (matching xschem license)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
from collections import defaultdict


@dataclass
class Instance:
    """Represents a component instance in the schematic"""
    symbol: str
    x: float
    y: float
    rotation: int
    flip: int
    attributes: Dict[str, str]
    index: int = 0
    
    @property
    def name(self) -> Optional[str]:
        """Get the instance name from attributes"""
        return self.attributes.get('name')
    
    @property
    def label(self) -> Optional[str]:
        """Get the net label from attributes"""
        return self.attributes.get('lab')
    
    @property
    def is_port(self) -> bool:
        """Check if this instance is a port (ipin, opin, iopin)"""
        symbol_name = self.symbol.lower()
        return any(p in symbol_name for p in ['ipin.sym', 'opin.sym', 'iopin.sym'])
    
    @property
    def is_input_port(self) -> bool:
        """Check if this is an input port"""
        return 'ipin.sym' in self.symbol.lower()
    
    @property
    def is_output_port(self) -> bool:
        """Check if this is an output port"""
        return 'opin.sym' in self.symbol.lower()
    
    @property
    def is_inout_port(self) -> bool:
        """Check if this is an inout port"""
        return 'iopin.sym' in self.symbol.lower()
    
    @property
    def is_label(self) -> bool:
        """Check if this instance is a net label"""
        symbol_name = self.symbol.lower()
        return 'lab_pin.sym' in symbol_name or 'lab_wire.sym' in symbol_name
    
    def __repr__(self) -> str:
        port_type = ""
        if self.is_input_port:
            port_type = " [INPUT]"
        elif self.is_output_port:
            port_type = " [OUTPUT]"
        elif self.is_inout_port:
            port_type = " [INOUT]"
        return f"Instance({self.name or self.symbol} at ({self.x}, {self.y}){port_type})"


@dataclass
class Wire:
    """Represents a wire/net connection in the schematic"""
    x1: float
    y1: float
    x2: float
    y2: float
    attributes: Dict[str, str]
    index: int = 0
    net_name: Optional[str] = None
    
    @property
    def label(self) -> Optional[str]:
        """Get the net label from attributes"""
        return self.attributes.get('lab')
    
    @property
    def start_point(self) -> Tuple[float, float]:
        """Get the start point as a tuple"""
        return (self.x1, self.y1)
    
    @property
    def end_point(self) -> Tuple[float, float]:
        """Get the end point as a tuple"""
        return (self.x2, self.y2)
    
    @property
    def points(self) -> List[Tuple[float, float]]:
        """Get both endpoints as a list"""
        return [self.start_point, self.end_point]
    
    def __repr__(self) -> str:
        net_str = f" net={self.net_name}" if self.net_name else ""
        return f"Wire(({self.x1}, {self.y1}) -> ({self.x2}, {self.y2}){net_str})"


@dataclass
class SchematicInfo:
    """Metadata about the schematic"""
    version: str = ""
    file_version: str = ""
    vhdl_code: str = ""  # G section
    verilog_code: str = ""  # V section
    spice_code: str = ""  # S section
    embedded_symbols: str = ""  # E section
    extra_code: str = ""  # K section
    format: str = ""  # F section


class XschemSchematicParser:
    """Parser for xschem .sch files"""
    
    def __init__(self):
        self.instances: List[Instance] = []
        self.wires: List[Wire] = []
        self.info = SchematicInfo()
        self.raw_lines: List[str] = []
        self.filename: Optional[str] = None
        
    def parse_file(self, filename: str) -> None:
        """
        Parse an xschem .sch file
        
        Args:
            filename: Path to the .sch file
        """
        self.filename = filename
        self.instances.clear()
        self.wires.clear()
        self.raw_lines.clear()
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            self.raw_lines = content.split('\n')
        
        self._parse_content(content)
    
    def _parse_content(self, content: str) -> None:
        """Parse the content of a .sch file"""
        i = 0
        lines = content.split('\n')
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Version line
            if line.startswith('v {'):
                version_block, i = self._read_block(lines, i)
                self._parse_version(version_block)
            
            # VHDL code block (G)
            elif line.startswith('G {'):
                block, i = self._read_block(lines, i)
                self.info.vhdl_code = block
            
            # Verilog code block (V)
            elif line.startswith('V {'):
                block, i = self._read_block(lines, i)
                self.info.verilog_code = block
            
            # SPICE code block (S)
            elif line.startswith('S {'):
                block, i = self._read_block(lines, i)
                self.info.spice_code = block
            
            # Embedded symbols (E)
            elif line.startswith('E {'):
                block, i = self._read_block(lines, i)
                self.info.embedded_symbols = block
            
            # Extra code (K)
            elif line.startswith('K {'):
                block, i = self._read_block(lines, i)
                self.info.extra_code = block
            
            # Format (F)
            elif line.startswith('F {'):
                block, i = self._read_block(lines, i)
                self.info.format = block
            
            # Component instance
            elif line.startswith('C {'):
                self._parse_component(line)
                i += 1
            
            # Wire/Net
            elif line.startswith('N '):
                self._parse_wire(line)
                i += 1
            
            # Text
            elif line.startswith('T {'):
                # Text objects - skip for now
                i += 1
            
            # Line/Arc/Box/Polygon/etc - graphical elements
            elif line[0] in ['L', 'A', 'B', 'P']:
                i += 1
            
            else:
                i += 1
    
    def _read_block(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """
        Read a multi-line block delimited by {}
        
        Returns:
            (block_content, next_line_index)
        """
        first_line = lines[start_idx]
        
        # Check if it's a single-line block
        if first_line.count('{') == first_line.count('}'):
            # Extract content between { and }
            match = re.search(r'\{(.*)\}', first_line, re.DOTALL)
            if match:
                return match.group(1), start_idx + 1
            return "", start_idx + 1
        
        # Multi-line block
        block_lines = []
        brace_count = 0
        i = start_idx
        started = False
        
        while i < len(lines):
            line = lines[i]
            
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1
            
            if started:
                block_lines.append(line)
            
            i += 1
            
            if brace_count == 0 and started:
                break
        
        # Join and extract content between first { and last }
        full_text = '\n'.join(block_lines)
        # Remove the outer braces
        if full_text.startswith('{'):
            full_text = full_text[1:]
        if full_text.endswith('}'):
            full_text = full_text[:-1]
        
        return full_text.strip(), i
    
    def _parse_version(self, version_str: str) -> None:
        """Parse version information"""
        # Extract version info
        match = re.search(r'xschem version=([\d.RC]+)', version_str)
        if match:
            self.info.version = match.group(1)
        
        match = re.search(r'file_version=([\d.]+)', version_str)
        if match:
            self.info.file_version = match.group(1)
    
    def _parse_component(self, line: str) -> None:
        """
        Parse component instance line
        Format: C {symbol.sym} x y rotation flip {attributes}
        """
        # Pattern: C {symbol} x y rot flip {attrs}
        pattern = r'C\s+\{([^}]+)\}\s+([\d.e+-]+)\s+([\d.e+-]+)\s+(\d+)\s+(\d+)\s+\{([^}]*)\}'
        match = re.match(pattern, line)
        
        if match:
            symbol, x, y, rot, flip, attrs_str = match.groups()
            attrs = self._parse_attributes(attrs_str)
            
            inst = Instance(
                symbol=symbol.strip(),
                x=float(x),
                y=float(y),
                rotation=int(rot),
                flip=int(flip),
                attributes=attrs,
                index=len(self.instances)
            )
            self.instances.append(inst)
    
    def _parse_wire(self, line: str) -> None:
        """
        Parse wire line
        Format: N x1 y1 x2 y2 {attributes}
        """
        # Pattern: N x1 y1 x2 y2 {attrs}
        pattern = r'N\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+\{([^}]*)\}'
        match = re.match(pattern, line)
        
        if match:
            x1, y1, x2, y2, attrs_str = match.groups()
            attrs = self._parse_attributes(attrs_str)
            
            wire = Wire(
                x1=float(x1),
                y1=float(y1),
                x2=float(x2),
                y2=float(y2),
                attributes=attrs,
                index=len(self.wires),
                net_name=attrs.get('lab')
            )
            self.wires.append(wire)
    
    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:
        """
        Parse attribute string
        Format: name=value lab=netname key="multi word value"
        """
        attrs = {}
        
        # Handle quoted values and unquoted values
        # Pattern matches: key=value or key="quoted value" or key='quoted value'
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]+))'
        
        for match in re.finditer(pattern, attrs_str):
            key = match.group(1)
            # One of the three capture groups will have the value
            value = match.group(2) or match.group(3) or match.group(4)
            attrs[key] = value
        
        return attrs
    
    # === Query Methods ===
    
    def get_ports(self) -> List[Instance]:
        """Get all port instances (ipin, opin, iopin)"""
        return [inst for inst in self.instances if inst.is_port]
    
    def get_input_ports(self) -> List[Instance]:
        """Get all input ports"""
        return [inst for inst in self.instances if inst.is_input_port]
    
    def get_output_ports(self) -> List[Instance]:
        """Get all output ports"""
        return [inst for inst in self.instances if inst.is_output_port]
    
    def get_inout_ports(self) -> List[Instance]:
        """Get all inout ports"""
        return [inst for inst in self.instances if inst.is_inout_port]
    
    def get_labels(self) -> List[Instance]:
        """Get all net label instances"""
        return [inst for inst in self.instances if inst.is_label]
    
    def get_instances_by_symbol(self, symbol_pattern: str) -> List[Instance]:
        """
        Get instances matching a symbol pattern
        
        Args:
            symbol_pattern: Pattern to match (supports wildcards)
        """
        pattern = re.compile(symbol_pattern.replace('*', '.*'))
        return [inst for inst in self.instances if pattern.search(inst.symbol)]
    
    def get_instance_by_name(self, name: str) -> Optional[Instance]:
        """Get an instance by its name attribute"""
        for inst in self.instances:
            if inst.name == name:
                return inst
        return None
    
    # === Connectivity Analysis ===
    
    def get_net_labels(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Get all labeled nets with their coordinates
        
        Returns:
            Dictionary mapping net_name -> [(x, y), ...]
        """
        net_labels = defaultdict(list)
        
        # From wires with labels
        for wire in self.wires:
            if wire.label:
                net_labels[wire.label].extend(wire.points)
        
        # From label instances
        for inst in self.instances:
            if inst.is_label and inst.label:
                net_labels[inst.label].append((inst.x, inst.y))
        
        # From ports
        for inst in self.instances:
            if inst.is_port and inst.label:
                net_labels[inst.label].append((inst.x, inst.y))
        
        return dict(net_labels)
    
    def build_connectivity_graph(self, tolerance: float = 1e-6) -> Dict[Tuple[float, float], Set[Tuple[float, float]]]:
        """
        Build a connectivity graph from wire segments
        
        Args:
            tolerance: Distance tolerance for considering points connected
        
        Returns:
            Dictionary mapping each point to all directly connected points
        """
        graph = defaultdict(set)
        
        for wire in self.wires:
            p1 = wire.start_point
            p2 = wire.end_point
            graph[p1].add(p2)
            graph[p2].add(p1)
        
        return dict(graph)
    
    def trace_net(self, start_point: Tuple[float, float], tolerance: float = 1e-6) -> Set[Tuple[float, float]]:
        """
        Trace all connected points from a starting point
        
        Args:
            start_point: Starting (x, y) coordinate
            tolerance: Distance tolerance for point matching
        
        Returns:
            Set of all connected points
        """
        graph = self.build_connectivity_graph(tolerance)
        
        visited = set()
        to_visit = {start_point}
        
        while to_visit:
            point = to_visit.pop()
            if point in visited:
                continue
            
            visited.add(point)
            
            # Find all directly connected points
            if point in graph:
                for neighbor in graph[point]:
                    if neighbor not in visited:
                        to_visit.add(neighbor)
        
        return visited
    
    def get_net_at_point(self, x: float, y: float, tolerance: float = 1e-6) -> Optional[str]:
        """
        Find the net name at a specific point
        
        Args:
            x, y: Coordinates to check
            tolerance: Distance tolerance
        
        Returns:
            Net name if found, None otherwise
        """
        point = (x, y)
        
        # Check if point is on a labeled wire
        for wire in self.wires:
            if wire.label:
                # Check if point matches either endpoint
                if (abs(wire.x1 - x) < tolerance and abs(wire.y1 - y) < tolerance) or \
                   (abs(wire.x2 - x) < tolerance and abs(wire.y2 - y) < tolerance):
                    return wire.label
        
        # Check if point is at a label instance
        for inst in self.instances:
            if inst.is_label and inst.label:
                if abs(inst.x - x) < tolerance and abs(inst.y - y) < tolerance:
                    return inst.label
        
        # Check if point is at a port
        for inst in self.instances:
            if inst.is_port and inst.label:
                if abs(inst.x - x) < tolerance and abs(inst.y - y) < tolerance:
                    return inst.label
        
        # Trace connectivity to find labeled net
        connected_points = self.trace_net(point, tolerance)
        
        for pt in connected_points:
            net_name = self.get_net_at_point(pt[0], pt[1], tolerance=0)
            if net_name:
                return net_name
        
        return None
    
    def get_instance_connections(self, tolerance: float = 1e-6) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Get net connections for all instances
        
        Returns:
            Dictionary mapping instance_name -> {pin_name: net_name}
        """
        connections = {}
        
        for inst in self.instances:
            if not inst.name:
                continue
            
            # For now, we assume the instance position is the pin location
            # In reality, pins have offsets that would need to be calculated
            # based on the symbol definition
            net = self.get_net_at_point(inst.x, inst.y, tolerance)
            
            connections[inst.name] = {'default': net}
        
        return connections
    
    # === Summary Methods ===
    
    def print_summary(self) -> None:
        """Print a summary of the schematic"""
        print(f"=== Schematic Summary: {self.filename or 'Unknown'} ===")
        print(f"Version: {self.info.version} (file format {self.info.file_version})")
        print(f"\nInstances: {len(self.instances)}")
        print(f"  - Input ports: {len(self.get_input_ports())}")
        print(f"  - Output ports: {len(self.get_output_ports())}")
        print(f"  - Inout ports: {len(self.get_inout_ports())}")
        print(f"  - Other components: {len(self.instances) - len(self.get_ports())}")
        print(f"\nWires: {len(self.wires)}")
        
        net_labels = self.get_net_labels()
        print(f"Named nets: {len(net_labels)}")
        
        if self.info.vhdl_code:
            print("\nContains VHDL code")
        if self.info.verilog_code:
            print("Contains Verilog code")
        if self.info.spice_code:
            print("Contains SPICE code")
    
    def print_ports(self) -> None:
        """Print all ports"""
        print("\n=== Ports ===")
        
        for port in self.get_input_ports():
            print(f"  INPUT:  {port.label or port.name} at ({port.x}, {port.y})")
        
        for port in self.get_output_ports():
            print(f"  OUTPUT: {port.label or port.name} at ({port.x}, {port.y})")
        
        for port in self.get_inout_ports():
            print(f"  INOUT:  {port.label or port.name} at ({port.x}, {port.y})")
    
    def print_nets(self) -> None:
        """Print all named nets"""
        print("\n=== Named Nets ===")
        
        net_labels = self.get_net_labels()
        for net_name, points in sorted(net_labels.items()):
            print(f"  {net_name}: {len(points)} connection points")
    
    def to_dict(self) -> Dict:
        """
        Convert the parsed schematic to a dictionary
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            'filename': self.filename,
            'version': self.info.version,
            'file_version': self.info.file_version,
            'instances': [
                {
                    'index': inst.index,
                    'symbol': inst.symbol,
                    'name': inst.name,
                    'x': inst.x,
                    'y': inst.y,
                    'rotation': inst.rotation,
                    'flip': inst.flip,
                    'attributes': inst.attributes,
                    'is_port': inst.is_port,
                    'port_type': 'input' if inst.is_input_port else 'output' if inst.is_output_port else 'inout' if inst.is_inout_port else None
                }
                for inst in self.instances
            ],
            'wires': [
                {
                    'index': wire.index,
                    'x1': wire.x1,
                    'y1': wire.y1,
                    'x2': wire.x2,
                    'y2': wire.y2,
                    'net_name': wire.net_name,
                    'attributes': wire.attributes
                }
                for wire in self.wires
            ],
            'nets': self.get_net_labels()
        }


def main():
    """Example usage"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python xschem_parser.py <schematic.sch> [--json]")
        print("\nExample:")
        print("  python xschem_parser.py example.sch")
        print("  python xschem_parser.py example.sch --json > output.json")
        sys.exit(1)
    
    filename = sys.argv[1]
    output_json = '--json' in sys.argv
    
    if not Path(filename).exists():
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    # Parse the schematic
    parser = XschemSchematicParser()
    
    try:
        parser.parse_file(filename)
    except Exception as e:
        print(f"Error parsing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if output_json:
        # Output as JSON
        print(json.dumps(parser.to_dict(), indent=2))
    else:
        # Print human-readable summary
        parser.print_summary()
        parser.print_ports()
        parser.print_nets()
        
        # Show some example instances
        if len(parser.instances) > 0:
            print(f"\n=== Sample Instances (showing first 5) ===")
            for inst in parser.instances[:5]:
                print(f"  {inst}")
        
        # Show some example wires
        if len(parser.wires) > 0:
            print(f"\n=== Sample Wires (showing first 5) ===")
            for wire in parser.wires[:5]:
                print(f"  {wire}")


if __name__ == '__main__':
    main()
