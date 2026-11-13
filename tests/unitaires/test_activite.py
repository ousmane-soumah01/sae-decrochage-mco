"""Tests unitaires de src/activite.py, sur des exemples calculés à la main."""

import pandas as pd
import pytest

from src.activite import calculer_activite, est_eligible
from src.config import charger_config

pytestmark = pytest.mark.unitaire


@pytest.fixture
def config():
    return charger_config()


# Cinq établissements fictifs : journées, venues, séjours de 0 jour
EXEMPLE = pd.DataFrame({
    "jou_mco":   [100_000, 12_000, 6_000, 8_000, 200],
    "sejhp_mco": [40_000, 20_000, 1_000, 2_000, 200],
    "sej0_mco":  [8_000, 1_000, 400, 600, 50],
}, index=["A", "B", "C", "D", "E"], dtype="float64")


def test_calculer_activite_retrouve_le_calcul_a_la_main(config):
    # A : 100 000 + 0,5 x (40 000 + 8 000) = 124 000 ; ... ; E : 200 + 0,5 x 250 = 325
    assert calculer_activite(EXEMPLE, config).tolist() == [124_000, 22_500, 6_700, 9_300, 325]


def test_calculer_activite_composante_vide_compte_zero(config):
    t = pd.DataFrame({"jou_mco": [1000.0], "sejhp_mco": [None], "sej0_mco": [200.0]})
    assert calculer_activite(t, config).tolist() == [1100.0]


def test_calculer_activite_tout_vide_est_inconnu(config):
    t = pd.DataFrame({"jou_mco": [None], "sejhp_mco": [None], "sej0_mco": [None]}, dtype="float64")
    assert pd.isna(calculer_activite(t, config)[0])


def test_calculer_activite_suit_le_poids_de_config(config):
    config["activite"]["poids_partielle"] = 1.0           # variante de robustesse
    t = pd.DataFrame({"jou_mco": [100.0], "sejhp_mco": [50.0], "sej0_mco": [0.0]})
    assert calculer_activite(t, config).tolist() == [150.0]

def test_est_eligible_seuil_1000(config):
    activite = pd.Series([124_000, 1000, 999.5, 325, None])
    assert est_eligible(activite, config).tolist() == [True, True, False, False, False]
