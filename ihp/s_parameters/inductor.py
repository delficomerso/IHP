import gdsfactory as gf

gf.gpdk.PDK.activate()

c = gf.components.inductor(width=2, space=2.1, diameter=25.35, resistance=0.578, inductance=0.0, turns=1, layer_metal='M3', layer_inductor='M1', layer_metal_pin='WG_PIN', layers_no_fill=('DEVREC', 'NO_TILE_SI')).copy()
c.draw_ports()
c.show()
