#!/usr/bin/env python3
import ast
from pathlib import Path

import yaml

IHPPYCELL_DIR = Path("ihp/cells2/ihp_pycell")  # folder with pycell classes


def extract_sch_param_descriptions(py_file: Path):
    """Return {class_name: {sch_arg: description}}"""
    param_map = {}

    with py_file.open() as f:
        tree = ast.parse(f.read(), filename=str(py_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            param_map[class_name] = {}
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef)
                    and item.name == "defineParamSpecs"
                ):
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Call):
                            if getattr(stmt.func, "id", None) == "specs":
                                if stmt.args and isinstance(stmt.args[0], ast.Constant):
                                    sch_arg = stmt.args[0].value
                                else:
                                    continue
                                # get description (third argument)
                                description = (
                                    stmt.args[2].value
                                    if len(stmt.args) >= 3
                                    and isinstance(stmt.args[2], ast.Constant)
                                    else None
                                )
                                param_map[class_name][sch_arg] = description
    return param_map


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
if __name__ == "__main__":
    all_param_map = {}
    for py_file in IHPPYCELL_DIR.glob("*.py"):
        all_param_map.update(extract_sch_param_descriptions(py_file))

    out_file = Path("ihp_sch_param_descriptions.yml")
    with open(out_file, "w") as f:
        yaml.dump(all_param_map, f, sort_keys=True)
    print(f"Extracted .sch parameter descriptions saved to {out_file}")
