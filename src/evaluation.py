"""Évaluation des modèles : scores pli par pli contre le hasard, et journal des expériences.

Règles (docs/decisions.md, « Découpage et évaluation » et « Journal des expériences ») :
  - un modèle est évalué en validation croisée par année, sur l'entraînement seulement ;
    le test n'entre jamais dans le journal (evaluer_par_pli refuse une autre partie) ;
  - trois populations : toutes les lignes, les décrochages contre les stables, les sorties
    contre les stables ; le Brier n'a de sens que pour « toutes » (le modèle prédit un y = 1
    quelconque, pas un décrochage ou une sortie en particulier) ;
  - chaque score est comparé à son niveau du hasard sur le même pli : PR-AUC = part de y = 1
    de l'année validée, ROC-AUC = 0,5, Brier d'une prédiction constante égale à la part de
    y = 1 de l'entraînement du pli ;
  - le journal ne fait qu'ajouter : un identifiant déjà pris est refusé, rien n'est effacé.
"""

import hashlib
import json
import subprocess

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

# Classes gardées dans chaque population (colonne « classe » de la table de modélisation).
POPULATIONS = {
    "toutes": ("stable", "decrochage", "sortie"),
    "decrochages": ("stable", "decrochage"),
    "sorties": ("stable", "sortie"),
}
METRIQUES = ["pr_auc", "roc_auc", "brier"]
FICHIER_JOURNAL = "journal_experiences.csv"
FICHIER_SCORES = "scores_par_pli.csv"
DOSSIER_PARAMETRES = "parametres"


def scores(y, p, p_hasard):
    """PR-AUC, ROC-AUC et Brier des probabilités p, et leurs niveaux du hasard.

    p_hasard : la probabilité constante du hasard (part de y = 1 de l'entraînement du pli).
    """
    y, p = np.asarray(y), np.asarray(p, dtype=float)
    return {"pr_auc": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p),
            "brier": brier_score_loss(y, p),
            "pr_auc_hasard": float(y.mean()), "roc_auc_hasard": 0.5,
            "brier_hasard": brier_score_loss(y, np.full(len(y), p_hasard))}


def evaluer_par_pli(table, plis, predire):
    """Entraîne et évalue un modèle sur chaque pli, pour les trois populations.

    table : lignes d'entraînement (colonnes t, y, classe, partie et variables), dans l'ordre des plis.
    plis : liste de (indices d'entraînement, indices de validation) (src.decoupage.plis_par_annee).
    predire(entrainement, validation) -> (probabilités pour la validation, paramètres appris : dict).
    Renvoie (scores : une ligne par pli et par population, paramètres : une entrée par pli).
    """
    if "partie" in table and set(table["partie"]) != {"entrainement"}:
        raise ValueError("evaluer_par_pli n'utilise que l'entraînement : le test n'entre jamais dans le journal.")
    lignes, parametres = [], []
    for numero, (i_entr, i_val) in enumerate(plis, 1):
        entr, val = table.iloc[i_entr], table.iloc[i_val]
        p, appris = predire(entr, val)
        val = val.assign(p=np.asarray(p, dtype=float))
        parametres.append({"pli": numero, "annee_validee": int(val["t"].iloc[0]), **appris})
        for population, classes in POPULATIONS.items():
            v = val[val["classe"].isin(classes)]
            s = scores(v["y"], v["p"], entr["y"].mean())
            if population != "toutes":
                s["brier"] = s["brier_hasard"] = np.nan
            lignes.append({"pli": numero, "annee_validee": int(val["t"].iloc[0]),
                           "annees_entrainement": int(entr["t"].nunique()), "population": population,
                           "lignes": len(v), "y1": int(v["y"].sum()), **s})
    return pd.DataFrame(lignes), parametres


def resumer(scores_par_pli, annees_min=3):
    """Moyennes des scores de la population « toutes » sur tous les plis, et sur les plis qui ont
    au moins annees_min années d'entraînement (point resté ouvert : les deux sont gardées)."""
    toutes = scores_par_pli[scores_par_pli["population"] == "toutes"]
    assez = toutes[toutes["annees_entrainement"] >= annees_min]
    resume = {}
    for m in METRIQUES:
        resume[f"{m}_{len(toutes)}_plis"] = toutes[m].mean()
        resume[f"{m}_{len(assez)}_plis"] = assez[m].mean()
    return resume


def empreinte(chemin):
    """Empreinte md5 d'un fichier : même empreinte, mêmes données."""
    return hashlib.md5(chemin.read_bytes()).hexdigest()


def version_du_code(racine):
    """(commit court, code modifié non commité ?) ; (« inconnu », True) si git ne répond pas.

    Le code, c'est src/, scripts/ et config.yaml : un fichier modifié ou jamais commité y compte.
    """
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=racine, capture_output=True,
                                text=True, check=True).stdout.strip()
        etat = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "src", "scripts",
                               "config.yaml"], cwd=racine, capture_output=True, text=True, check=True).stdout.strip()
        return commit, bool(etat)
    except (OSError, subprocess.CalledProcessError):
        return "inconnu", True


def ajouter_au_journal(dossier, experience, scores_par_pli, parametres):
    """Ajoute une expérience au journal, sans jamais rien effacer.

    dossier : resultats/05_modeles ; experience : une ligne du journal (dict, avec la clé « id ») ;
    scores_par_pli : sortie d'evaluer_par_pli ; parametres : paramètres appris (liste), écrits
    dans parametres/<id>.json. Refuse un identifiant déjà présent dans le journal ou les paramètres.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    journal = dossier / FICHIER_JOURNAL
    deja = pd.read_csv(journal, dtype=str)["id"].tolist() if journal.exists() else []
    fichier_parametres = dossier / DOSSIER_PARAMETRES / f"{experience['id']}.json"
    if experience["id"] in deja or fichier_parametres.exists():
        raise ValueError(f"L'expérience {experience['id']} est déjà dans le journal : on n'efface ni ne remplace rien.")
    pd.DataFrame([experience]).to_csv(journal, mode="a", header=not journal.exists(), index=False)
    lignes = scores_par_pli.assign(id=experience["id"])[["id"] + list(scores_par_pli.columns)]
    fichier_scores = dossier / FICHIER_SCORES
    lignes.to_csv(fichier_scores, mode="a", header=not fichier_scores.exists(), index=False)
    fichier_parametres.parent.mkdir(exist_ok=True)
    fichier_parametres.write_text(json.dumps(parametres, ensure_ascii=False, indent=1), encoding="utf-8")
