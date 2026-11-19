"""Tests unitaires de src/decoupage.py, sur de petits exemples écrits à la main."""

import numpy as np
import pandas as pd
import pytest

from src.config import charger_config
from src.decoupage import lignes_evaluees, plis_par_annee, separer_test

pytestmark = pytest.mark.unitaire


@pytest.fixture
def config():
    return charger_config()


def classes_exemple():
    # a : stable ; b : décrochage ; c : inconnue ; d : sortie restructurée
    return pd.DataFrame({"fi": ["a", "b", "c", "d"], "t": [2013, 2013, 2014, 2014],
                         "y": [0, 1, np.nan, 1], "restructuration_probable": [0, 0, 0, 1]})


def test_lignes_evaluees_retire_inconnues_et_restructurations(config):
    assert list(lignes_evaluees(classes_exemple(), config)["fi"]) == ["a", "b"]


def test_lignes_evaluees_garde_restructurations_si_demande(config):
    config["cible"]["retirer_restructurations"] = False
    assert list(lignes_evaluees(classes_exemple(), config)["fi"]) == ["a", "b", "d"]


def lignes_annees():
    # 2 lignes par année t, 2019 et 2020 comprises, dans le désordre
    t = [2022, 2013, 2019, 2014, 2020, 2021, 2015, 2013, 2014, 2015, 2019, 2020, 2021, 2022]
    return pd.DataFrame({"t": t, "y": 0})


def test_separer_test():
    entrainement, test, exclues = separer_test(lignes_annees(), [2022], [2019, 2020])
    assert sorted(set(entrainement["t"])) == [2013, 2014, 2015, 2021]
    assert set(test["t"]) == {2022} and set(exclues["t"]) == {2019, 2020}
    assert len(entrainement) + len(test) + len(exclues) == len(lignes_annees())


def test_separer_test_refuse_une_annee_des_deux_cotes():
    with pytest.raises(ValueError, match="2020"):
        separer_test(lignes_annees(), [2020], [2019, 2020])


def test_plis_par_annee_fenetre_croissante():
    entrainement, _, _ = separer_test(lignes_annees(), [2022], [2019, 2020])
    annees = entrainement["t"].to_numpy()
    plis = plis_par_annee(annees)
    assert [sorted(set(annees[te])) for _, te in plis] == [[2014], [2015], [2021]]
    assert [sorted(set(annees[tr])) for tr, _ in plis] == [[2013], [2013, 2014], [2013, 2014, 2015]]
    for tr, te in plis:
        assert annees[tr].max() < annees[te].min()        # jamais l'avenir, jamais la même année
        assert not set(tr) & set(te)


def test_plis_par_annee_minimum_d_annees():
    annees = np.array([2013, 2014, 2015, 2016, 2017, 2013, 2016])
    plis = plis_par_annee(annees, annees_min_entrainement=3)
    assert [int(annees[te][0]) for _, te in plis] == [2016, 2017]
    assert sorted(plis[0][1]) == [3, 6]                  # les deux lignes de 2016, où qu'elles soient


def test_plis_par_annee_refuse_zero():
    with pytest.raises(ValueError):
        plis_par_annee([2013, 2014], annees_min_entrainement=0)
