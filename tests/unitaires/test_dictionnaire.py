"""Tests unitaires de src/dictionnaire.py : chaque colonne du panel est documentée, une fois."""

import pandas as pd
import pytest

from src.dictionnaire import DICTIONNAIRE, GROUPES, colonnes_sans_definition, table_dictionnaire, vers_markdown
from src.variables import CLE, INDICATEURS, QUANTITES_MCO

pytestmark = pytest.mark.unitaire

COLONNES_PANEL = (CLE + QUANTITES_MCO
                  + ["inc_lits_vides_avec_journees", "inc_places_vides_avec_venues", "inc_sej0_superieur_a_sejhc",
                     "inc_jou_trop_bas", "inc_lits_zero_avec_journees"]
                  + ["rs", "fi_ej", "stjr", "catr", "dep", "reg_actuelle"] + list(INDICATEURS))


def test_chaque_colonne_du_panel_a_une_definition_et_rien_de_plus():
    assert set(DICTIONNAIRE) == set(COLONNES_PANEL)
    assert len(DICTIONNAIRE) == 47


def test_aucun_champ_vide_et_groupes_connus():
    for colonne, e in DICTIONNAIRE.items():
        assert e["groupe"] in GROUPES, colonne
        for champ in ("definition", "unite", "source", "regle"):
            assert e[champ].strip(), f"{colonne} : {champ} vide"


def test_libelles_drees_sensibles():
    assert "2 : Privé lucratif, 3 : Privé non lucratif" in DICTIONNAIRE["stjr"]["definition"]
    assert DICTIONNAIRE["lit_mco"]["definition"] == "« Lits de MCO installés en hospitalisation complète au 31/12 »"
    assert "décision 1" in DICTIONNAIRE["pla_med"]["regle"]


def panel_minimal():
    p = pd.DataFrame({c: [1.0, 2.0, 3.0, 4.0] for c in COLONNES_PANEL})
    p.loc[0, "lit_mco"] = None                       # 1 case vide sur 4
    return p


def test_table_dictionnaire_mesure_les_cases_vides():
    d = table_dictionnaire(panel_minimal()).set_index("colonne")
    assert list(d.index) == COLONNES_PANEL
    assert d.loc["lit_mco", "vides_pct"] == 25.0
    assert d.loc["jou_mco", "vides_pct"] == 0.0


def test_colonnes_sans_definition():
    p = panel_minimal().assign(nouvelle=0).drop(columns="dep")
    assert colonnes_sans_definition(p) == (["nouvelle"], ["dep"])


def test_vers_markdown_une_ligne_par_colonne():
    texte = vers_markdown(table_dictionnaire(panel_minimal()), 4)
    assert len([l for l in texte.splitlines() if l.startswith("| `")]) == 47
    assert "## Quantité MCO" in texte
