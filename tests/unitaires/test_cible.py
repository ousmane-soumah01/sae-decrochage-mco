"""Tests unitaires de src/cible.py, sur l'exemple des cinq établissements calculé à la main.

Passage 2023 -> 2024 (activités en journées-équivalentes, seuil 1 000) :
    A  124 000 -> 129 500     B  22 500 -> 16 900     C  6 700 -> 6 140
    D    9 300 -> absent      E     325 -> 325 (sous le seuil)
    référence = 152 540 / 153 200 - 1 = -0,4308 %
"""

import pandas as pd
import pytest

from src.cible import construire_passages, ecarts_et_decrochages, reference_ponderee
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
