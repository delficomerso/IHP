"""S-parameter model definitions for IHP PDK."""

import sax

from .generic import (
    capacitor,
    gamma_0_load,
    inductor,
    open,
    resistor,
    short,
    single_admittance_element,
    single_impedance_element,
    tee,
)
from .waveguides import (
    bend_circular,
    bend_euler,
    bend_s,
    straight,
    straight_metal,
)

sax.set_port_naming_strategy("optical")

models = {
    func.__name__: func
    for func in (
        bend_circular,
        bend_euler,
        bend_s,
        capacitor,
        gamma_0_load,
        inductor,
        open,
        resistor,
        short,
        single_admittance_element,
        single_impedance_element,
        straight,
        straight_metal,
        tee,
    )
}

__all__ = ["models", *models.keys()]
