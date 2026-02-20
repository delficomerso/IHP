from ihp import PDK
from ihp.cells.inductors import inductor3

PDK.activate()

c = inductor3()
c.draw_ports()
c.show()


