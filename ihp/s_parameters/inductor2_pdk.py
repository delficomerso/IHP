from ihp import PDK
from ihp.cells.inductors import inductor2

PDK.activate()

c = inductor2()
c.draw_ports()
c.show()
