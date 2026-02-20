import gdsfactory as gf
from ihp import PDK
from ihp.cells.capacitors import cmom   # adjust import if needed

PDK.activate()

c = cmom(nfingers=2, length=6.0)
c.draw_ports()
c.show()      # opens in KLayout

#cd /Users/delficomerso/Desktop/IHP
#source .venv/bin/activate
#python -m ihp.s_parameters.capacitor_cmom_pdk
