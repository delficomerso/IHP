from ihp import PDK
from ihp.cells.resistors import rhigh

PDK.activate()

c = rhigh()
c.draw_ports()
c.show()
