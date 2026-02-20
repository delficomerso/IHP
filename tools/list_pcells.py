#!/usr/bin/env python3
from pathlib import Path
import ast
import yaml

HIP_DIR = Path(__file__).resolve().parent.parent / "ihp"
CELLS_FOLDERS = ["cells2"]
EXCLUDE_DIRS = {"ihp_pycell"}
EXCLUDE_FILES = {"__init__.py","waveguides.py"}


def get_gf_cells_from_file(py_file: Path):
    cells = []
    with py_file.open() as f:
        tree = ast.parse(f.read(), filename=str(py_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # @gf.cell
                if isinstance(decorator, ast.Attribute):
                    if getattr(decorator.value, "id", "") == "gf" and decorator.attr == "cell":
                        cells.append(node.name)
                # @cell (imported directly)
                elif isinstance(decorator, ast.Name) and decorator.id == "cell":
                    cells.append(node.name)

    return cells


def collect_all_gf_cells():
    gf_cells = []

    for folder in CELLS_FOLDERS:
        folder_path = HIP_DIR / folder
        if not folder_path.exists():
            continue

        for py_file in folder_path.rglob("*.py"):
            if py_file.name in EXCLUDE_FILES:
                continue
            if any(excluded in py_file.parts for excluded in EXCLUDE_DIRS):
                continue

            cells = get_gf_cells_from_file(py_file)
            for cell in cells:
                gf_cells.append({
                    "name": cell
                })
    return gf_cells


if __name__ == "__main__":
    cells = collect_all_gf_cells()

    out_file = Path(__file__).resolve().parent / "available_pcells.yml"

    with open(out_file, "w") as f:
        yaml.dump({"gf_pcells": cells}, f, sort_keys=False)

    print(f"Saved {len(cells)} pcells to {out_file}")
