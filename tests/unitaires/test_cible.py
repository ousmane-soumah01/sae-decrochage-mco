"""Tests unitaires de src/cible.py, sur l'exemple des cinq établissements calculé à la main.

Passage 2023 -> 2024 (activités en journées-équivalentes, seuil 1 000) :
    A  124 000 -> 129 500     B  22 500 -> 16 900     C  6 700 -> 6 140
    D    9 300 -> absent      E     325 -> 325 (sous le seuil)
    référence = 152 540 / 153 200 - 1 = -0,4308 %
"""

import numpy as np
import pandas as pd
import pytest

from src.cible import (
    citations_fusion_scission,
    classer,
    reprises_de_capacites,
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


# --- reprise des capacités par un autre site --------------------------------------------

def panel_reprise(lignes_en_plus=()):
    """A (entité EA, département 01) : 100 lits en 2023, absent en 2024. N (entité EN, 01), nouveau en
    2024 : 98 lits, 9 000 journées. H : grand site stable qui fixe la référence à 0."""
    lignes = [("A", 2023, "EA", "01", 10_000.0, 100.0), ("N", 2024, "EN", "01", 9_000.0, 98.0),
              ("H", 2023, "EH", "02", 100_000.0, 400.0), ("H", 2024, "EH", "02", 100_000.0, 400.0),
              *lignes_en_plus]
    p = pd.DataFrame(lignes, columns=["fi", "an", "fi_ej", "dep", "activite", "lit_mco"])
    p["pla_mco"] = 0.0
    return p


def test_reprise_par_un_nouveau_site_d_une_autre_entite(config):
    # 100 lits perdus, 98 repris (à 10 % près), même département, 9 000 journées sur 10 000 reprises.
    c = avec_restructurations(panel_reprise(), config)
    assert c.loc["A", "classe"] == "sortie"
    assert c.loc["A", "compensation"] == 0 or pd.isna(c.loc["A", "compensation"])   # A seul dans son entité
    assert c.loc["A", "reprise_capacites"] == 1 and c.loc["A", "reprise_meme_ej"] == 0
    assert c.loc["A", "restructuration_probable"] == 1


def test_reprise_dans_la_meme_entite(config):
    p = panel_reprise()
    p.loc[p.fi == "N", "fi_ej"] = "EA"
    assert avec_restructurations(p, config).loc["A", "reprise_meme_ej"] == 1


@pytest.mark.parametrize("modifier, raison", [
    (lambda p: p.assign(dep=p.dep.where(p.fi != "N", "03")), "autre département"),
    (lambda p: p.assign(lit_mco=p.lit_mco.where(p.fi != "N", 70.0)), "gain trop différent de la perte"),
    (lambda p: p.assign(activite=p.activite.where(p.fi != "N", 4_000.0)), "activité pas reprise"),
    (lambda p: p.assign(lit_mco=p.lit_mco.where(p.fi != "A", 25.0)).assign(
        lit_mco=lambda q: q.lit_mco.where(q.fi != "N", 25.0)), "perte sous 30 lits et places"),
])
def test_pas_de_reprise(config, modifier, raison):
    c = avec_restructurations(modifier(panel_reprise()), config)
    assert c.loc["A", "reprise_capacites"] == 0, raison
    assert c.loc["A", "restructuration_probable"] == 0, raison


def test_pas_de_reprise_quand_l_ancien_site_garde_des_lits(config):
    # A passe de 100 à 40 lits (et de 10 000 à 3 000 journées) ; N gagne 60 lits : A est toujours là, il décroche.
    p = panel_reprise([("A", 2024, "EA", "01", 3_000.0, 40.0)])
    p.loc[p.fi == "N", "lit_mco"] = 60.0
    c = avec_restructurations(p, config)
    assert c.loc["A", "classe"] == "decrochage"
    assert c.loc["A", "reprise_capacites"] == 0 and c.loc["A", "restructuration_probable"] == 0


def test_pas_de_reprise_quand_trop_de_candidats(config):
    # 7 sites gagnent aussi 100 lits ailleurs en France : 8 candidats > 6, la correspondance peut être le hasard.
    autres = [(f"Z{i}", 2024, f"EZ{i}", "50", 9_000.0, 100.0) for i in range(7)]
    assert avec_restructurations(panel_reprise(autres), config).loc["A", "reprise_capacites"] == 0


def test_reprise_desactivee_ou_sans_capacites(config):
    config["cible"]["reprise"]["active"] = False
    assert avec_restructurations(panel_reprise(), config).loc["A", "reprise_capacites"] == 0
    config["cible"]["reprise"]["active"] = True
    sans_lits = panel_reprise().drop(columns=["lit_mco", "pla_mco"])
    classes = classer(construire_passages(sans_lits, config), sans_lits, config)
    assert reprises_de_capacites(classes, sans_lits, config).empty


# --- fermeture en cours d'année ---------------------------------------------------------

def panel_fermeture(activite_2024=4_000.0, lits_2024=0.0, actif_2025=False):
    """F : 50 lits et 10 000 journées en 2023 ; en 2024, activite_2024 et lits_2024 ; en 2025, actif
    ou absent. H : grand site stable de 2023 à 2025, qui fixe la référence à 0."""
    lignes = [("F", 2023, 10_000.0, 50.0), ("F", 2024, activite_2024, lits_2024),
              ("H", 2023, 100_000.0, 400.0), ("H", 2024, 100_000.0, 400.0), ("H", 2025, 100_000.0, 400.0)]
    if actif_2025:
        lignes.append(("F", 2025, 3_000.0, 10.0))
    p = pd.DataFrame(lignes, columns=["fi", "an", "activite", "lit_mco"])
    p["pla_mco"], p["fi_ej"] = 0.0, "E" + p["fi"]
    return p


def classe_de_f_en_2023(panel, config):
    c = classer(construire_passages(panel, config), panel, config)
    return c[(c.fi == "F") & (c.t == 2023)].iloc[0]


def test_fermeture_en_cours_d_annee_devient_une_sortie(config):
    # 10 000 -> 4 000 journées, 0 lit au 31/12/2024, plus rien en 2025 : sortie, y = 1.
    f = classe_de_f_en_2023(panel_fermeture(), config)
    assert f["decrochage"] and f["fermeture_en_cours"] == 1
    assert f["classe"] == "sortie" and f["y"] == 1


def test_pas_de_fermeture_si_le_site_est_encore_actif_ensuite(config):
    f = classe_de_f_en_2023(panel_fermeture(actif_2025=True), config)
    assert f["fermeture_en_cours"] == 0 and f["classe"] == "decrochage"


def test_pas_de_fermeture_si_le_site_garde_des_lits(config):
    f = classe_de_f_en_2023(panel_fermeture(lits_2024=12.0), config)
    assert f["fermeture_en_cours"] == 0 and f["classe"] == "decrochage"


def test_pas_de_fermeture_quand_t1_est_la_derniere_annee(config):
    # Sans 2025 dans le panel, on ne sait pas si F reprend : il reste un décrochage.
    panel = panel_fermeture()
    panel = panel[panel.an < 2025]
    f = classe_de_f_en_2023(panel, config)
    assert f["fermeture_en_cours"] == 0 and f["classe"] == "decrochage"


def test_un_stable_qui_ferme_en_fin_d_annee_reste_stable(config):
    # Activité presque inchangée en 2024, puis fermeture : pas de baisse en 2023 -> 2024, y = 0.
    f = classe_de_f_en_2023(panel_fermeture(activite_2024=9_800.0), config)
    assert f["fermeture_en_cours"] == 1 and f["classe"] == "stable" and f["y"] == 0


def test_fermeture_desactivee(config):
    config["cible"]["fermeture_en_cours_est_une_sortie"] = False
    assert classe_de_f_en_2023(panel_fermeture(), config)["classe"] == "decrochage"


# --- champ : capacité MCO en t ------------------------------------------------------------

def test_sans_capacite_mco_lit_seulement_l_annee_t(config):
    # F 2024 : 0 lit, 4 000 journées (fermé pendant 2024). Le passage 2024 -> 2025 est sans capacité
    # en t ; le passage 2023 -> 2024 (50 lits en 2023) ne l'est pas, et garde y = 1.
    panel = panel_fermeture()
    panel = pd.concat([panel, pd.DataFrame({"fi": ["H"], "an": [2026], "activite": [100_000.0], "lit_mco": [400.0],
                                            "pla_mco": [0.0], "fi_ej": ["EH"]})], ignore_index=True)
    c = classer(construire_passages(panel, config), panel, config).set_index(["fi", "t"])
    assert c.loc[("F", 2023), "sans_capacite_mco_t"] == 0 and c.loc[("F", 2023), "y"] == 1
    assert c.loc[("F", 2024), "sans_capacite_mco_t"] == 1


def test_sans_capacite_mco_compte_les_cases_vides_comme_0(config):
    panel = panel_fermeture()
    panel.loc[(panel.fi == "F") & (panel.an == 2024), "lit_mco"] = np.nan
    c = classer(construire_passages(panel, config), panel, config).set_index(["fi", "t"])
    assert c.loc[("F", 2024), "sans_capacite_mco_t"] == 1


def test_sans_capacite_mco_faux_sans_colonnes_de_capacite(config):
    panel = panel_exemple()
    c = classer(construire_passages(panel, config), panel, config)
    assert (c["sans_capacite_mco_t"] == 0).all()
