"""BJT Transistor components for IHP PDK."""

import math

import gdsfactory as gf
from gdsfactory.typings import LayerSpec

from cni.tech import Tech

tech_name = "SG13_dev"
tech = Tech.get("SG13_dev").getTechParams()


@gf.cell
def npn13G2(
    baspolyx: float = 0.3,
    bipwinx: float = 0.07,
    bipwiny: float = 0.1,
    empolyx: float = 0.15,
    empolyy: float = 0.18,
    STI: float = 0.44,
    emitter_length: float = 0.9,
    emitter_width: float = 0.7,
    Nx: int = 1,
    Ny: int = 1,
    text: str = "npn13G2",
    CMetY1: float = 0,
    CMetY2: float = 0,
) -> gf.Component:
    """Returns the IHP npn13G2 BJT transistor as a gdsfactory Component.

    Args:
        Nx: Number of emitter fingers in the x-direction.
        Ny: Number of emitter fingers in the y-direction.
        emitter_length: Length of the emitter region in microns.
        emitter_width: Width of the emitter region in microns.
        STI: Shallow Trench Isolation width in microns.
        baspolyx: Base poly extension in x-direction in microns.
        bipwinx: Bipolar window extension in x-direction in microns.
        bipwiny: Bipolar window extension in y-direction in microns.
        empolyx: Emitter poly extension in x-direction in microns.
        empolyy: Emitter poly extension in y-direction in microns.
        text: Text label for the transistor.
        CMetY1: Contact metal Y1 dimension in microns.
        CMetY2: Contact metal Y2 dimension in microns.

    Returns:
        gdsfactory.Component: The generated npn13G2 transistor layout.
    """

    c = gf.Component()

    def _snap_width_to_grid(width_um: float) -> float:
        """Snap port width to the nearest multiple of 0.002 um (2 DBU = 0.002 um).

        Args:
            width_um: Port width in microns.

        Returns:
            Width snapped to the nearest valid grid multiple.
        """
        grid = 0.002
        w = max(width_um, grid)
        return round(w / grid) * grid

    layer_via1: LayerSpec = "Via1drawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_cont: LayerSpec = "Contdrawing"
    layer_emwind: LayerSpec = "EmWinddrawing"
    layer_activmask: LayerSpec = "Activmask"
    layer_activ: LayerSpec = "Activdrawing"
    layer_metal1: LayerSpec = "Metal1drawing"
    layer_metal1_pin: LayerSpec = "Metal1pin"
    layer_metal2_pin: LayerSpec = "Metal2pin"
    layer_metal2: LayerSpec = "Metal2drawing"
    layer_nSDblock: LayerSpec = "nSDblock"
    layer_text: LayerSpec = "TEXTdrawing"
    layer_trans: LayerSpec = "TRANSdrawing"
    layer_pSD: LayerSpec = "pSDdrawing"

    ActivShift = 0.01
    ActivShift = 0.0

    # for multiplied npn: le has to be bigger
    stepX = 1.85
    stretchX = stepX * (Nx - 1)

    # stretchX = stepX * (Nx - 1)
    bipwinyoffset = (2 * (bipwiny - 0.1) - 0) / 2
    empolyyoffset = (2 * (empolyy - 0.18)) / 2

    empolyxoffset = (2 * (empolyx - 0.15)) / 2
    baspolyxoffset = (2 * (baspolyx - 0.3)) / 2
    STIoffset = (2 * (STI - 0.44)) / 2

    tmp = emitter_length
    le = emitter_width
    we = tmp

    nSDBlockShift = (
        0.43 - le
    )  # 23.07.09: needed to draw nSDBlock shorter in small pCell

    leoffset = 0  # ((le - 0.07) / 2)

    ##############
    # npn13G2_base

    pcStepY = 0.41
    yOffset = 0.20

    pcRepeatY = 4

    if Nx > 1:
        CMetY1 = 1.01 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        CMetY2 = 0.57 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
    else:
        CMetY1 = 0.8 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        CMetY2 = 0.56 + we / 2 + leoffset + bipwinyoffset + empolyyoffset

    for pcIndexX in range(int(math.floor(Nx))):
        # loop for generate the given number of vias in variable pcRepeatY
        # two vias are generated per loop
        for pcIndexY in range(int(math.floor(pcRepeatY))):
            # Via on left side
            via1_size = 0.19
            left = (stepX * pcIndexX) - 0.3
            bottom = (
                -(
                    (-0.3 - yOffset - leoffset - bipwinyoffset - empolyyoffset)
                    + (pcIndexY * pcStepY)
                )
                + 0.2
                - via1_size
            )
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        via1_size,
                        via1_size,
                    ),
                    layer=layer_via1,
                )
            ).move((left, bottom))

            left = (stepX * pcIndexX) + 0.11
            # Via on the right side
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        via1_size,
                        via1_size,
                    ),
                    layer=layer_via1,
                )
            ).move((left, bottom))

        # Emitter metal
        left = (stepX * pcIndexX) - 0.35
        bottom = -(0.335 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stepX * pcIndexX + 0.35
        top = -(-0.32 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))
        # Cont layer
        left = stepX * pcIndexX - 0.79 - le / 2
        top = -(-0.76 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = stepX * pcIndexX + 0.79 + le / 2
        bottom = -(-0.6 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_cont,
            )
        ).move((left, bottom))

        left = stepX * pcIndexX - 0.76
        top = -(0.61 + we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = stepX * pcIndexX + 0.76
        bottom = -(0.77 + we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_cont,
            )
        ).move((left, bottom))

        # EmWind
        left = stepX * pcIndexX - le / 2
        top = we / 2 + leoffset
        right = stepX * pcIndexX + le / 2
        bottom = -we / 2 - leoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_emwind,
            )
        ).move((left, bottom))

        # Activmask
        xl = stepX * pcIndexX - 0.06
        xh = xl + 0.12
        yl = -0.24 - leoffset
        yh = -yl

        c.add_polygon(
            [
                (xh + 0.865, -yl + 0.74),
                (xl - 0.865, -yl + 0.74),
                (xl - 0.865, -yh - 0.38),
                (xl - 0.385, -yh - 0.38),
                (xl - 0.175, -yh - 0.59),
                (xh + 0.175, -yh - 0.59),
                (xh + 0.385, -yh - 0.38),
                (xh + 0.865, -yh - 0.38),
            ],
            layer=layer_activmask,
        )

        # Activ
        left = (
            stepX * pcIndexX
            - 0.89
            - le / 2
            - empolyxoffset
            - baspolyxoffset
            - STIoffset
        )
        top = -(-0.83 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        right = (
            stepX * pcIndexX
            + 0.89
            + le / 2
            + empolyxoffset
            + baspolyxoffset
            + STIoffset
        )
        bottom = -(-0.89 - we / 2 + 0.36 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_activ,
            )
        ).move((left, bottom))

        c.add_polygon(
            [
                (
                    stepX * pcIndexX
                    + 0.94
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(1.98 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.94
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(0.45 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.52
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(0.03 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    + 0.52
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(
                        -0.6
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    + 0.27
                    + le / 2
                    + empolyxoffset
                    + baspolyxoffset
                    + STIoffset,
                    -(
                        -0.85
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.27
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(
                        -0.85
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.52
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(
                        -0.6
                        - we / 2
                        + leoffset
                        + bipwinyoffset
                        + empolyyoffset
                        + nSDBlockShift
                    ),
                ),
                (
                    stepX * pcIndexX
                    - 0.52
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(0.03 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    - 0.94
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(0.45 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stepX * pcIndexX
                    - 0.94
                    - le / 2
                    - empolyxoffset
                    - baspolyxoffset
                    - STIoffset,
                    -(1.98 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
            ],
            layer=layer_nSDblock,
        )

        # Collector metal
        left = -0.89 - le / 2
        top = CMetY1
        right = stretchX + 0.89 + le / 2
        bottom = CMetY2
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))

        # Base metal
        left = -0.94 - le / 2
        bottom = -(0.81 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stretchX + 0.94 + le / 2
        top = -(0.57 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1,
            )
        ).move((left, bottom))

        # Metal2
        left = -0.89 - le / 2
        bottom = -(0.335 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)
        right = stretchX + 0.89 + le / 2
        top = -(-0.32 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal2,
            )
        ).move((left, bottom))

        c.add_label(
            text=text,
            layer=layer_text,
            position=(
                0.015,
                1.86 + we / 2 + leoffset + bipwinyoffset + empolyyoffset,
            ),
        )

        c.add_polygon(
            [
                (
                    stretchX + 2.45,
                    (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (-2.45, (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (-2.45, (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (
                    stretchX + 2.45,
                    (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
            ],
            layer=layer_trans,
        )

        c.add_polygon(
            [
                (
                    stretchX + 3.35,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
                (-2.45, (-1.98 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (-2.45, (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (
                    stretchX + 2.45,
                    (2.43 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (
                    stretchX + 2.45,
                    (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset),
                ),
                (-3.35, (3.33 + we / 2 + leoffset + bipwinyoffset + empolyyoffset)),
                (-3.35, (-2.88 - we / 2 - leoffset - bipwinyoffset - empolyyoffset)),
                (
                    stretchX + 3.35,
                    (-2.88 - we / 2 - leoffset - bipwinyoffset - empolyyoffset),
                ),
            ],
            layer=layer_pSD,
        )

        c.add_polygon(
            [
                (
                    stretchX + 3.15 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    -2.18
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    -2.65 - ActivShift,
                    -2.18
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    -2.65 - ActivShift,
                    2.63
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    2.63
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    stretchX + 2.65 + ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    -3.15 - ActivShift,
                    3.13
                    + we / 2
                    + leoffset
                    + bipwinyoffset
                    + empolyyoffset
                    + ActivShift,
                ),
                (
                    -3.15 - ActivShift,
                    -2.68
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
                (
                    stretchX + 3.15 + ActivShift,
                    -2.68
                    - we / 2
                    - leoffset
                    - bipwinyoffset
                    - empolyyoffset
                    - ActivShift,
                ),
            ],
            layer=layer_activ,
        )

        if Nx > 1:
            left = -0.89 - le / 2
            bottom = 0.57 + we / 2 - leoffset - bipwinyoffset - empolyyoffset
            right = stretchX + 0.89 + le / 2
            top = 1.01 + we / 2 - leoffset - bipwinyoffset - empolyyoffset
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        right - left,
                        top - bottom,
                    ),
                    layer=layer_metal1_pin,
                )
            ).move((left, bottom))
            c.add_label(
                text="C",
                layer=layer_text,
                position=(
                    0.5 * (left + right),
                    0.5 * (top + bottom),
                ),
            )
        else:
            left = -0.89 - le / 2
            bottom = 0.56 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
            right = stretchX + 0.89 + le / 2
            top = 0.8 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
            c.add_ref(
                gf.components.rectangle(
                    size=(
                        right - left,
                        top - bottom,
                    ),
                    layer=layer_metal1_pin,
                )
            ).move((left, bottom))
            c.add_label(
                text="C",
                layer=layer_text,
                position=(
                    0.5 * (left + right),
                    0.5 * (top + bottom),
                ),
            )
        # Collector port
        c.add_port(
            "C",
            center=(0.5 * (left + right), 0.5 * (top + bottom)),
            width=_snap_width_to_grid(top - bottom),
            layer=layer_metal1_pin,
            orientation=180.0,
            port_type="electrical",
        )

        left = -0.94 - le / 2
        bottom = -0.81 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
        right = stretchX + 0.94 + le / 2
        top = -0.57 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal1_pin,
            )
        ).move((left, bottom))
        c.add_label(
            text="B",
            layer=layer_text,
            position=(
                0.5 * (left + right),
                0.5 * (top + bottom),
            ),
        )

        # Base port
        c.add_port(
            "B",
            center=(0.5 * (left + right), 0.5 * (top + bottom)),
            width=_snap_width_to_grid(top - bottom),
            layer=layer_metal1_pin,
            orientation=180.0,
            port_type="electrical",
        )

        left = -0.71 - le / 2
        bottom = -0.335 - we / 2 - leoffset - bipwinyoffset - empolyyoffset
        right = stretchX + 0.71 + le / 2
        top = 0.32 + we / 2 + leoffset + bipwinyoffset + empolyyoffset
        c.add_ref(
            gf.components.rectangle(
                size=(
                    right - left,
                    top - bottom,
                ),
                layer=layer_metal2_pin,
            )
        ).move((left, bottom))
        c.add_label(
            text="E",
            layer=layer_text,
            position=(
                0.5 * (left + right),
                0.5 * (top + bottom),
            ),
        )

        pcLabelText = f"Ae={int(Nx):d}*{int(Ny):d}*{le:.2f}*{we:.2f}"
        c.add_label(text=pcLabelText, layer=layer_text, position=(-1.977, -2.546))

        # Emitter port
        c.add_port(
            "E",
            center=(0.5 * (left + right), 0.5 * (top + bottom)),
            width=_snap_width_to_grid(top - bottom),
            layer=layer_metal2_pin,
            orientation=180.0,
            port_type="electrical",
        )

    return c


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK, cells2

    PDK.activate()
    c0 = cells2.npn13G2()
    c1 = npn13G2()
    c = xor(c0, c1)
    c.show()
