"""Tests unitaires de src/nettoyage.py : chaque fonction est testée seule."""

import pandas as pd
import pytest

from src.nettoyage import valeurs_non_numeriques, vers_nombre

pytestmark = pytest.mark.unitaire


# --- vers_nombre --------------------------------------------------------------

def test_vers_nombre_entiers_et_decimales():
    s = pd.Series(["12", "12,5", "12.5", "0"], dtype="object")
    assert vers_nombre(s).tolist() == [12.0, 12.5, 12.5, 0.0]


def test_vers_nombre_retire_les_espaces():
    assert vers_nombre(pd.Series(["1 234", " 7 "])).tolist() == [1234.0, 7.0]


def test_vers_nombre_case_vide_reste_manquante():
    resultat = vers_nombre(pd.Series(["5", None]))
    assert resultat[0] == 5.0 and pd.isna(resultat[1])


def test_vers_nombre_texte_devient_manquant():
    assert pd.isna(vers_nombre(pd.Series(["abc"]))[0])


def test_vers_nombre_renvoie_des_flottants():
    assert vers_nombre(pd.Series(["1", "2"])).dtype == "float64"


# --- valeurs_non_numeriques ---------------------------------------------------

def test_valeurs_non_numeriques_liste_les_echecs_avec_leur_nombre():
    s = pd.Series(["1", "abc", None, "abc", "2,5", "x"])
    assert valeurs_non_numeriques(s).to_dict() == {"abc": 2, "x": 1}


def test_valeurs_non_numeriques_vide_si_tout_est_numerique():
    assert valeurs_non_numeriques(pd.Series(["1", "2,5", None])).empty
