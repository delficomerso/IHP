"""SAX frequency-domain S-parameter models for the IHP SG13G2 PDK.

This package provides process-aware SAX models that convert IHP component
geometry parameters into S-parameter representations suitable for circuit
simulation with the `SAX <https://github.com/flaport/sax>`_ solver.

Example usage::

    import jax.numpy as jnp
    from ihp.models.sax import models, rsil

    f = jnp.linspace(1e9, 20e9, 201)

    # Use a model directly
    s_res = rsil(f=f, width=1.0, length=10.0)

    # Use the models dict for SAX circuit simulation
    import sax
    circuit, _ = sax.circuit(netlist=my_netlist, models=models)
"""

import sax

from ihp.models.sax.capacitors import (
    cmim,
    cmim_capacitance,
    cmom,
    cmom_capacitance,
    rfcmim,
    rfcmim_capacitance,
)
from ihp.models.sax.constants import DEFAULT_FREQUENCY, Z0_DEFAULT
from ihp.models.sax.inductors import inductor2, inductor3, inductor_with_loss
from ihp.models.sax.resistors import (
    resistor,
    rhigh,
    rppd,
    rsil,
)

__all__ = [
    "DEFAULT_FREQUENCY",
    "Z0_DEFAULT",
    "cmim",
    "cmim_capacitance",
    "cmom",
    "cmom_capacitance",
    "inductor2",
    "inductor3",
    "inductor_with_loss",
    "models",
    "resistor",
    "rfcmim",
    "rfcmim_capacitance",
    "rhigh",
    "rppd",
    "rsil",
]

models: dict[str, sax.Model] = {
    "resistor": resistor,
    "rsil": rsil,
    "rppd": rppd,
    "rhigh": rhigh,
    "cmim": cmim,
    "rfcmim": rfcmim,
    "cmom": cmom,
    "inductor2": inductor2,
    "inductor3": inductor3,
    "inductor_with_loss": inductor_with_loss,
}
