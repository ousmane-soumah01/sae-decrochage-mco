"""Tests unitaires de src/cible.py, sur l'exemple des cinq établissements calculé à la main.

Passage 2023 -> 2024 (activités en journées-équivalentes, seuil 1 000) :
    A  124 000 -> 129 500     B  22 500 -> 16 900     C  6 700 -> 6 140
    D    9 300 -> absent      E     325 -> 325 (sous le seuil)
    référence = 152 540 / 153 200 - 1 = -0,4308 %
"""

import pandas as pd
import pytest

from src.cible import (
    citations_fusion_scission,
    classer,
    construire_passages,
    ecarts_et_decrochages,
    reference_ponderee,
    restructurations,
)
from src.config import charger_config

pytestmark = pytest.mark.unitaire


@pytest.fixture
def config():
    return charger_config()


def panel_exemple():
    lignes = [
        ("A", 2023, "EJ_A", 124_000), ("A", 2024, "EJ_A", 129_500),
        ("B", 2023, "EJ_B", 22_500), ("B", 2024, "EJ_B", 16_900),
        ("C", 2023, "EJ_C", 6_700), ("C", 2024, "EJ_C", 6_140),
        ("D", 2023, "EJ_D", 9_300),                                   # absente en 2024
        ("E", 2023, "EJ_E", 325), ("E", 2024, "EJ_E", 325),
    ]
    return pd.DataFrame(lignes, columns=["fi", "an", "fi_ej", "activite"])


def test_construire_passages_exclut_e_et_garde_d(config):
    p = construire_passages(panel_exemple(), config).set_index("fi")
    assert sorted(p.index) == ["A", "B", "C", "D"]                  # E (325 < 1 000) exclu
    assert not p.loc["D", "actif_t1"] and p.loc["A", "actif_t1"]
    assert (p["t"] == 2023).all() and (p["t1"] == 2024).all()


def test_construire_passages_ignore_la_derniere_annee(config):
    # 2024 n'a pas d'année suivante dans le panel : aucun passage 2024 -> 2025.
    assert 2024 not in set(construire_passages(panel_exemple(), config)["t"])


def test_construire_passages_activite_nulle_en_t1_n_est_pas_active(config):
    panel = pd.DataFrame({"fi": ["X", "X"], "an": [2023, 2024], "fi_ej": ["E1", "E1"],
                          "activite": [5000.0, 0.0]})
    assert construire_passages(panel, config)["actif_t1"].tolist() == [False]


def test_reference_ponderee_retrouve_le_calcul_a_la_main(config):
    ref = reference_ponderee(construire_passages(panel_exemple(), config))
    assert ref[2023] == pytest.approx(152_540 / 153_200 - 1)       # -0,4308 %
    assert ref[2023] == pytest.approx(-0.004308, abs=1e-6)

def test_ecarts_et_decrochages_retrouvent_le_calcul_a_la_main(config):
    p = ecarts_et_decrochages(construire_passages(panel_exemple(), config), config).set_index("fi")
    assert p.loc["B", "evolution"] == pytest.approx(-0.248889, abs=1e-6)
    assert p.loc["B", "ecart_points"] == pytest.approx(-24.4581, abs=1e-4)
    assert p.loc["C", "ecart_points"] == pytest.approx(-7.9274, abs=1e-4)
    assert p["decrochage"].to_dict() == {"A": False, "B": True, "C": False, "D": False}
    assert pd.isna(p.loc["D", "evolution"])                          # inactif en t+1 : pas d'évolution


def test_decrochage_seuil_strict_a_15_points(config):
    # R domine la référence (≈ -0,03 %) : S à -14,9 % ne décroche pas, T à -15,1 % décroche.
    panel = pd.DataFrame({
        "fi": ["R", "R", "S", "S", "T", "T"], "an": [2023, 2024] * 3, "fi_ej": ["E"] * 6,
        "activite": [1_000_000.0, 1_000_000.0, 1000.0, 851.0, 1000.0, 849.0],
    })
    p = ecarts_et_decrochages(construire_passages(panel, config), config).set_index("fi")
    assert not p.loc["S", "decrochage"]
    assert p.loc["T", "decrochage"]


def test_decrochage_suit_l_ecart_de_config(config):
    config["cible"]["ecart_points"] = 5                             # variante de robustesse
    p = ecarts_et_decrochages(construire_passages(panel_exemple(), config), config).set_index("fi")
    assert p.loc["C", "decrochage"]                                  # -7,9 points < -5

# --- classer : sorties et réapparitions ---------------------------------------------

def test_classer_retrouve_les_verdicts_a_la_main(config):
    panel = panel_exemple()
    c = classer(construire_passages(panel, config), panel, config).set_index("fi")
    assert c["classe"].to_dict() == {"A": "stable", "B": "decrochage", "C": "stable", "D": "sortie"}
    assert c["y"].to_dict() == {"A": 0, "B": 1, "C": 0, "D": 1}


def test_classer_reapparition_donne_une_classe_inconnue(config):
    # X : présent en 2023, absent en 2024, de retour en 2025 -> activité 2024 inconnue.
    panel = pd.DataFrame({"fi": ["X", "X", "R", "R", "R"], "an": [2023, 2025, 2023, 2024, 2025],
                          "fi_ej": ["E1"] * 2 + ["E2"] * 3, "activite": [5000.0, 5000.0, 9000.0, 9000.0, 9000.0]})
    c = classer(construire_passages(panel, config), panel, config)
    x = c[(c.fi == "X") & (c.t == 2023)].iloc[0]
    assert x["classe"] == "inconnue" and pd.isna(x["y"])


# --- restructurations ---------------------------------------------------------------

def identite_vide():
    return pd.DataFrame({"fi": pd.Series(dtype=str), "an": pd.Series(dtype=int)})


def avec_restructurations(panel, config, identite=None):
    classes = classer(construire_passages(panel, config), panel, config)
    return restructurations(classes, panel, identite if identite is not None else identite_vide(),
                            config).set_index("fi")


def test_transfert_entre_deux_sites_du_groupe(config):
    # Le site 1 perd 4 000, le site 2 du même groupe G en gagne 4 000 ; H, stable, fixe la référence à 0.
    panel = pd.DataFrame({
        "fi": ["1", "1", "2", "2", "9", "9"], "an": [2023, 2024] * 3,
        "fi_ej": ["G", "G", "G", "G", "H", "H"],
        "activite": [10_000.0, 6_000.0, 10_000.0, 14_000.0, 100_000.0, 100_000.0]})
    c = avec_restructurations(panel, config)
    assert c.loc["1", "classe"] == "decrochage"
    assert c.loc["1", "compensation"] == pytest.approx(1.0)        # 4 000 retrouvés sur 4 000 perdus
    assert c.loc["1", "restructuration_probable"] == 1
    assert c.loc["2", "restructuration_probable"] == 0              # y = 0


def test_changement_de_finess_dans_le_meme_groupe(config):
    # Le numéro « ancien » disparaît, un « nouveau » numéro du même groupe reprend l'activité.
    panel = pd.DataFrame({"fi": ["ancien", "nouveau", "9", "9"], "an": [2023, 2024, 2023, 2024],
                          "fi_ej": ["G", "G", "H", "H"], "activite": [10_000.0, 10_200.0, 100_000.0, 100_000.0]})
    c = avec_restructurations(panel, config)
    assert c.loc["ancien", "classe"] == "sortie"
    assert c.loc["ancien", "restructuration_probable"] == 1


def test_vrai_declin_sans_compensation(config):
    # Le site 1 perd 4 000, le site 2 du groupe ne gagne rien : pas de restructuration.
    panel = pd.DataFrame({
        "fi": ["1", "1", "2", "2", "9", "9"], "an": [2023, 2024] * 3,
        "fi_ej": ["G", "G", "G", "G", "H", "H"],
        "activite": [10_000.0, 6_000.0, 10_000.0, 10_000.0, 100_000.0, 100_000.0]})
    assert avec_restructurations(panel, config).loc["1", "restructuration_probable"] == 0


def test_grand_groupe_qui_grandit_normalement_ne_compense_pas(config):
    # A perd 1 000 ; B, du même groupe, croît comme la France : ce n'est pas un transfert.
    panel = pd.DataFrame({
        "fi": ["A", "A", "B", "B", "H", "H"], "an": [2023, 2024] * 3,
        "fi_ej": ["G", "G", "G", "G", "K", "K"],
        "activite": [2_000.0, 1_000.0, 100_000.0, 103_000.0, 1_000_000.0, 1_030_000.0]})
    c = avec_restructurations(panel, config)
    assert c.loc["A", "classe"] == "decrochage"
    assert c.loc["A", "compensation"] < 0.5                          # B ne gagne presque rien au-delà de la référence
    assert c.loc["A", "restructuration_probable"] == 0


def test_site_cite_dans_une_fusion_declaree_par_un_autre_groupe(config):
    # X disparaît en 2024 ; Y, d'un autre groupe, déclare en 2024 une fusion avec X.
    panel = pd.DataFrame({"fi": ["X", "Y", "Y"], "an": [2023, 2023, 2024],
                          "fi_ej": ["EX", "EY", "EY"], "activite": [5_000.0, 50_000.0, 50_000.0]})
    identite = pd.DataFrame({"fi": ["Y"], "an": [2024], "fifu1": ["X"]})
    assert citations_fusion_scission(identite) == {("X", 2024)}
    c = avec_restructurations(panel, config, identite)
    assert c.loc["X", "cite_fusion_scission"] and c.loc["X", "restructuration_probable"] == 1


def test_changement_de_groupe(config):
    panel = pd.DataFrame({"fi": ["Z", "Z"], "an": [2023, 2024], "fi_ej": ["E1", "E2"],
                          "activite": [5_000.0, 5_000.0]})
    assert avec_restructurations(panel, config).loc["Z", "changement_de_groupe"] == 1
