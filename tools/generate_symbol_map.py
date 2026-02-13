#!/usr/bin/env python3
import ast
import re
from pathlib import Path

import yaml

# -------------------------------------------------------------------
# Folders inside IHP/ihp
# -------------------------------------------------------------------
HIP_DIR = Path("ihp")
CELLS_FOLDERS = ["cells", "cells2"]  # folders to scan for gf.cell functions
PYCELL_FOLDER = HIP_DIR / "cells2" / "ihp_pycell"  # folder with pycell classes
EXCLUDE_FILES = {"__init__.py", "fixed.py", "ihp_pycell"}  # files to ignore


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def normalize(name: str) -> str:
    """Normalize CamelCase and snake_case to comparable lowercase string."""
    return re.sub(r"_", "", name).lower()


def get_classes_from_file(py_file: Path):
    """Extract class names inheriting from DloGen."""
    classes = []
    with py_file.open() as f:
        tree = ast.parse(f.read(), filename=str(py_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "DloGen":
                    classes.append(node.name)
    return classes


def get_cells_from_file(py_file: Path):
    """Return a list of gf.cell function names in a Python file."""
    cells = []
    with py_file.open() as f:
        tree = ast.parse(f.read(), filename=str(py_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # @gf.cell
                if isinstance(decorator, ast.Attribute):
                    if (
                        getattr(decorator.value, "id", "") == "gf"
                        and decorator.attr == "cell"
                    ):
                        cells.append(node.name)
                # @cell (if imported directly)
                elif isinstance(decorator, ast.Name) and decorator.id == "cell":
                    cells.append(node.name)
    return cells


# -------------------------------------------------------------------
# Collect data
# -------------------------------------------------------------------
def collect_pycell_classes():
    pycell_classes = []
    for py_file in PYCELL_FOLDER.glob("*.py"):
        pycell_classes.extend(get_classes_from_file(py_file))
    return pycell_classes


def collect_gf_cells():
    gf_cells = []
    for folder in CELLS_FOLDERS:
        folder_path = HIP_DIR / folder
        if not folder_path.exists():
            continue
        for py_file in folder_path.rglob("*.py"):
            if py_file.name in EXCLUDE_FILES:
                continue
            gf_cells.extend(get_cells_from_file(py_file))
    return gf_cells


# -------------------------------------------------------------------
# Generate symbol map
# -------------------------------------------------------------------
def generate_symbol_map():
    symbol_map = {}

    pycell_classes = collect_pycell_classes()
    gf_cells = collect_gf_cells()

    # Normalize gf cells into lookup dictionary
    normalized_cells = {normalize(cell): cell for cell in gf_cells}

    for class_name in pycell_classes:
        norm_class = normalize(class_name)

        if norm_class in normalized_cells:
            matched_cell = normalized_cells[norm_class]
            symbol_map[f"{class_name}.sym"] = matched_cell
        else:
            print(f"No match found for {class_name}")

    return symbol_map


# -------------------------------------------------------------------
# Save to YAML for inspection
# -------------------------------------------------------------------
if __name__ == "__main__":
    smap = generate_symbol_map()
    out_file = Path("tools") / "symbol_map.yml"
    with open(out_file, "w") as f:
        yaml.dump(smap, f, sort_keys=True)
    print(f"Symbol map saved to {out_file}")
