"""Tests unitaires de src/variables.py.

construire_panel() enchaîne plusieurs modules : elle sera testée de bout en bout
dans tests/integration/test_chaine_preparation.py.
"""

import pytest

from src.variables import CAPACITES, QUANTITES_MCO

pytestmark = pytest.mark.unitaire


def test_quantites_mco_29_colonnes_dont_l_activite():
    assert len(QUANTITES_MCO) == 29                  # 7 mesures x 4 disciplines + séances
    for colonne in ("jou_mco", "sejhp_mco", "sej0_mco", "sejhc_mco", "sea_mco", "jli_mco"):
        assert colonne in QUANTITES_MCO


def test_capacites_associe_chaque_capacite_a_son_activite():
    assert CAPACITES["lit_mco"] == "jou_mco"
    assert CAPACITES["jli_chi"] == "jou_chi"
    assert CAPACITES["pla_obs"] == "sejhp_obs"
    assert len(CAPACITES) == 12                      # 3 capacités x 4 disciplines
