"""Tests unitaires de src/nettoyage.py : chaque fonction est testée seule."""

import pandas as pd
import pytest

from src.nettoyage import (
    capacite_vide_a_zero,
    convertir_quantites,
    correspondance_region,
    indicateurs_incoherences,
    joindre_gauche,
    valeurs_non_numeriques,
    vers_nombre,
)

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


# --- convertir_quantites ------------------------------------------------------

def test_convertir_quantites_ne_touche_que_les_colonnes_demandees():
    t = pd.DataFrame({"dep": ["01", "2A"], "lit_mco": ["10", "5,5"]})
    r = convertir_quantites(t, ["lit_mco", "absente"])
    assert r["lit_mco"].tolist() == [10.0, 5.5]
    assert r["dep"].tolist() == ["01", "2A"]      # code laissé en texte
    assert t["lit_mco"].tolist() == ["10", "5,5"]  # la table d'origine n'est pas modifiée


# --- capacite_vide_a_zero -----------------------------------------------------

def test_capacite_vide_a_zero_suit_la_decision_1():
    t = pd.DataFrame({"lit_mco": [None, None, 3.0], "jou_mco": [0.0, 50.0, 40.0]})
    r, a_zero, laissees_vides = capacite_vide_a_zero(t, "lit_mco", "jou_mco")
    assert r.loc[0, "lit_mco"] == 0.0             # vide + aucune journée -> 0
    assert pd.isna(r.loc[1, "lit_mco"])           # vide + journées -> reste vide
    assert r.loc[2, "lit_mco"] == 3.0             # renseigné -> inchangé
    assert (a_zero, laissees_vides) == (1, 1)


def test_capacite_vide_a_zero_activite_vide_compte_comme_nulle():
    t = pd.DataFrame({"pla_mco": [None], "sejhp_mco": [None]})
    r, a_zero, _ = capacite_vide_a_zero(t, "pla_mco", "sejhp_mco")
    assert r.loc[0, "pla_mco"] == 0.0 and a_zero == 1


# --- indicateurs_incoherences -------------------------------------------------

def test_indicateurs_incoherences_chaque_ligne_declenche_un_seul_indicateur():
    t = pd.DataFrame({
        #            correcte  sej0>hc  jou trop bas  0 lit avec journées
        "sejhc_mco": [10.0,     2.0,     10.0,         5.0],
        "sej0_mco":  [2.0,      5.0,     0.0,          0.0],
        "jou_mco":   [30.0,     0.0,     5.0,          20.0],
        "lit_mco":   [5.0,      1.0,     5.0,          0.0],
    })
    i = indicateurs_incoherences(t)
    assert i["inc_sej0_superieur_a_sejhc"].tolist() == [0, 1, 0, 0]
    assert i["inc_jou_trop_bas"].tolist() == [0, 0, 1, 0]
    assert i["inc_lits_zero_avec_journees"].tolist() == [0, 0, 0, 1]


# --- correspondance_region ----------------------------------------------------

def test_correspondance_region():
    t = pd.DataFrame({"dep": ["31", "34", "31", "2A"], "reg": ["76", "76", "76", "94"]})
    assert correspondance_region(t) == {"31": "76", "34": "76", "2A": "94"}


def test_correspondance_region_refuse_un_departement_ambigu():
    t = pd.DataFrame({"dep": ["31", "31"], "reg": ["76", "73"]})
    with pytest.raises(ValueError, match="plusieurs régions"):
        correspondance_region(t)


# --- joindre_gauche -----------------------------------------------------------

def test_joindre_gauche_garde_toutes_les_lignes_et_compte_les_absents():
    gauche = pd.DataFrame({"fi": ["1", "2", "3"], "an": [2020] * 3})
    droite = pd.DataFrame({"fi": ["1", "2"], "an": [2020] * 2, "stjr": ["1", "2"]})
    r, absents = joindre_gauche(gauche, droite, ["fi", "an"])
    assert len(r) == 3 and absents == 1
    assert r["stjr"].tolist()[:2] == ["1", "2"] and pd.isna(r.loc[2, "stjr"])


def test_joindre_gauche_refuse_une_cle_en_double_a_droite():
    gauche = pd.DataFrame({"fi": ["1"], "an": [2020]})
    droite = pd.DataFrame({"fi": ["1", "1"], "an": [2020, 2020], "x": ["a", "b"]})
    with pytest.raises(ValueError, match="pas unique"):
        joindre_gauche(gauche, droite, ["fi", "an"])
