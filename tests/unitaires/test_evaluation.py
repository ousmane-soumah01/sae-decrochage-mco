"""Tests unitaires de src/evaluation.py, sur de petits exemples calculés à la main."""

import json

import numpy as np
import pandas as pd
import pytest

from src.evaluation import ajouter_au_journal, evaluer_par_pli, resumer, scores

pytestmark = pytest.mark.unitaire


def test_scores_calcules_a_la_main():
    # y = 0, 0, 1, 1 ; p = 0,1 ; 0,4 ; 0,35 ; 0,8
    # ROC : 3 paires bien ordonnées sur 4 = 0,75.
    # PR-AUC : rangé par p décroissant -> 1 (précision 1, rappel 0,5), 0, 1 (précision 2/3, rappel 1) :
    #   0,5 x 1 + 0,5 x 2/3 = 0,8333.
    # Brier : (0,01 + 0,16 + 0,4225 + 0,04) / 4 = 0,158125 ; hasard à 0,5 : 0,25.
    s = scores([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], p_hasard=0.5)
    assert s["roc_auc"] == pytest.approx(0.75)
    assert s["pr_auc"] == pytest.approx(5 / 6)
    assert s["brier"] == pytest.approx(0.158125)
    assert s["pr_auc_hasard"] == 0.5 and s["roc_auc_hasard"] == 0.5 and s["brier_hasard"] == pytest.approx(0.25)


def test_une_prediction_constante_vaut_le_hasard():
    y = [0, 0, 0, 1, 0, 1, 0, 0]
    s = scores(y, np.full(8, 0.3), p_hasard=0.3)
    assert s["pr_auc"] == pytest.approx(s["pr_auc_hasard"]) == pytest.approx(0.25)
    assert s["roc_auc"] == 0.5 and s["brier"] == pytest.approx(s["brier_hasard"])


def table_trois_annees():
    """2013, 2014, 2015 : 4 lignes par année, une sortie et un décrochage chaque année."""
    classe = ["stable", "stable", "decrochage", "sortie"] * 3
    return pd.DataFrame({"t": np.repeat([2013, 2014, 2015], 4), "classe": classe,
                         "y": [0 if c == "stable" else 1 for c in classe], "partie": "entrainement",
                         "x": [5.0, 4.0, 1.0, 2.0] * 3})


def plis_trois_annees():
    return [(np.arange(4), np.arange(4, 8)), (np.arange(8), np.arange(8, 12))]


def predire_petit_x(entr, val):
    """Score = opposé de x (plus petit, plus risqué), ramené entre 0 et 1 ; un paramètre « appris »."""
    return 1 / (1 + val["x"]), {"moyenne_x": float(entr["x"].mean())}


def test_evaluer_par_pli_trois_populations_et_parametres():
    s, parametres = evaluer_par_pli(table_trois_annees(), plis_trois_annees(), predire_petit_x)
    assert len(s) == 2 * 3
    assert s.set_index(["pli", "population"]).loc[(1, "decrochages"), "lignes"] == 3     # sans la sortie
    assert s.set_index(["pli", "population"]).loc[(1, "sorties"), "y1"] == 1
    # Brier seulement pour « toutes »
    assert s.loc[s.population == "toutes", "brier"].notna().all()
    assert s.loc[s.population != "toutes", "brier"].isna().all()
    # x sépare parfaitement : décrochage (x = 1) et sortie (x = 2) avant les stables (4 et 5)
    assert (s["roc_auc"] == 1.0).all()
    assert parametres == [{"pli": 1, "annee_validee": 2014, "moyenne_x": 3.0},
                          {"pli": 2, "annee_validee": 2015, "moyenne_x": 3.0}]
    assert s["annees_entrainement"].tolist() == [1, 1, 1, 2, 2, 2]


def test_evaluer_par_pli_refuse_le_test():
    table = table_trois_annees()
    table.loc[11, "partie"] = "test"
    with pytest.raises(ValueError, match="test"):
        evaluer_par_pli(table, plis_trois_annees(), predire_petit_x)


def test_resumer_sur_tous_les_plis_et_sur_ceux_d_au_moins_n_annees():
    s = pd.DataFrame({"population": "toutes", "annees_entrainement": [1, 2, 3, 4],
                      "pr_auc": [0.1, 0.2, 0.3, 0.5], "roc_auc": 0.6, "brier": 0.05})
    r = resumer(s, annees_min=3)
    assert r["pr_auc_4_plis"] == pytest.approx(0.275) and r["pr_auc_2_plis"] == pytest.approx(0.4)


def test_le_journal_ajoute_et_refuse_un_identifiant_deja_pris(tmp_path):
    s, parametres = evaluer_par_pli(table_trois_annees(), plis_trois_annees(), predire_petit_x)
    ajouter_au_journal(tmp_path, {"id": "E001", "modele": "essai"}, s, parametres)
    ajouter_au_journal(tmp_path, {"id": "E002", "modele": "essai"}, s, parametres)
    assert pd.read_csv(tmp_path / "journal_experiences.csv")["id"].tolist() == ["E001", "E002"]
    assert len(pd.read_csv(tmp_path / "scores_par_pli.csv")) == 2 * len(s)
    assert json.loads((tmp_path / "parametres" / "E002.json").read_text(encoding="utf-8"))[0]["moyenne_x"] == 3.0
    with pytest.raises(ValueError, match="E001"):
        ajouter_au_journal(tmp_path, {"id": "E001", "modele": "autre"}, s, parametres)
    assert len(pd.read_csv(tmp_path / "journal_experiences.csv")) == 2       # rien n'a été effacé
