#!/usr/bin/env python3
"""
SPICE to pic.yml Converter - Functional Implementation

This module converts SPICE netlists to gdsfactory pic.yml format using
a functional approach with dictionaries instead of classes.

Features:
- Component type mapping (SPICE model -> PDK function)
- Parameter translation (SPICE param -> PDK param with type conversion)
- Automatic unit conversion (e.g., "60.0u" -> 60.0)
- Layout generation with organized placements
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import gdsfactory as gf
import yaml

# ============================================================================
# GDS COORDINATE EXTRACTION
# ============================================================================


def extract_rppd_from_gds(
    gds_file: Path,
    poly_layer: tuple[int, int] = (128, 0),
) -> list[dict[str, Any]]:
    """Extract RPPD resistor placements and dimensions from GDS file.

    Reads the PolyResdrawing layer geometry to get the actual dx/dy dimensions,
    which can then be matched against SPICE w/l parameters.

    Args:
        gds_file: Path to the GDS file.
        poly_layer: The (layer, datatype) number of the PolyResdrawing layer.
                    Defaults to (128, 0) for IHP SG13G2.

    Returns:
        List of dicts, each containing: name, x, y, rotation, mirror, dx, dy.
    """

    print(f"Extracting rppd placements from GDS: {gds_file}")

    c = gf.import_gds(str(gds_file))
    layout = c.kcl.layout
    top_cell = layout.cell(c.cell_index())

    # Find the PolyResdrawing layer - first try by name, then fall back to layer number
    poly_layer_index = None

    # Try by name first
    for layer_index in layout.layer_indexes():
        layer_info = layout.get_info(layer_index)
        if "PolyResdrawing" in str(layer_info):
            poly_layer_index = layer_index
            print(f"  Found PolyRes layer by name: {layer_info} (index {layer_index})")
            break

    # Fall back to layer number (128/0 for IHP SG13G2)
    if poly_layer_index is None:
        layer_num, datatype = poly_layer
        poly_layer_index = layout.find_layer(layer_num, datatype)
        if poly_layer_index is not None:
            print(
                f"  Found PolyRes layer by number: {layer_num}/{datatype} (index {poly_layer_index})"
            )
        else:
            raise ValueError(
                f"PolyResdrawing layer not found by name or by number {layer_num}/{datatype}. "
                f"Available layers: {[str(layout.get_info(i)) for i in layout.layer_indexes()[:10]]}"
            )

    rppd_data = []

    for inst in top_cell.each_inst():
        ref_cell = layout.cell(inst.cell_index)

        if "rppd" not in ref_cell.name.lower():
            continue

        trans = inst.dcplx_trans
        x = trans.disp.x
        y = trans.disp.y
        rotation = trans.angle
        mirror = trans.is_mirror()

        # Extract dx/dy from the PolyRes rectangle - search recursively
        dx, dy = None, None
        shape_iter = ref_cell.begin_shapes_rec(poly_layer_index)
        while not shape_iter.at_end():
            shape = shape_iter.shape()
            if shape.is_box():
                box = shape.box
                dx = box.width() * layout.dbu
                dy = box.height() * layout.dbu
            elif shape.is_polygon():
                bbox = shape.polygon.bbox()
                dx = bbox.width() * layout.dbu
                dy = bbox.height() * layout.dbu
            if dx is not None:
                break
            shape_iter.next()

        if dx is None:
            raise ValueError(f"No PolyRes rectangle found in {ref_cell.name}")

        rppd_data.append(
            {
                "name": ref_cell.name,
                "x": x,
                "y": y,
                "rotation": rotation,
                "mirror": mirror,
                "dx": dx,
                "dy": dy,
            }
        )

    print(f"  Extracted {len(rppd_data)} rppd instances")
    return rppd_data


def extract_inductors_from_gds(
    gds_file: Path,
    ind_layer: tuple[int, int] = (1, 23),
) -> list[dict[str, Any]]:
    """Extract inductor placements and dimensions from GDS file.

    Reads the Activnofill (or INDdrawing) layer to find octagonal inductor shapes
    and extracts their bounding box width as the diameter.

    Args:
        gds_file: Path to the GDS file.
        ind_layer: The (layer, datatype) of the Activnofill layer.
                   Defaults to (1, 23) for IHP SG13G2.

    Returns:
        List of dicts, each containing: name, x, y, rotation, mirror, diameter.
    """

    print(f"Extracting inductor placements from GDS: {gds_file}")

    c = gf.import_gds(str(gds_file))
    layout = c.kcl.layout
    top_cell = layout.cell(c.cell_index())

    # Find the inductor layer - try by name first
    ind_layer_index = None

    for layer_index in layout.layer_indexes():
        layer_info = layout.get_info(layer_index)
        if "Activnofill" in str(layer_info) or "INDdrawing" in str(layer_info):
            ind_layer_index = layer_index
            print(f"  Found inductor layer by name: {layer_info} (index {layer_index})")
            break

    # Fall back to layer number
    if ind_layer_index is None:
        layer_num, datatype = ind_layer
        ind_layer_index = layout.find_layer(layer_num, datatype)
        if ind_layer_index is not None:
            print(
                f"  Found inductor layer by number: {layer_num}/{datatype} (index {ind_layer_index})"
            )
        else:
            raise ValueError(
                f"Inductor layer not found by name or by number {layer_num}/{datatype}. "
                f"Available layers: {[str(layout.get_info(i)) for i in layout.layer_indexes()[:10]]}"
            )

    inductor_data = []

    for inst in top_cell.each_inst():
        ref_cell = layout.cell(inst.cell_index)

        if "inductor" not in ref_cell.name.lower():
            continue

        trans = inst.dcplx_trans
        x = trans.disp.x
        y = trans.disp.y
        rotation = trans.angle
        mirror = trans.is_mirror()

        # Find octagonal polygon and extract diameter from bbox - search recursively
        diameter = None
        shape_iter = ref_cell.begin_shapes_rec(ind_layer_index)
        while not shape_iter.at_end():
            shape = shape_iter.shape()

            if shape.is_polygon():
                poly = shape.polygon
                bbox = poly.bbox()

                width = bbox.width() * layout.dbu
                height = bbox.height() * layout.dbu

                # Use the larger dimension as diameter
                diameter = max(width, height)
                break  # Only need one polygon

            shape_iter.next()

        if diameter is None:
            print(f"  Warning: No inductor polygon found in {ref_cell.name}, skipping")
            continue

        inductor_data.append(
            {
                "name": ref_cell.name,
                "x": x,
                "y": y,
                "rotation": rotation,
                "mirror": mirror,
                "diameter": diameter,
            }
        )

    print(f"  Extracted {len(inductor_data)} inductor instances")
    return inductor_data


def extract_nmos_from_gds(gds_file: Path) -> list[dict[str, Any]]:
    """Extract NMOS transistor placements and dimensions from GDS file.

    Uses recursive traversal to find all NMOS cells and extracts their bounding
    box dimensions as a proxy for device size (correlates with nf).

    Args:
        gds_file: Path to the GDS file.

    Returns:
        List of dicts, each containing: name, x, y, rotation, mirror, width, length.
    """
    try:
        import gdsfactory as gf
        import klayout.db as kdb
    except ImportError as err:
        raise ImportError(
            "gdsfactory and klayout not installed. Install with: pip install gdsfactory"
        ) from err

    print(f"Extracting NMOS placements from GDS: {gds_file}")

    c = gf.import_gds(str(gds_file))
    layout = c.kcl.layout
    top_cell = layout.cell(c.cell_index())
    dbu = layout.dbu

    def walk_instances(cell, parent_trans=None):
        """Recursively walk through cell hierarchy."""
        if parent_trans is None:
            parent_trans = kdb.DCplxTrans()

        for inst in cell.each_inst():
            ref_cell = layout.cell(inst.cell_index)
            total_trans = parent_trans * inst.dcplx_trans

            yield ref_cell, total_trans
            yield from walk_instances(ref_cell, total_trans)

    nmos_data = []

    for ref_cell, trans in walk_instances(top_cell):
        if "nmos" not in ref_cell.name.lower():
            continue

        bbox = ref_cell.bbox()
        width = (bbox.right - bbox.left) * dbu
        height = (bbox.top - bbox.bottom) * dbu

        nmos_data.append(
            {
                "name": ref_cell.name,
                "x": trans.disp.x,
                "y": trans.disp.y,
                "rotation": trans.angle,
                "mirror": trans.is_mirror(),
                "width": width,
                "length": height,
            }
        )

    print(f"  Extracted {len(nmos_data)} NMOS instances")
    return nmos_data


def extract_cmim_from_gds(
    gds_file: Path,
    mim_layer: tuple[int, int] = (36, 0),
) -> list[dict[str, Any]]:
    """Extract CMIM capacitor placements and dimensions from GDS file.

    Reads the MIM capacitor layer to extract width and length dimensions.

    Args:
        gds_file: Path to the GDS file.
        mim_layer: The (layer, datatype) of the MIM layer.
                   Defaults to (36, 0) for IHP SG13G2.

    Returns:
        List of dicts, each containing: name, x, y, rotation, mirror, width, length.
    """
    try:
        import gdsfactory as gf
    except ImportError as err:
        raise ImportError(
            "gdsfactory not installed. Install with: pip install gdsfactory"
        ) from err

    print(f"Extracting CMIM placements from GDS: {gds_file}")

    c = gf.import_gds(str(gds_file))
    layout = c.kcl.layout
    top_cell = layout.cell(c.cell_index())

    # Find the MIM layer - try by name first
    mim_layer_index = None

    for layer_index in layout.layer_indexes():
        layer_info = layout.get_info(layer_index)
        if "MIM" in str(layer_info) or "Metal5" in str(layer_info):
            mim_layer_index = layer_index
            print(f"  Found MIM layer by name: {layer_info} (index {layer_index})")
            break

    # Fall back to layer number
    if mim_layer_index is None:
        layer_num, datatype = mim_layer
        mim_layer_index = layout.find_layer(layer_num, datatype)
        if mim_layer_index is not None:
            print(
                f"  Found MIM layer by number: {layer_num}/{datatype} (index {mim_layer_index})"
            )
        else:
            raise ValueError(
                f"MIM layer not found by name or by number {layer_num}/{datatype}. "
                f"Available layers: {[str(layout.get_info(i)) for i in layout.layer_indexes()[:10]]}"
            )

    cmim_data = []

    for inst in top_cell.each_inst():
        ref_cell = layout.cell(inst.cell_index)

        if "cmim" not in ref_cell.name.lower():
            continue

        trans = inst.dcplx_trans
        x = trans.disp.x
        y = trans.disp.y
        rotation = trans.angle
        mirror = trans.is_mirror()

        # Extract width/length from MIM rectangle - search recursively
        width, length = None, None
        shape_iter = ref_cell.begin_shapes_rec(mim_layer_index)
        while not shape_iter.at_end():
            shape = shape_iter.shape()
            if shape.is_box():
                box = shape.box
                width = box.width() * layout.dbu
                length = box.height() * layout.dbu
            elif shape.is_polygon():
                bbox = shape.polygon.bbox()
                width = bbox.width() * layout.dbu
                length = bbox.height() * layout.dbu
            if width is not None:
                break
            shape_iter.next()

        if width is None:
            print(f"  Warning: No MIM rectangle found in {ref_cell.name}, skipping")
            continue

        cmim_data.append(
            {
                "name": ref_cell.name,
                "x": x,
                "y": y,
                "rotation": rotation,
                "mirror": mirror,
                "width": width,
                "length": length,
            }
        )

    print(f"  Extracted {len(cmim_data)} CMIM instances")
    return cmim_data


def match_rppd_to_gds(
    spice_instances: dict[str, Any],
    rppd_data: list[dict[str, Any]],
    tolerance: float = 0.01,
) -> dict[str, dict[str, Any]]:
    """Match SPICE rppd instances to GDS placements by comparing dx/dy parameters.

    The GDS dx/dy values (extracted from the PolyRes layer geometry) are compared
    directly against the SPICE w/l parameters (converted to µm). This is exact
    matching - no heuristics needed.

    Args:
        spice_instances: Dictionary of SPICE instances with their models and parameters.
        rppd_data: List of dicts from extract_rppd_from_gds(), each containing
                   x, y, rotation, mirror, dx, dy.
        tolerance: Maximum allowed difference in µm when comparing dx/dy to w/l (default: 0.01).

    Returns:
        Dictionary mapping SPICE instance names to placement info.
    """
    matched_placements = {}

    # Extract SPICE rppd instances with their w/l converted to µm
    spice_rppd = {}
    for inst_name, inst_data in spice_instances.items():
        if inst_data.get("model") != "rppd":
            continue
        params = inst_data.get("parameters", {})
        spice_rppd[inst_name] = {
            "dx": parse_dimension(params["w"]),  # w in SPICE → dx in µm
            "dy": parse_dimension(params["l"]),  # l in SPICE → dy in µm
        }

    print("\n=== SPICE rppd instances (w/l converted to µm) ===")
    for name, dims in sorted(spice_rppd.items()):
        print(f"  {name}: dx={dims['dx']:.4f}, dy={dims['dy']:.4f}")

    print("\n=== GDS rppd instances (dx/dy from PolyRes layer) ===")
    for entry in rppd_data:
        print(
            f"  {entry['name']}: dx={entry['dx']:.4f}, dy={entry['dy']:.4f} @ ({entry['x']:.2f}, {entry['y']:.2f})"
        )

    # Group GDS entries by (dx, dy) signature
    # Multiple GDS entries with the same dx/dy belong to the same SPICE parameter group
    gds_by_dims: dict[tuple, list] = {}
    for entry in rppd_data:
        key = (round(entry["dx"], 3), round(entry["dy"], 3))
        if key not in gds_by_dims:
            gds_by_dims[key] = []
        gds_by_dims[key].append(entry)

    # Group SPICE instances by (dx, dy) signature
    spice_by_dims: dict[tuple, list] = {}
    for inst_name, dims in spice_rppd.items():
        key = (round(dims["dx"], 3), round(dims["dy"], 3))
        if key not in spice_by_dims:
            spice_by_dims[key] = []
        spice_by_dims[key].append(inst_name)

    # Sort each group alphabetically for consistent ordering
    for key in spice_by_dims:
        spice_by_dims[key].sort()

    # Match: for each unique (dx, dy), pair up SPICE instances with GDS entries
    print("\n=== Matching ===")
    for dims_key, spice_names in sorted(spice_by_dims.items()):
        dx, dy = dims_key

        # Find GDS entries with matching dimensions (within tolerance)
        gds_matches = []
        for (gds_dx, gds_dy), gds_entries in gds_by_dims.items():
            if abs(gds_dx - dx) <= tolerance and abs(gds_dy - dy) <= tolerance:
                gds_matches.extend(gds_entries)

        print(
            f"\n  dx={dx}, dy={dy}: {len(spice_names)} SPICE → {len(gds_matches)} GDS"
        )

        if len(spice_names) != len(gds_matches):
            print(
                f"  ⚠ Count mismatch! SPICE has {len(spice_names)}, GDS has {len(gds_matches)}"
            )

        for spice_name, gds_entry in zip(spice_names, gds_matches):
            matched_placements[spice_name] = {
                "x": gds_entry["x"],
                "y": gds_entry["y"],
                "rotation": gds_entry["rotation"],
                "mirror": gds_entry["mirror"],
            }
            print(f"    {spice_name} → ({gds_entry['x']:.2f}, {gds_entry['y']:.2f})")

    unmatched = [n for n in spice_rppd if n not in matched_placements]
    if unmatched:
        print(f"\n  ⚠ Unmatched SPICE instances: {unmatched}")

    print(f"\n✓ Matched {len(matched_placements)} of {len(spice_rppd)} rppd instances")

    return matched_placements


def match_inductors_to_gds(
    spice_instances: dict[str, Any],
    inductor_data: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Match SPICE inductor instances to GDS placements by order.

    Since inductors in SPICE don't have dimensional parameters we can match,
    we simply match them by alphabetical order.

    Args:
        spice_instances: Dictionary of SPICE instances.
        inductor_data: List of dicts from extract_inductors_from_gds().

    Returns:
        Dictionary mapping SPICE instance names to placement info.
    """
    matched_placements = {}

    # Extract SPICE inductors
    spice_inductors = []
    for inst_name, inst_data in spice_instances.items():
        if "inductor" in inst_data.get("model", "").lower():
            spice_inductors.append(inst_name)

    spice_inductors.sort()  # Match by alphabetical order

    print("\n=== Matching Inductors ===")
    print(
        f"  {len(spice_inductors)} SPICE inductors → {len(inductor_data)} GDS inductors"
    )

    if len(spice_inductors) != len(inductor_data):
        print("  ⚠ Count mismatch!")

    for spice_name, gds_entry in zip(spice_inductors, inductor_data):
        matched_placements[spice_name] = {
            "x": gds_entry["x"],
            "y": gds_entry["y"],
            "rotation": gds_entry["rotation"],
            "mirror": gds_entry["mirror"],
            "diameter": gds_entry["diameter"],  # Include diameter for potential use
        }
        print(
            f"    {spice_name} → ({gds_entry['x']:.2f}, {gds_entry['y']:.2f}), diameter={gds_entry['diameter']:.2f}"
        )

    print(f"\n✓ Matched {len(matched_placements)} of {len(spice_inductors)} inductors")

    return matched_placements


def match_nmos_to_gds(
    spice_instances: dict[str, Any],
    nmos_data: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Match SPICE NMOS instances to GDS placements by nf (number of fingers).

    Higher nf → wider device in GDS. We sort both by width/nf and match in order.

    Args:
        spice_instances: Dictionary of SPICE instances.
        nmos_data: List of dicts from extract_nmos_from_gds().

    Returns:
        Dictionary mapping SPICE instance names to placement info.
    """
    matched_placements = {}

    # Extract SPICE NMOS with their nf values
    spice_nmos = []
    for inst_name, inst_data in spice_instances.items():
        model = inst_data.get("model", "")
        if "nmos" in model.lower():
            params = inst_data.get("parameters", {})
            nf = int(float(params.get("ng", params.get("nf", 1))))
            spice_nmos.append((inst_name, nf))

    # Sort SPICE by nf (ascending)
    spice_nmos.sort(key=lambda x: x[1])

    # Sort GDS by width (ascending) - width correlates with nf
    nmos_data_sorted = sorted(nmos_data, key=lambda x: x["width"])

    print("\n=== Matching NMOS ===")
    print(f"  {len(spice_nmos)} SPICE NMOS → {len(nmos_data_sorted)} GDS NMOS")

    if len(spice_nmos) != len(nmos_data_sorted):
        print("  ⚠ Count mismatch!")

    for (spice_name, nf), gds_entry in zip(spice_nmos, nmos_data_sorted):
        matched_placements[spice_name] = {
            "x": gds_entry["x"],
            "y": gds_entry["y"],
            "rotation": gds_entry["rotation"],
            "mirror": gds_entry["mirror"],
        }
        print(
            f"    {spice_name} (nf={nf}) → ({gds_entry['x']:.2f}, {gds_entry['y']:.2f}), width={gds_entry['width']:.2f}"
        )

    print(f"\n✓ Matched {len(matched_placements)} of {len(spice_nmos)} NMOS")

    return matched_placements


def match_cmim_to_gds(
    spice_instances: dict[str, Any],
    cmim_data: list[dict[str, Any]],
    tolerance: float = 0.01,
) -> dict[str, dict[str, Any]]:
    """Match SPICE CMIM capacitor instances to GDS placements by width/length.

    Similar to rppd matching - compares SPICE w/l against GDS width/length.

    Args:
        spice_instances: Dictionary of SPICE instances.
        cmim_data: List of dicts from extract_cmim_from_gds().
        tolerance: Maximum allowed difference in µm (default: 0.01).

    Returns:
        Dictionary mapping SPICE instance names to placement info.
    """
    matched_placements = {}

    # Extract SPICE cmim instances with their w/l converted to µm
    spice_cmim = {}
    for inst_name, inst_data in spice_instances.items():
        if inst_data.get("model") != "cap_cmim":
            continue
        params = inst_data.get("parameters", {})
        spice_cmim[inst_name] = {
            "width": parse_dimension(params["w"]),
            "length": parse_dimension(params["l"]),
        }

    print("\n=== SPICE cmim instances (w/l converted to µm) ===")
    for name, dims in sorted(spice_cmim.items()):
        print(f"  {name}: width={dims['width']:.4f}, length={dims['length']:.4f}")

    print("\n=== GDS cmim instances (width/length from MIM layer) ===")
    for entry in cmim_data:
        print(
            f"  {entry['name']}: width={entry['width']:.4f}, length={entry['length']:.4f} @ ({entry['x']:.2f}, {entry['y']:.2f})"
        )

    # Group GDS by dimensions
    gds_by_dims: dict[tuple, list] = {}
    for entry in cmim_data:
        key = (round(entry["width"], 3), round(entry["length"], 3))
        if key not in gds_by_dims:
            gds_by_dims[key] = []
        gds_by_dims[key].append(entry)

    # Group SPICE by dimensions
    spice_by_dims: dict[tuple, list] = {}
    for inst_name, dims in spice_cmim.items():
        key = (round(dims["width"], 3), round(dims["length"], 3))
        if key not in spice_by_dims:
            spice_by_dims[key] = []
        spice_by_dims[key].append(inst_name)

    # Sort each group alphabetically
    for key in spice_by_dims:
        spice_by_dims[key].sort()

    # Match
    print("\n=== Matching ===")
    for dims_key, spice_names in sorted(spice_by_dims.items()):
        width, length = dims_key

        # Find GDS entries with matching dimensions
        gds_matches = []
        for (gds_w, gds_l), gds_entries in gds_by_dims.items():
            if abs(gds_w - width) <= tolerance and abs(gds_l - length) <= tolerance:
                gds_matches.extend(gds_entries)

        print(
            f"\n  width={width}, length={length}: {len(spice_names)} SPICE → {len(gds_matches)} GDS"
        )

        if len(spice_names) != len(gds_matches):
            print(
                f"  ⚠ Count mismatch! SPICE has {len(spice_names)}, GDS has {len(gds_matches)}"
            )

        for spice_name, gds_entry in zip(spice_names, gds_matches):
            matched_placements[spice_name] = {
                "x": gds_entry["x"],
                "y": gds_entry["y"],
                "rotation": gds_entry["rotation"],
                "mirror": gds_entry["mirror"],
            }
            print(f"    {spice_name} → ({gds_entry['x']:.2f}, {gds_entry['y']:.2f})")

    unmatched = [n for n in spice_cmim if n not in matched_placements]
    if unmatched:
        print(f"\n  ⚠ Unmatched SPICE instances: {unmatched}")

    print(f"\n✓ Matched {len(matched_placements)} of {len(spice_cmim)} cmim instances")

    return matched_placements


def match_spice_to_gds_placements(
    spice_instances: dict[str, Any],
    rppd_data: list[dict[str, Any]] | None = None,
    inductor_data: list[dict[str, Any]] | None = None,
    nmos_data: list[dict[str, Any]] | None = None,
    cmim_data: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Unified function to match SPICE instances to GDS placements.

    Args:
        spice_instances: Dictionary of SPICE instances.
        rppd_data: Optional list of rppd data from extract_rppd_from_gds().
        inductor_data: Optional list of inductor data from extract_inductors_from_gds().
        nmos_data: Optional list of NMOS data from extract_nmos_from_gds().
        cmim_data: Optional list of CMIM data from extract_cmim_from_gds().

    Returns:
        Dictionary mapping SPICE instance names to placement info.
    """
    all_matched = {}

    if rppd_data:
        rppd_matched = match_rppd_to_gds(spice_instances, rppd_data)
        all_matched.update(rppd_matched)

    if inductor_data:
        inductor_matched = match_inductors_to_gds(spice_instances, inductor_data)
        all_matched.update(inductor_matched)

    if nmos_data:
        nmos_matched = match_nmos_to_gds(spice_instances, nmos_data)
        all_matched.update(nmos_matched)

    if cmim_data:
        cmim_matched = match_cmim_to_gds(spice_instances, cmim_data)
        all_matched.update(cmim_matched)

    return all_matched


# ============================================================================
# CONVERSION FUNCTIONS
# ============================================================================

# SPICE letter suffixes and their SI multipliers
_SPICE_SUFFIX_MULTIPLIERS = {
    "f": 1e-15,  # femto
    "p": 1e-12,  # pico
    "n": 1e-9,  # nano
    "u": 1e-6,  # micro
    "m": 1e-3,  # milli
    "k": 1e3,  # kilo
    "M": 1e6,  # mega
    "G": 1e9,  # giga
}


def _parse_spice_number(value: str) -> float:
    """Parse a raw SPICE number, handling broken scientific notation and SI suffixes.

    SPICE uses letter suffixes as SI multipliers:
        2.006n -> 2.006e-9
        4.5e-6 -> 4.5e-6   (standard scientific notation, no suffix)
        60.0u  -> 60.0e-6   (suffix used instead of scientific notation)

    Args:
        value: The raw SPICE number as a string.
    Returns:
        The parsed number as a float, in SI units.
    """
    value = value.strip()

    # Handle scientific notation missing 'e': 4.50-6 -> 4.50e-6
    if re.search(r"[0-9]-[0-9]", value) and "e" not in value.lower():
        value = re.sub(r"([0-9])-", r"\1e-", value)
    if re.search(r"[0-9]\+[0-9]", value) and "e" not in value.lower():
        value = re.sub(r"([0-9])\+", r"\1e+", value)

    # Check for a trailing SI suffix (single letter, not part of 'e' notation)
    match = re.match(r"^([0-9.eE+-]+)([a-zA-Z])$", value)
    if match:
        number = float(match.group(1))
        suffix = match.group(2)
        multiplier = _SPICE_SUFFIX_MULTIPLIERS.get(suffix, 1.0)
        return number * multiplier

    return float(value)


def parse_dimension(value: str) -> float:
    """Parse a dimensional value (width, length, etc.) and convert meters to micrometers.

    SPICE uses meters for dimensions, gdsfactory uses micrometers by default, so we always multiply by 1e6.
    Rounds to 4 decimal places to avoid floating point noise (e.g. 59.9999 -> 60.0).

    Args:
        value: The raw SPICE dimension as a string (e.g., "2.006n").
    Returns:
        The parsed dimension as a float in micrometers (e.g., 2.006).
    """
    return round(_parse_spice_number(value) * 1e6, 4)


def parse_float(value: str) -> float:
    """Parse a non-space SI quantity (inductance, resistance, etc.).

    Keeps the value in SI units as-is (e.g., 2.006e-9 H stays 2.006e-9).

    Args:
        value: The raw SPICE number as a string (e.g., "2.006n").
    Returns:
        The parsed number as a float in SI units (e.g., 2.006e-9).
    """
    return _parse_spice_number(value)


def parse_int(value: str) -> int:
    """Parse integer.

    Args:
        value: The raw SPICE integer as a string (e.g., "4").

    Returns:
        The parsed integer as an int (e.g., 4).
    """
    return int(float(value))


def keep_string(value: str) -> str:
    """Keep as string."""
    return value.strip()


# ============================================================================
# PARAMETER MAPPING FUNCTIONS
# ============================================================================


def create_param_mapping(
    ihp_param_name: str,
    pdk_param_name: str,
    converter: Callable | None = None,
    default: Any = None,
) -> dict[str, Any]:
    """Create a parameter mapping dictionary.

    Args:
        ihp_param_name: The parameter name used in the SPICE netlist (e.g., "w").
        pdk_param_name: The corresponding parameter name used in the PDK (e.g., "width").
        converter: A function to convert the SPICE parameter value to the PDK format (e.g., parse_dimension). If None, the value will be kept as a string.
        default: An optional default value to use if the parameter is not specified in the SPICE netlist.

    Returns:
        A dictionary containing the mapping information for this parameter.
    """
    return {
        "ihp_param_name": ihp_param_name,
        "pdk_param_name": pdk_param_name,
        "converter": converter or keep_string,
        "default": default,
    }


def apply_param_mapping(mapping: dict[str, Any], value: str) -> Any:
    """Apply a parameter mapping to convert a value.

    Args:
        mapping: The parameter mapping dictionary created by create_param_mapping.
        value: The raw SPICE parameter value as a string.

    Returns:
        The converted parameter value, after applying the mapping's converter function.
    """
    converter = mapping["converter"]
    return converter(value)


def map_parameters(
    spice_params: dict[str, str], param_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Convert SPICE parameters to PDK parameters using mappings.

    Args:
        spice_params: A dictionary of parameters from the SPICE netlist (e.g., {"w": "2.006n", "l": "1.5u"}).
        param_mappings: A dictionary of parameter mappings created by create_param_mapping.

    Returns:
        A dictionary of converted parameters for the PDK (e.g., {"width": 2.006, "length": 1.5}).
    """
    pdk_params = {}

    for ihp_param_name, value in spice_params.items():
        if ihp_param_name in param_mappings:
            mapping = param_mappings[ihp_param_name]
            pdk_param_name = mapping["pdk_param_name"]
            pdk_params[pdk_param_name] = apply_param_mapping(mapping, value)

    # Add any missing defaults
    for _, mapping in param_mappings.items():
        pdk_param_name = mapping["pdk_param_name"]
        if pdk_param_name not in pdk_params and mapping["default"] is not None:
            pdk_params[pdk_param_name] = mapping["default"]

    return pdk_params


# ============================================================================
# COMPONENT MAPPING FUNCTIONS
# ============================================================================


def create_component_mapping(
    spice_model: str, pdk_component: str, param_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Create a component mapping dictionary.

    Args:
        spice_model: The model name used in the SPICE netlist (e.g., "sg13_lv_nmos").
        pdk_component: The corresponding component name used in the PDK (e.g., "nmos").
        param_mappings: A dictionary of parameter mappings for this component, created by create_param_mapping.

    Returns:
        A dictionary containing the mapping information for this component, including the SPICE model name, PDK component name, and parameter mappings.
    """
    return {
        "spice_model": spice_model,
        "pdk_component": pdk_component,
        "param_mappings": param_mappings,
    }


def get_default_ihp_mappings() -> dict[str, dict[str, Any]]:
    """Get default component mappings for IHP SG13G2 PDK."""

    mappings = {}

    # NMOS parameter mappings
    nmos_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        "ng": create_param_mapping("ng", "nf", parse_int),
        "model": create_param_mapping(
            "model", "model", keep_string, default="sg13_lv_nmos"
        ),
    }

    # PMOS parameter mappings (same as NMOS)
    pmos_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        "ng": create_param_mapping("ng", "nf", parse_int),
        "model": create_param_mapping(
            "model", "model", keep_string, default="sg13_lv_pmos"
        ),
    }

    # rppd resistor parameter mappings
    rppd_params = {
        "w": create_param_mapping(
            "w", "dx", parse_dimension
        ),  # meters -> um, width -> dx
        "l": create_param_mapping(
            "l", "dy", parse_dimension
        ),  # meters -> um, length -> dy
        "model": create_param_mapping("model", "model", keep_string, default="rppd"),
    }

    # MIM capacitor parameter mappings
    cmim_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        # "model": create_param_mapping("model", "model", keep_string, default="cmim"),
    }

    # Inductor parameter mappings
    inductor_params = {
        "inductance": create_param_mapping(
            "inductance", "inductance", parse_float
        ),  # SI, keep as-is
    }

    # Register all component mappings
    mappings["sg13_lv_nmos"] = create_component_mapping(
        "sg13_lv_nmos", "nmos", nmos_params
    )
    mappings["sg13_lv_pmos"] = create_component_mapping(
        "sg13_lv_pmos", "pmos", pmos_params
    )
    mappings["sg13_hv_nmos"] = create_component_mapping(
        "sg13_hv_nmos", "nmos", nmos_params.copy()
    )
    mappings["sg13_hv_pmos"] = create_component_mapping(
        "sg13_hv_pmos", "pmos", pmos_params.copy()
    )
    mappings["rppd"] = create_component_mapping("rppd", "rppd", rppd_params)
    mappings["cap_cmim"] = create_component_mapping("cap_cmim", "cmim", cmim_params)
    mappings["inductor"] = create_component_mapping(
        "inductor", "inductor2", inductor_params
    )

    return mappings


# ============================================================================
# SPICE PARSING FUNCTIONS
# ============================================================================


def parse_instance_line(
    line: str, component_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Parse a single SPICE instance line.

    Args:
        line: The raw line from the SPICE netlist representing an instance (e.g., "X1 in out vdd sg13_lv_nmos w=2.006n l=1.5u ng=4").
        component_mappings: The dictionary of component mappings to identify the model.
    Returns:
        A dictionary containing the instance information (name, nodes, model, parameters) or None if the line cannot be parsed as an instance.
    """
    parts = line.split()
    if len(parts) < 2:
        return None

    instance = {"name": parts[0], "nodes": [], "model": None, "parameters": {}}

    first_char = parts[0][0].upper()

    if first_char == "X":
        # Subcircuit instance: X<n> <nodes> <model> <params>
        model_idx = None
        for i in range(1, len(parts)):
            part = parts[i]
            if "=" not in part and any(c.isalpha() for c in part):
                if any(model in part for model in component_mappings.keys()):
                    model_idx = i
                    instance["model"] = part
                    break

        if model_idx:
            instance["nodes"] = parts[1:model_idx]
            for param_str in parts[model_idx + 1 :]:
                if "=" in param_str:
                    key, val = param_str.split("=", 1)
                    instance["parameters"][key] = val

    elif first_char == "L":
        # Inductor: L<n> <node1> <node2> <value>
        instance["model"] = "inductor"
        if len(parts) >= 3:
            instance["nodes"] = parts[1:3]
            if len(parts) > 3:
                instance["parameters"]["inductance"] = parts[3]

    elif first_char in ["R", "C"]:
        instance["model"] = "resistor" if first_char == "R" else "capacitor"
        if len(parts) >= 3:
            instance["nodes"] = parts[1:3]
            if len(parts) > 3:
                instance["parameters"]["value"] = parts[3]

    return instance


def parse_spice_netlist(
    spice_file: Path, component_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Parse SPICE netlist file.

    Args:
        spice_file: Path to the SPICE netlist file.
        component_mappings: The dictionary of component mappings to identify models and parameters.
    Returns:
        A dictionary containing the parsed netlist information (name, ports, instances, nets).
    """
    with open(spice_file) as f:
        lines = f.readlines()

    # Ignore ports for now
    # netlist = {"name": None, "ports": [], "instances": {}, "nets": set()}
    netlist = {"name": None, "instances": {}, "nets": set()}

    for line in lines:
        line = line.strip()

        if not line or line.startswith("**"):
            continue

        # Parse subcircuit definition
        if line.startswith(".subckt"):
            parts = line.split()
            netlist["name"] = parts[1] if len(parts) > 1 else "circuit"
            # netlist["ports"] = parts[2:] if len(parts) > 2 else []
            continue

        # Ignore ports for now
        # # Parse ports from commented iopin lines
        # if line.startswith("*.iopin"):
        #     parts = line.split()
        #     if len(parts) > 1:
        #         port_name = parts[1]
        #         if port_name not in netlist["ports"]:
        #             netlist["ports"].append(port_name)
        #     continue

        # End of subcircuit or other directives
        if line.startswith("."):
            continue

        # Skip comments
        if line.startswith("*"):
            continue

        # Parse instance lines
        first_char = line[0].upper()
        if first_char in ["X", "M", "R", "C", "L", "Q"]:
            instance = parse_instance_line(line, component_mappings)
            if instance:
                netlist["instances"][instance["name"]] = instance
                netlist["nets"].update(instance.get("nodes", []))

    netlist["nets"] = list(netlist["nets"])

    return netlist


# ============================================================================
# PIC.YML GENERATION FUNCTIONS
# ============================================================================


def convert_to_picyml(
    netlist: dict[str, Any],
    component_mappings: dict[str, dict[str, Any]],
    layout_spacing: float = 100.0,
    components_per_row: int = 5,
    gds_placements: dict[str, dict[str, Any]] | None = None,
    gds_only: bool = False,
) -> dict[str, Any]:
    """Convert parsed netlist to pic.yml structure.

    Args:
        netlist: The parsed netlist dictionary containing name, ports, instances, and nets.
        component_mappings: The dictionary of component mappings to convert SPICE models and parameters to PDK components and parameters.
        layout_spacing: The spacing in micrometers between components in the generated layout.
        components_per_row: The number of components to place in each row of the layout grid.
        gds_placements: Optional dictionary of GDS placements to use instead of grid layout.
        gds_only: If True, only include instances that have a GDS placement. Instances
                  without GDS coordinates are silently excluded from the output.

    Returns:
        A dictionary representing the pic.yml structure with instances, placements, and ports.
    """

    pic = {
        "name": netlist["name"] or "circuit",
        "instances": {},
        "placements": {},
        # "ports": {},
    }

    # Convert instances
    for inst_name, inst_data in netlist["instances"].items():
        model = inst_data["model"]

        # Check if we have a mapping for this model
        if model not in component_mappings:
            print(f"Warning: No mapping for model '{model}', skipping {inst_name}")
            continue

        # If gds_only, skip instances that have no GDS placement
        if gds_only and (not gds_placements or inst_name not in gds_placements):
            continue

        mapping = component_mappings[model]

        # Add model to parameters if not already there
        spice_params = inst_data["parameters"].copy()
        if "model" not in spice_params and model:
            spice_params["model"] = model

        # Convert parameters
        pdk_params = map_parameters(spice_params, mapping["param_mappings"])

        # Create instance entry
        pic["instances"][inst_name] = {
            "component": mapping["pdk_component"],
            "settings": pdk_params,
        }

    # Generate grid positions for all instances first as fallback
    grid_placements = {}
    x, y = 0.0, 0.0
    for i, inst_name in enumerate(pic["instances"].keys()):
        grid_placements[inst_name] = {"x": x, "y": y}
        x += layout_spacing
        if (i + 1) % components_per_row == 0:
            x = 0.0
            y += layout_spacing

    # Apply placements: GDS coordinates where available, grid otherwise
    for inst_name in pic["instances"].keys():
        if gds_placements and inst_name in gds_placements:
            placement = gds_placements[inst_name]
            pic["placements"][inst_name] = {"x": placement["x"], "y": placement["y"]}
            if placement.get("rotation", 0) != 0:
                pic["placements"][inst_name]["rotation"] = placement["rotation"]
            if placement.get("mirror", False):
                pic["placements"][inst_name]["mirror"] = placement["mirror"]
        else:
            pic["placements"][inst_name] = grid_placements[inst_name]

    # # Add ports
    # for port_name in netlist["ports"]:
    #     pic["ports"][port_name] = f"{port_name},e1"

    return pic


# ============================================================================
# FILE I/O FUNCTIONS
# ============================================================================


def convert_file(
    spice_file: Path,
    output_file: Path,
    component_mappings: dict[str, dict[str, Any]] | None = None,
    layout_spacing: float = 100.0,
    components_per_row: int = 5,
    gds_file: Path | None = None,
    poly_layer: tuple[int, int] = (128, 0),
    gds_only: bool = False,
):
    """Convert SPICE file to pic.yml file.

    Args:
        spice_file: Path to the input SPICE netlist file.
        output_file: Path to the output pic.yml file.
        component_mappings: Optional dictionary of component mappings. If None, default IHP mappings will be used.
        layout_spacing: The spacing in micrometers between components in the generated layout (default: 100).
        components_per_row: The number of components to place in each row of the layout grid (default: 5).
        gds_file: Optional path to GDS file to extract real layout coordinates for rppd resistors.
        poly_layer: The (layer, datatype) of the PolyResdrawing layer (default: (128, 0) for IHP SG13G2).
        gds_only: If True, only include instances that have GDS coordinates (default: False).

    Returns:
        None. Writes the converted pic.yml to the specified output file.
    """

    # Use default mappings if none provided
    if component_mappings is None:
        component_mappings = get_default_ihp_mappings()

    print(f"Parsing SPICE netlist: {spice_file}")
    netlist = parse_spice_netlist(spice_file, component_mappings)

    print(f"Found {len(netlist['instances'])} instances")

    # Extract GDS placements if GDS file provided
    gds_placements_matched = None
    if gds_file:
        if not gds_file.exists():
            print(f"Warning: GDS file not found: {gds_file}, using grid layout")
        else:
            rppd_data = extract_rppd_from_gds(gds_file, poly_layer=poly_layer)
            inductor_data = extract_inductors_from_gds(gds_file)
            nmos_data = extract_nmos_from_gds(gds_file)
            cmim_data = extract_cmim_from_gds(gds_file)

            if rppd_data or inductor_data or nmos_data or cmim_data:
                gds_placements_matched = match_spice_to_gds_placements(
                    netlist["instances"],
                    rppd_data=rppd_data if rppd_data else None,
                    inductor_data=inductor_data if inductor_data else None,
                    nmos_data=nmos_data if nmos_data else None,
                    cmim_data=cmim_data if cmim_data else None,
                )

    print("Converting to pic.yml format...")
    pic = convert_to_picyml(
        netlist,
        component_mappings,
        layout_spacing,
        components_per_row,
        gds_placements=gds_placements_matched,
        gds_only=gds_only,
    )

    print(f"Writing to {output_file}")
    with open(output_file, "w") as f:
        yaml.dump(pic, f, default_flow_style=False, sort_keys=False, indent=2)

    print("✓ Conversion complete!")
    print("\nSummary:")
    print(f"  - {len(pic['instances'])} components")
    # print(f"  - {len(pic['ports'])} ports")
    print(f"  - {len(pic['placements'])} placements")
    if gds_placements_matched:
        print(f"  - Used GDS coordinates from: {gds_file.name}")


def add_component_mapping(
    component_mappings: dict[str, dict[str, Any]],
    spice_model: str,
    pdk_component: str,
    param_mappings: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Add a custom component mapping to the mappings dictionary."""
    mapping = create_component_mapping(spice_model, pdk_component, param_mappings)
    component_mappings[spice_model] = mapping
    return component_mappings


# ============================================================================
# MAIN / CLI
# ============================================================================


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert SPICE netlists to gdsfactory pic.yml format"
    )
    parser.add_argument("input", type=Path, help="Input SPICE netlist file")
    parser.add_argument("output", type=Path, help="Output pic.yml file")
    parser.add_argument(
        "--gds",
        type=Path,
        help="Optional GDS file to extract real layout coordinates",
    )
    parser.add_argument(
        "--gds-only",
        action="store_true",
        help="Only include components that have GDS coordinates (requires --gds)",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=100.0,
        help="Component spacing in micrometers (default: 100)",
    )
    parser.add_argument(
        "--per-row",
        type=int,
        default=5,
        help="Components per row in grid layout (default: 5)",
    )

    args = parser.parse_args()

    if args.gds_only and not args.gds:
        parser.error("--gds-only requires --gds to be specified")

    convert_file(
        args.input,
        args.output,
        layout_spacing=args.spacing,
        components_per_row=args.per_row,
        gds_file=args.gds,
        gds_only=args.gds_only,
    )


if __name__ == "__main__":
    main()
