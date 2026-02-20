import gdsfactory as gf

gf.gpdk.PDK.activate()

c = gf.components.interdigital_capacitor(fingers=4, finger_length=20, finger_gap=2, thickness=5, layer='WG').copy()
c.draw_ports()
c.show()