"""Tests unitaires de src/variables.py.

construire_panel() enchaîne plusieurs modules : elle sera testée de bout en bout
dans tests/integration/test_chaine_preparation.py.
"""

import pandas as pd
import pytest

from src.variables import CAPACITES, INDICATEURS, QUANTITES_MCO, indicateur

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


def test_indicateur_garde_les_lignes_vraies_sans_doublon():
    t = pd.DataFrame({"fi": ["1", "1", "2", "3"], "an": [2020] * 4,
                      "gde": ["A", "B", "A", "A"], "ok": [True, True, False, True]})
    r = indicateur(t, t["ok"], "a_quelque_chose")
    assert r[["fi", "an"]].values.tolist() == [["1", 2020], ["3", 2020]]   # « 1 » une seule fois
    assert r["a_quelque_chose"].tolist() == [1, 1]


def test_indicateur_smr_exige_des_sejours_en_complete():
    _, condition = INDICATEURS["a_smr"]
    t = pd.DataFrame({"gde": ["SSR_TOT", "SSR_TOT", "SSR_A50", "SSR_TOT"],
                      "sejhc": ["40", "0", "40", None]})
    assert condition(t).tolist() == [True, False, False, False]
