"""Tests unitaires de src/variables.py.

construire_panel() enchaîne plusieurs modules : elle sera testée de bout en bout
dans tests/integration/test_chaine_preparation.py.
"""

import numpy as np
import pandas as pd
import pytest

from src.variables import (
    CAPACITES,
    CATEGORIELLES,
    INDICATEURS,
    QUANTITES_MCO,
    REGIONS_OUTRE_MER,
    REGROUPEMENT_CATR,
    VARIABLES_INTERDITES,
    indicateur,
    ratio,
    variables_explicatives,
    verifier_sans_fuite,
)

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


# --- Variables explicatives ---

def test_ratio_vide_quand_le_denominateur_est_nul_ou_vide():
    r = ratio(pd.Series([10.0, 10.0, 10.0]), pd.Series([4.0, 0.0, np.nan]))
    assert r.iloc[0] == 2.5 and r.iloc[1:].isna().all()


def panel_trois_sites():
    """Trois sites en 2020 : A et B dans l'entité E1, C seul dans E2 (sans journées exploitables)."""
    p = pd.DataFrame({c: 0.0 for c in QUANTITES_MCO}, index=range(3))
    p["fi"], p["an"], p["fi_ej"] = ["A", "B", "C"], 2020, ["E1", "E1", "E2"]
    p["jou_mco"], p["jli_mco"] = [800.0, 300.0, 1000.0], [1000.0, 600.0, 0.0]
    p["jou_med"], p["jou_chi"], p["jou_obs"] = [400.0, 300.0, 1000.0], [400.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    p["sejhc_mco"], p["sej0_mco"], p["sejhp_mco"] = [120.0, 60.0, 100.0], [20.0, 10.0, 0.0], [400.0, 0.0, 0.0]
    p["activite"] = p["jou_mco"] + 0.5 * (p["sejhp_mco"] + p["sej0_mco"])   # 1010, 305, 1000
    p["stjr"], p["catr"], p["reg_actuelle"] = ["1", "1", "2"], ["PUB2", "PUB2", "PLU4"], ["76", "76", "11"]
    for nom in INDICATEURS:
        p[nom] = 0
    p["inc_jou_trop_bas"] = 0
    p["rs"] = ["a", "b", "c"]
    return p


def test_variables_explicatives_ratios_calcules_a_la_main():
    v = variables_explicatives(panel_trois_sites()).set_index("fi")
    assert v.loc["A", "taux_occupation_mco"] == 0.8                 # 800 / 1000
    assert np.isnan(v.loc["C", "taux_occupation_mco"])              # 0 journée exploitable : vide
    assert v.loc["A", "part_partielle_mco"] == 400 / 520            # 400 venues / (120 + 400) séjours
    assert v.loc["A", "duree_moyenne_sejour_mco"] == 8.0            # 800 / (120 - 20)
    assert v.loc["A", "part_journees_med"] == 0.5 and v.loc["C", "part_journees_med"] == 1.0
    assert v.loc["A", "log_activite"] == pytest.approx(np.log(1011))


def test_variables_explicatives_place_dans_l_entite():
    v = variables_explicatives(panel_trois_sites()).set_index("fi")
    assert v["sites_entite"].to_dict() == {"A": 2, "B": 2, "C": 1}
    assert v.loc["A", "part_site_dans_entite"] == pytest.approx(1010 / 1315)
    assert v.loc["C", "part_site_dans_entite"] == 1.0


def test_variables_explicatives_garde_les_categorielles_en_texte_et_sans_fuite():
    v = variables_explicatives(panel_trois_sites())
    assert v["catr"].tolist() == ["PUB2", "PUB2", "PLU4"]
    assert set(CATEGORIELLES) <= set(v.columns)
    assert "rs" not in v.columns and "fi_ej" not in v.columns
    verifier_sans_fuite([c for c in v.columns if c not in ("fi", "an")])   # ne lève rien


@pytest.mark.parametrize("colonne", ["activite_t1", "restructuration_probable", "changement_de_groupe", "fi_ej",
                                     "reprise_capacites", "reprise_meme_ej", "fermeture_en_cours"])
def test_verifier_sans_fuite_refuse_une_colonne_interdite(colonne):
    assert colonne in VARIABLES_INTERDITES
    with pytest.raises(ValueError, match=colonne):
        verifier_sans_fuite(["jou_mco", colonne])


def test_occupation_impossible_au_dela_de_1_5():
    p = panel_trois_sites()
    p["jou_mco"] = [1_600.0, 300.0, 1000.0]          # A : 1 600 / 1 000 = 1,6 ; B : 0,5 ; C : pas de jli
    v = variables_explicatives(p).set_index("fi")
    assert v["inc_occupation_superieure_a_1_5"].to_dict() == {"A": 1, "B": 0, "C": 0}


def test_modalites_rares_regroupees():
    p = panel_trois_sites()
    p["catr"], p["reg_actuelle"] = ["PUB10", "PLU7", "PNL4"], ["03", "76", "06"]
    v = variables_explicatives(p).set_index("fi")
    assert v["catr"].to_dict() == {"A": "PUB_autres", "B": "PLU_autres", "C": "PNL4"}
    assert v["reg_actuelle"].to_dict() == {"A": "outre_mer", "B": "76", "C": "outre_mer"}


def test_regroupements_par_statut_et_outre_mer_complets():
    # Chaque groupe garde le préfixe du statut ; les cinq régions d'outre-mer sont là.
    assert all(groupe.startswith(code[:3]) for code, groupe in REGROUPEMENT_CATR.items())
    assert sorted(REGIONS_OUTRE_MER) == ["01", "02", "03", "04", "06"]
