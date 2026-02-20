from ihp import PDK
from ihp.cells.resistors import rsil

PDK.activate()

c = rsil()
c.draw_ports()
c.show()
