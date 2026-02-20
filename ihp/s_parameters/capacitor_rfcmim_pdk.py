import gdsfactory as gf
from ihp import PDK
from ihp.cells.capacitors import rfcmim

PDK.activate()

c = rfcmim(width=10.0, length=10.0)
c.draw_ports()
c.show()
