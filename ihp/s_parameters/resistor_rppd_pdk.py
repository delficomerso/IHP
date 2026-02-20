from ihp import PDK
from ihp.cells.resistors import rppd

PDK.activate()

c = rppd()
c.draw_ports()
c.show()
