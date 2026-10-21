"""Tests for device PCell sizing validation.

Verifies that all cell functions raise ValueError when given out-of-range
dimensions, and accept default (in-range) parameters without error.
"""

from __future__ import annotations

import pytest

from ihp import PDK
from ihp.tech import TECH


@pytest.fixture(autouse=True)
def activate_pdk() -> None:
    PDK.activate()


# ---------------------------------------------------------------------------
# FET transistors
# ---------------------------------------------------------------------------
class TestNmos:
    def test_default_params(self):
        from ihp.cells.fet_transistors import nmos

        nmos()

    def test_width_below_min(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos width"):
            nmos(width=TECH.nmos_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos width"):
            nmos(width=TECH.nmos_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos length"):
            nmos(length=TECH.nmos_min_length - 0.01)

    def test_length_above_max(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos length"):
            nmos(length=TECH.nmos_max_length + 0.01)

    def test_nf_above_max(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos nf"):
            nmos(nf=TECH.nmos_max_nf + 1)

    def test_nf_below_min(self):
        from ihp.cells.fet_transistors import nmos

        with pytest.raises(ValueError, match="nmos nf"):
            nmos(nf=0)


class TestPmos:
    def test_default_params(self):
        from ihp.cells.fet_transistors import pmos

        pmos()

    def test_width_below_min(self):
        from ihp.cells.fet_transistors import pmos

        with pytest.raises(ValueError, match="pmos width"):
            pmos(width=TECH.pmos_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.fet_transistors import pmos

        with pytest.raises(ValueError, match="pmos width"):
            pmos(width=TECH.pmos_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.fet_transistors import pmos

        with pytest.raises(ValueError, match="pmos length"):
            pmos(length=TECH.pmos_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.fet_transistors import pmos

        with pytest.raises(ValueError, match="pmos nf"):
            pmos(nf=TECH.pmos_max_nf + 1)


class TestNmosHv:
    def test_default_params(self):
        from ihp.cells.fet_transistors import nmos_hv

        nmos_hv()

    def test_width_below_min(self):
        from ihp.cells.fet_transistors import nmos_hv

        with pytest.raises(ValueError, match="nmos_hv width"):
            nmos_hv(width=TECH.nmos_hv_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.fet_transistors import nmos_hv

        with pytest.raises(ValueError, match="nmos_hv width"):
            nmos_hv(width=TECH.nmos_hv_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.fet_transistors import nmos_hv

        with pytest.raises(ValueError, match="nmos_hv length"):
            nmos_hv(length=TECH.nmos_hv_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.fet_transistors import nmos_hv

        with pytest.raises(ValueError, match="nmos_hv nf"):
            nmos_hv(nf=TECH.nmos_hv_max_nf + 1)


class TestPmosHv:
    def test_default_params(self):
        from ihp.cells.fet_transistors import pmos_hv

        pmos_hv()

    def test_width_below_min(self):
        from ihp.cells.fet_transistors import pmos_hv

        with pytest.raises(ValueError, match="pmos_hv width"):
            pmos_hv(width=TECH.pmos_hv_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.fet_transistors import pmos_hv

        with pytest.raises(ValueError, match="pmos_hv width"):
            pmos_hv(width=TECH.pmos_hv_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.fet_transistors import pmos_hv

        with pytest.raises(ValueError, match="pmos_hv length"):
            pmos_hv(length=TECH.pmos_hv_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.fet_transistors import pmos_hv

        with pytest.raises(ValueError, match="pmos_hv nf"):
            pmos_hv(nf=TECH.pmos_hv_max_nf + 1)


# ---------------------------------------------------------------------------
# RF transistors
# ---------------------------------------------------------------------------
class TestRfnmos:
    def test_default_params(self):
        from ihp.cells.rf_transistors import rfnmos

        rfnmos()

    def test_width_below_min(self):
        from ihp.cells.rf_transistors import rfnmos

        with pytest.raises(ValueError, match="rfnmos width"):
            rfnmos(width=TECH.rfnmos_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.rf_transistors import rfnmos

        with pytest.raises(ValueError, match="rfnmos width"):
            rfnmos(width=TECH.rfnmos_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.rf_transistors import rfnmos

        with pytest.raises(ValueError, match="rfnmos length"):
            rfnmos(length=TECH.rfnmos_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.rf_transistors import rfnmos

        with pytest.raises(ValueError, match="rfnmos nf"):
            rfnmos(nf=TECH.rfnmos_max_nf + 1)


class TestRfpmos:
    def test_default_params(self):
        from ihp.cells.rf_transistors import rfpmos

        rfpmos()

    def test_width_below_min(self):
        from ihp.cells.rf_transistors import rfpmos

        with pytest.raises(ValueError, match="rfpmos width"):
            rfpmos(width=TECH.rfpmos_min_width - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.rf_transistors import rfpmos

        with pytest.raises(ValueError, match="rfpmos nf"):
            rfpmos(nf=TECH.rfpmos_max_nf + 1)


class TestRfnmosHv:
    def test_default_params(self):
        from ihp.cells.rf_transistors import rfnmos_hv

        rfnmos_hv()

    def test_width_below_min(self):
        from ihp.cells.rf_transistors import rfnmos_hv

        with pytest.raises(ValueError, match="rfnmos_hv width"):
            rfnmos_hv(width=TECH.rfnmos_hv_min_width - 0.01)

    def test_length_below_min(self):
        from ihp.cells.rf_transistors import rfnmos_hv

        with pytest.raises(ValueError, match="rfnmos_hv length"):
            rfnmos_hv(length=TECH.rfnmos_hv_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.rf_transistors import rfnmos_hv

        with pytest.raises(ValueError, match="rfnmos_hv nf"):
            rfnmos_hv(nf=TECH.rfnmos_hv_max_nf + 1)


class TestRfpmosHv:
    def test_default_params(self):
        from ihp.cells.rf_transistors import rfpmos_hv

        rfpmos_hv()

    def test_width_below_min(self):
        from ihp.cells.rf_transistors import rfpmos_hv

        with pytest.raises(ValueError, match="rfpmos_hv width"):
            rfpmos_hv(width=TECH.rfpmos_hv_min_width - 0.01)

    def test_length_below_min(self):
        from ihp.cells.rf_transistors import rfpmos_hv

        with pytest.raises(ValueError, match="rfpmos_hv length"):
            rfpmos_hv(length=TECH.rfpmos_hv_min_length - 0.01)

    def test_nf_above_max(self):
        from ihp.cells.rf_transistors import rfpmos_hv

        with pytest.raises(ValueError, match="rfpmos_hv nf"):
            rfpmos_hv(nf=TECH.rfpmos_hv_max_nf + 1)


# ---------------------------------------------------------------------------
# BJT transistors
# ---------------------------------------------------------------------------
class TestNpn13G2:
    def test_default_params(self):
        from ihp.cells.bjt_transistors import npn13G2

        npn13G2()

    def test_nx_above_max(self):
        from ihp.cells.bjt_transistors import npn13G2

        with pytest.raises(ValueError, match="npn13G2 Nx"):
            npn13G2(Nx=TECH.npn_max_nx + 1)

    def test_nx_zero(self):
        from ihp.cells.bjt_transistors import npn13G2

        with pytest.raises(ValueError, match="npn13G2 Nx"):
            npn13G2(Nx=0)


class TestNpn13G2L:
    def test_default_params(self):
        from ihp.cells.bjt_transistors import npn13G2L

        npn13G2L()

    def test_nx_above_max(self):
        from ihp.cells.bjt_transistors import npn13G2L

        with pytest.raises(ValueError, match="npn13G2L Nx"):
            npn13G2L(Nx=TECH.npn_max_nx + 1)


class TestNpn13G2V:
    def test_default_params(self):
        from ihp.cells.bjt_transistors import npn13G2V

        npn13G2V()

    def test_nx_above_max(self):
        from ihp.cells.bjt_transistors import npn13G2V

        with pytest.raises(ValueError, match="npn13G2V Nx"):
            npn13G2V(Nx=TECH.npn_max_nx + 1)


class TestPnpMPA:
    def test_default_params(self):
        from ihp.cells.bjt_transistors import pnpMPA

        pnpMPA()

    def test_width_below_min(self):
        from ihp.cells.bjt_transistors import pnpMPA

        with pytest.raises(ValueError, match="pnpMPA width"):
            pnpMPA(width=TECH.pnp_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.bjt_transistors import pnpMPA

        with pytest.raises(ValueError, match="pnpMPA width"):
            pnpMPA(width=TECH.pnp_max_width + 0.01)

    def test_length_below_min(self):
        from ihp.cells.bjt_transistors import pnpMPA

        with pytest.raises(ValueError, match="pnpMPA length"):
            pnpMPA(length=TECH.pnp_min_length - 0.01)

    def test_length_above_max(self):
        from ihp.cells.bjt_transistors import pnpMPA

        with pytest.raises(ValueError, match="pnpMPA length"):
            pnpMPA(length=TECH.pnp_max_length + 0.01)


# ---------------------------------------------------------------------------
# Resistors
# ---------------------------------------------------------------------------
class TestRsil:
    def test_default_params(self):
        from ihp.cells.resistors import rsil

        rsil()

    def test_dx_below_min(self):
        from ihp.cells.resistors import rsil

        with pytest.raises(ValueError, match="rsil dx"):
            rsil(dx=TECH.rsil_min_width - 0.01)

    def test_dx_above_max(self):
        from ihp.cells.resistors import rsil

        with pytest.raises(ValueError, match="rsil dx"):
            rsil(dx=TECH.rsil_max_width + 1)

    def test_dy_below_min(self):
        from ihp.cells.resistors import rsil

        with pytest.raises(ValueError, match="rsil dy"):
            rsil(dy=TECH.rsil_min_length - 0.01)

    def test_dy_above_max(self):
        from ihp.cells.resistors import rsil

        with pytest.raises(ValueError, match="rsil dy"):
            rsil(dy=TECH.rsil_max_length + 1)


class TestRppd:
    def test_default_params(self):
        from ihp.cells.resistors import rppd

        rppd()

    def test_dx_below_min(self):
        from ihp.cells.resistors import rppd

        with pytest.raises(ValueError, match="rppd dx"):
            rppd(dx=TECH.rppd_min_width - 0.01)

    def test_dy_below_min(self):
        from ihp.cells.resistors import rppd

        with pytest.raises(ValueError, match="rppd dy"):
            rppd(dy=TECH.rppd_min_length - 0.01)


class TestRhigh:
    def test_default_params(self):
        from ihp.cells.resistors import rhigh

        rhigh()

    def test_dx_below_min(self):
        from ihp.cells.resistors import rhigh

        with pytest.raises(ValueError, match="rhigh dx"):
            rhigh(dx=TECH.rhigh_min_width - 0.01)

    def test_dy_below_min(self):
        from ihp.cells.resistors import rhigh

        with pytest.raises(ValueError, match="rhigh dy"):
            rhigh(dy=TECH.rhigh_min_length - 0.01)


# ---------------------------------------------------------------------------
# Capacitors
# ---------------------------------------------------------------------------
class TestCmim:
    def test_default_params(self):
        from ihp.cells.capacitors import cmim

        cmim()

    def test_width_below_min(self):
        from ihp.cells.capacitors import cmim

        with pytest.raises(ValueError, match="cmim width"):
            cmim(width=TECH.cmim_min_size - 0.01)

    def test_width_above_max(self):
        from ihp.cells.capacitors import cmim

        with pytest.raises(ValueError, match="cmim width"):
            cmim(width=TECH.cmim_max_size + 1)

    def test_length_below_min(self):
        from ihp.cells.capacitors import cmim

        with pytest.raises(ValueError, match="cmim length"):
            cmim(length=TECH.cmim_min_size - 0.01)


class TestRfcmim:
    def test_default_params(self):
        from ihp.cells.capacitors import rfcmim

        rfcmim(width=7.0, length=7.0)

    def test_width_below_min(self):
        from ihp.cells.capacitors import rfcmim

        with pytest.raises(ValueError, match="rfcmim width"):
            rfcmim(width=TECH.rfcmim_min_size - 0.01, length=7.0)

    def test_length_below_min(self):
        from ihp.cells.capacitors import rfcmim

        with pytest.raises(ValueError, match="rfcmim length"):
            rfcmim(width=7.0, length=TECH.rfcmim_min_size - 0.01)


# ---------------------------------------------------------------------------
# Passives (taps, sealring)
# ---------------------------------------------------------------------------
class TestPtap1:
    def test_default_params(self):
        from ihp.cells.passives import ptap1

        ptap1()

    def test_width_below_min(self):
        from ihp.cells.passives import ptap1

        with pytest.raises(ValueError, match="ptap1 width"):
            ptap1(width=TECH.ptap1_min_size - 0.01)

    def test_length_below_min(self):
        from ihp.cells.passives import ptap1

        with pytest.raises(ValueError, match="ptap1 length"):
            ptap1(length=TECH.ptap1_min_size - 0.01)


class TestNtap1:
    def test_default_params(self):
        from ihp.cells.passives import ntap1

        ntap1()

    def test_width_below_min(self):
        from ihp.cells.passives import ntap1

        with pytest.raises(ValueError, match="ntap1 width"):
            ntap1(width=TECH.ntap1_min_size - 0.01)

    def test_length_below_min(self):
        from ihp.cells.passives import ntap1

        with pytest.raises(ValueError, match="ntap1 length"):
            ntap1(length=TECH.ntap1_min_size - 0.01)


class TestSealring:
    def test_default_params(self):
        from ihp.cells.passives import sealring

        sealring()

    def test_width_below_min(self):
        from ihp.cells.passives import sealring

        with pytest.raises(ValueError, match="sealring width"):
            sealring(width=TECH.sealring_min_width - 1)

    def test_width_above_max(self):
        from ihp.cells.passives import sealring

        with pytest.raises(ValueError, match="sealring width"):
            sealring(width=TECH.sealring_max_width + 1)

    def test_height_below_min(self):
        from ihp.cells.passives import sealring

        with pytest.raises(ValueError, match="sealring height"):
            sealring(height=TECH.sealring_min_height - 1)

    def test_height_above_max(self):
        from ihp.cells.passives import sealring

        with pytest.raises(ValueError, match="sealring height"):
            sealring(height=TECH.sealring_max_height + 1)


# ---------------------------------------------------------------------------
# Antennas
# ---------------------------------------------------------------------------
class TestDantenna:
    def test_default_params(self):
        from ihp.cells.antennas import dantenna

        dantenna()

    def test_width_below_min(self):
        from ihp.cells.antennas import dantenna

        with pytest.raises(ValueError, match="dantenna width"):
            dantenna(width=TECH.dantenna_min_width - 0.01)

    def test_width_above_max(self):
        from ihp.cells.antennas import dantenna

        with pytest.raises(ValueError, match="dantenna width"):
            dantenna(width=TECH.dantenna_max_width + 1)

    def test_length_below_min(self):
        from ihp.cells.antennas import dantenna

        with pytest.raises(ValueError, match="dantenna length"):
            dantenna(length=TECH.dantenna_min_length - 0.01)


class TestDpantenna:
    def test_default_params(self):
        from ihp.cells.antennas import dpantenna

        dpantenna()

    def test_width_below_min(self):
        from ihp.cells.antennas import dpantenna

        with pytest.raises(ValueError, match="dpantenna width"):
            dpantenna(width=TECH.dpantenna_min_width - 0.01)

    def test_length_below_min(self):
        from ihp.cells.antennas import dpantenna

        with pytest.raises(ValueError, match="dpantenna length"):
            dpantenna(length=TECH.dpantenna_min_length - 0.01)
