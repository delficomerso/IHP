import gdsfactory as gf
from ihp import PDK
from ihp.cells.capacitors import cmim

PDK.activate()

c = cmim(width=8.0, length=8.0)
c.draw_ports()
c.show()
