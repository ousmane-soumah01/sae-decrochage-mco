"""Test d'intégration : la chaîne de préparation, des CSV extraits jusqu'au panel.

On fabrique de petits fichiers SAE fictifs (3 établissements, 2 années), en-têtes en
majuscules et encodage Windows-1252 comme les vrais, on lance construire_panel(), et on
vérifie le résultat de bout en bout : empilement, conversions, décisions 1 à 5.
"""

import pandas as pd
import pytest

from src.config import charger_config
from src.variables import QUANTITES_MCO, construire_panel

pytestmark = pytest.mark.integration

A, B, C = "010000024", "310000001", "2A0000017"     # C : un établissement corse (2A)


def ecrire(dossier, annee, table, entete, lignes):
    sous_dossier = dossier / str(annee)
    sous_dossier.mkdir(exist_ok=True)
    texte = ";".join(entete) + "\n" + "".join(";".join(map(str, l)) + "\n" for l in lignes)
    (sous_dossier / f"{table}_{annee}r.csv").write_bytes(texte.encode("cp1252"))


def ligne_mco(fi, annee, **valeurs):
    """Ligne MCO : toutes les quantités vides sauf celles données."""
    return [fi, annee] + [valeurs.get(c, "") for c in QUANTITES_MCO]


@pytest.fixture
def extraites(tmp_path):
    entete_mco = ["FI", "AN"] + [c.upper() for c in QUANTITES_MCO]
    for an in (2016, 2017):
        ecrire(tmp_path, an, "ID", ["FI", "AN", "RS", "FI_EJ", "STJR", "CATR", "DEP", "REG"], [
            [A, an, "CH ÉTOILE", "010000001", 1, "PUB2", "01", "84"],
            [B, an, "CLINIQUE", "310000000", 2, "PLU4", "31", "76"],
            [C, an, "CH AJACCIO", "2A0000001", 1, "PUB2", "2A", "94"],
        ])
        ecrire(tmp_path, an, "MCO", entete_mco, [
            # A : lits renseignés, pas de place (places vides, aucune venue) -> places mises à 0
            ligne_mco(A, an, lit_mco=10, jli_mco=3650, jou_mco=3000, sejhc_mco=500,
                      sej0_mco=50, sejhp_mco=0, sea_mco=0),
            # B : lits vides MAIS des journées -> lits laissés vides, incohérence repérée
            ligne_mco(B, an, jou_mco=800, sejhc_mco=100, sej0_mco=10,
                      pla_mco=5, sejhp_mco=1200, sea_mco=0),
            # C : uniquement de l'ambulatoire, lits vides et aucune journée -> lits mis à 0
            ligne_mco(C, an, sejhc_mco=0, sej0_mco=0, jou_mco=0, pla_mco=3, sejhp_mco=700),
        ])
        ecrire(tmp_path, an, "MCOPED", ["FI", "AN", "SPED"], [[A, an, 1]])
        ecrire(tmp_path, an, "MCOGER", ["FI", "AN", "UGER"], [[A, an, 1], [B, an, 0]])
        ecrire(tmp_path, an, "MCOAVC", ["FI", "AN", "UNV"], [[A, an, 1]])
        ecrire(tmp_path, an, "URGENCES", ["FI", "AN", "AUTSU"], [[A, an, 1]])
        ecrire(tmp_path, an, "SSR", ["FI", "AN", "GDE", "SEJHC"],
               [[B, an, "SSR_TOT", 40], [B, an, "SSR_A50", 40], [C, an, "SSR_TOT", 0]])
    return tmp_path


@pytest.fixture
def resultat(extraites):
    return construire_panel(charger_config(), extraites, [2016, 2017])


def ligne(panel, fi, an=2016):
    return panel[(panel.fi == fi) & (panel.an == an)].iloc[0]


def test_panel_une_ligne_par_etablissement_et_par_annee(resultat):
    panel, _ = resultat
    assert len(panel) == 6
    assert not panel.duplicated(["fi", "an"]).any()
    assert panel["an"].value_counts().to_dict() == {2016: 3, 2017: 3}


def test_panel_garde_le_zero_de_tete_et_la_corse(resultat):
    panel, _ = resultat
    assert set(panel["fi"]) == {A, B, C}


def test_panel_quantites_numeriques_et_annee_entiere(resultat):
    panel, _ = resultat
    assert panel["jou_mco"].dtype == "float64"
    assert panel["an"].dtype.kind == "i"
    assert ligne(panel, A)["lit_mco"] == 10.0


def test_panel_regle_des_capacites(resultat):
    panel, _ = resultat
    assert ligne(panel, A)["pla_mco"] == 0.0           # vide, aucune venue -> 0
    assert ligne(panel, C)["lit_mco"] == 0.0           # vide, aucune journée -> 0
    assert pd.isna(ligne(panel, B)["lit_mco"])         # vide avec journées -> reste vide
    assert ligne(panel, B)["inc_lits_vides_avec_journees"] == 1
    assert ligne(panel, A)["inc_lits_vides_avec_journees"] == 0


def test_panel_identite_et_region_actuelle(resultat):
    panel, _ = resultat
    a = ligne(panel, A)
    assert (a["stjr"], a["catr"], a["dep"]) == ("1", "PUB2", "01")
    assert a["rs"] == "CH ÉTOILE"                       # accent lu en Windows-1252
    assert {fi: ligne(panel, fi)["reg_actuelle"] for fi in (A, B, C)} == {A: "84", B: "76", C: "94"}
    assert "reg" not in panel.columns                   # la région d'origine n'entre pas


def test_panel_indicateurs_des_autres_tables(resultat):
    panel, _ = resultat
    colonnes = ["a_pediatrie", "a_geriatrie", "a_unv", "a_urgences", "a_smr"]
    assert ligne(panel, A)[colonnes].tolist() == [1, 1, 1, 1, 0]
    assert ligne(panel, B)[colonnes].tolist() == [0, 0, 0, 0, 1]   # uger = 0 ; SSR_TOT avec séjours
    assert ligne(panel, C)[colonnes].tolist() == [0, 0, 0, 0, 0]   # SSR_TOT sans séjour


def test_controles_documentent_chaque_etape(resultat):
    _, controles = resultat
    valeurs = {(c["etape"], c["mesure"]): c["valeur"] for c in controles}
    assert valeurs[("jointures", "lignes MCO absentes de ID")] == 0
    assert valeurs[("panel", "lignes")] == 6
    assert valeurs[("capacites", "lit_mco vide laissé vide (jou_mco > 0)")] == 2   # B, 2 années
