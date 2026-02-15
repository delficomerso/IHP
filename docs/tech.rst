
Technology
=============================

The ``ihp.tech`` module defines the IHP SG13G2 130nm BiCMOS process technology
for use with GDSFactory. It is exposed at the top level as ``ihp.tech`` and
its key objects are re-exported by the PDK:

.. code-block:: python

   from ihp import LAYER, LAYER_STACK, LAYER_VIEWS, cross_sections
   # or equivalently:
   from ihp.tech import LAYER, LAYER_STACK, TECH

Layer Map
---------

``LAYER`` is an instance of ``LayerMapIHP``, a Pydantic model mapping every
IHP SG13G2 GDS layer to its ``(layer, datatype)`` tuple. Access layers as
attributes:

.. code-block:: python

   from ihp.tech import LAYER

   LAYER.Metal1drawing   # (8, 0)
   LAYER.TopMetal2drawing # (134, 0)
   LAYER.Activdrawing     # (1, 0)

.. autoclass:: ihp.tech.LayerMapIHP
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Layer Stack
-----------

``LAYER_STACK`` provides a 3D representation of the metal/via stack for
cross-sectional visualization and electromagnetic simulation (e.g. with Palace
or MEEP). Thicknesses follow the IHP SG13 process specifications.

The stack includes: substrate, active silicon, poly gate, Metal1--Metal5,
Via1--Via4, TopVia1, TopMetal1, TopVia2, and TopMetal2.

.. autofunction:: ihp.tech.get_layer_stack
   :noindex:

.. plot::
  :include-source:

  import warnings
  warnings.filterwarnings("ignore", category=DeprecationWarning)

  from ihp import PDK
  PDK.activate()

  fig = PDK.layer_stack.plot()

Technology Parameters
---------------------

``TECH`` is an instance of ``TechIHP`` containing process design rules:
grid size, minimum transistor dimensions, metal widths/spacings, resistor
and capacitor parameters, and RF layout rules.

.. autopydantic_model:: ihp.tech.TechIHP
   :members:
   :show-inheritance:
   :noindex:

Cross-Sections
--------------

Pre-defined cross-sections for electrical routing on each metal layer.
All cross-sections use ``port_type="electrical"``.

.. list-table::
   :header-rows: 1
   :widths: 30 20 20

   * - Name
     - Layer
     - Default Width
   * - ``metal1_routing``
     - Metal1drawing (8, 0)
     - 0.28 um
   * - ``metal2_routing``
     - Metal2drawing (10, 0)
     - 0.32 um
   * - ``metal3_routing``
     - Metal3drawing (30, 0)
     - 0.40 um
   * - ``topmetal1_routing``
     - TopMetal1drawing (126, 0)
     - 1.0 um
   * - ``topmetal2_routing``
     - TopMetal2drawing (134, 0)
     - 2.0 um

``strip`` and ``metal_routing`` are aliases for ``topmetal2_routing``.

.. autofunction:: ihp.tech.metal_routing
   :noindex:

Routing Strategies
------------------

The PDK registers these routing strategies for use with GDSFactory's
auto-routing:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Strategy
     - Description
   * - ``route_bundle``
     - Bundle routing with ``strip`` (TopMetal2) cross-section
   * - ``route_bundle_rib``
     - Bundle routing with ``rib`` cross-section
   * - ``route_bundle_metal``
     - Metal bundle routing with bends (``bend_metal``)
   * - ``route_bundle_metal_corner``
     - Metal bundle routing with 90-degree corners (``wire_corner``)
   * - ``route_astar``
     - A* pathfinding on TopMetal2 with euler bends
   * - ``route_astar_metal``
     - A* pathfinding on TopMetal2 with wire corners

Connectivity
------------

The PDK defines layer connectivity for LVS and routing:

.. code-block:: text

   Metal1  -- Via1    -- Metal2
   Metal2  -- Via2    -- Metal3
   Metal3  -- Via3    -- Metal4
   Metal4  -- Via4    -- Metal5
   Metal5  -- TopVia1 -- TopMetal1
   TopMetal1 -- TopVia2 -- TopMetal2
