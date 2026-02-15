import inspect

from gdsfactory.get_factories import get_cells

from ihp import PDK
from ihp import cells2 as cells2_module
from ihp.config import PATH

filepath_cells = PATH.repo / "docs" / "cells.rst"
filepath_fixed = PATH.repo / "docs" / "cells_fixed.rst"
filepath_cells2 = PATH.repo / "docs" / "cells2_reference.rst"

skip = {
    "LIBRARY",
    "circuit_names",
    "component_factory",
    "component_names",
    "container_names",
    "component_names_test_ports",
    "component_names_skip_test",
    "component_names_skip_test_ports",
    "dataclasses",
    "library",
    "waveguide_template",
    # primitives.py — schematic-only VLSIR cells, no GDS geometry
    "resistor",
    "capacitor",
    "inductor",
    "mos",
    "diode",
    "bipolar",
    "vsource",
    "isource",
    "vcvs",
    "vccs",
    "cccs",
    "ccvs",
    "tline",
    "subckt",
    # utilities, not cells
    "import_gds",
}

skip_plot: tuple[str, ...] = ("",)
skip_settings: tuple[str, ...] = ("flatten", "safe_cell_names")

cells = PDK.cells


def write_cell_entry(f, name, cell_dict, module_path="ihp.cells", import_alias="cells"):
    """Write a single cell's RST entry (autofunction + plot)."""
    sig = inspect.signature(cell_dict[name])
    kwargs = ", ".join(
        [
            f"{p}={repr(sig.parameters[p].default)}"
            for p in sig.parameters
            if isinstance(sig.parameters[p].default, int | float | str | tuple)
            and p not in skip_settings
        ]
    )
    if name in skip_plot:
        f.write(
            f"""

{name}
----------------------------------------------------

.. autofunction:: {module_path}.{name}

"""
        )
    else:
        f.write(
            f"""

{name}
----------------------------------------------------

.. autofunction:: {module_path}.{name}

.. plot::
  :include-source:

  import warnings
  warnings.filterwarnings("ignore", category=DeprecationWarning)

  from ihp import PDK
  from ihp import {import_alias}

  PDK.activate()

  c = {import_alias}.{name}({kwargs}).copy()
  c.draw_ports()
  c.plot()

"""
        )


# Write parametric cells page
with open(filepath_cells, "w+") as f:
    f.write(
        """

Parametric Cells
=============================

Here are the parametric components available in the PDK.
"""
    )

    for name in sorted(cells.keys()):
        if name in skip or name.startswith("_") or name.endswith("_fixed"):
            continue
        print(name)
        write_cell_entry(f, name, cells, "ihp.cells", "cells")


# Write deprecated fixed cells page
with open(filepath_fixed, "w+") as f:
    f.write(
        """

Fixed Cells (Deprecated)
=============================

.. deprecated:: v0.2.0
   The fixed-GDS cells below are deprecated. Use the equivalent pure-Python
   parametric cells from the :doc:`cells` page instead.
"""
    )

    for name in sorted(cells.keys()):
        if name in skip or name.startswith("_") or not name.endswith("_fixed"):
            continue
        print(name)
        write_cell_entry(f, name, cells, "ihp.cells", "cells")


# Write cells2 PyCell reference page
cells2 = get_cells(cells2_module)

with open(filepath_cells2, "w+") as f:
    f.write(
        """

PyCell Reference (cells2)
=============================

These are reference implementations of the IHP SG13G2 PyCells, ported from the
original CNI (Cadence PyCell) library to GDSFactory. The ``ihp_pycell`` subfolder
contains the original CNI-based source code.

These cells serve as a validation reference for the primary parametric cells in
:doc:`cells`. They can also be used directly if needed.
"""
    )

    for name in sorted(cells2.keys()):
        if name in skip or name.startswith("_"):
            continue
        print(name)
        write_cell_entry(f, name, cells2, "ihp.cells2", "cells2")
