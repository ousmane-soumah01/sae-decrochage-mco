"""Étape 08 : les deux références à battre, E001 le hasard et E002 la règle naïve.

Lancement, depuis la racine du dépôt (après scripts/05_table_modelisation.py) :
    python scripts/08_references.py

Validation croisée par année, sur l'entraînement seulement (src.evaluation) :
  - E001, hasard : probabilité constante égale à la part de y = 1 de l'entraînement du pli ;
  - E002, règle naïve : « plus l'établissement est petit, plus il est à risque » ; recette fixée
    avant tout modèle : régression logistique sur log(1 + activité) seule, apprise sur chaque pli
    (le classement est celui de l'opposé de l'activité ; la logistique donne des probabilités).
Une expérience déjà dans le journal n'est ni recalculée ni remplacée.
Produit :
  - resultats/05_modeles/journal_experiences.csv, scores_par_pli.csv, parametres/E00x.json ;
  - resultats/04_references/tableaux/references_par_population.csv : moyennes sur les plis,
    par population, de la règle naïve et du hasard ;
  - resultats/04_references/figures/references_par_pli.png : PR-AUC et ROC-AUC pli par pli.
"""

import datetime
import json
import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.decoupage import plis_par_annee  # noqa: E402
from src.evaluation import (  # noqa: E402
    FICHIER_JOURNAL,
    FICHIER_SCORES,
    ajouter_au_journal,
    empreinte,
    evaluer_par_pli,
    resumer,
    version_du_code,
)

C_SANS_PENALITE = 1e6          # logistique sans pénalité réelle : la règle naïve n'a rien à régler
COULEURS = {"E002": "#2a78d6", "E001": "#eb6834"}
GRIS, GRILLE = "#6b6a64", "#e6e5e0"


def predire_hasard(entrainement, validation):
    return np.full(len(validation), entrainement["y"].mean()), {"part_y1_entrainement": float(entrainement["y"].mean())}


def predire_regle_naive(entrainement, validation):
    modele = LogisticRegression(C=C_SANS_PENALITE, max_iter=1000)
    modele.fit(np.log1p(entrainement[["activite"]]), entrainement["y"])
    return (modele.predict_proba(np.log1p(validation[["activite"]]))[:, 1],
            {"ordonnee": float(modele.intercept_[0]), "coef_log1p_activite": float(modele.coef_[0, 0])})


EXPERIENCES = [
    {"id": "E001", "modele": "hasard", "predire": predire_hasard, "reglages": {}, "preparation": "aucune",
     "commentaire": "niveau du hasard : probabilité constante égale à la part de y = 1 de l'entraînement du pli"},
    {"id": "E002", "modele": "regle_naive", "predire": predire_regle_naive, "reglages": {"C": C_SANS_PENALITE},
     "preparation": "log(1 + activite)",
     "commentaire": "règle naïve, recette fixée avant tout modèle : logistique sur log(1 + activité) seule"},
]


def main():
    config = charger_config()
    racine = racine_projet()
    chemin_table = chemin_donnees(config, "dossier_preparees") / "modelisation_mco.parquet"
    table = pd.read_parquet(chemin_table)
    entrainement = table[table["partie"] == "entrainement"].sort_values(["t", "fi"]).reset_index(drop=True)
    plis = plis_par_annee(entrainement["t"].to_numpy(), config["decoupage"]["annees_min_entrainement"])
    dossier = racine / "resultats" / "05_modeles"
    commit, modifie = version_du_code(racine)
    deja = (pd.read_csv(dossier / FICHIER_JOURNAL, dtype=str)["id"].tolist()
            if (dossier / FICHIER_JOURNAL).exists() else [])
    print(f"Entraînement : {len(entrainement)} lignes, {len(plis)} plis ; code {commit}"
          f"{' (modifié, non commité)' if modifie else ''}")

    for x in EXPERIENCES:
        if x["id"] in deja:
            print(f"{x['id']} ({x['modele']}) : déjà dans le journal, ni recalculée ni remplacée")
            continue
        scores_par_pli, parametres = evaluer_par_pli(entrainement, plis, x["predire"])
        experience = {"id": x["id"], "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "commit": commit,
                      "code_modifie_non_commite": modifie, "empreinte_table": empreinte(chemin_table),
                      "modele": x["modele"], "reglages": json.dumps(x["reglages"]), "preparation": x["preparation"],
                      "graine": config["projet"]["graine"],
                      **{k: round(v, 4) for k, v in resumer(scores_par_pli).items()}, "commentaire": x["commentaire"]}
        ajouter_au_journal(dossier, experience, scores_par_pli.round(4), parametres)
        print(f"{x['id']} ({x['modele']}) : ajoutée au journal")

    # Tableaux et figure des références, lus dans le journal
    journal = pd.read_csv(dossier / FICHIER_JOURNAL)
    scores = pd.read_csv(dossier / FICHIER_SCORES)
    references = scores[scores["id"].isin(["E001", "E002"])]
    tableaux, figures = racine / "resultats" / "04_references" / "tableaux", racine / "resultats" / "04_references" / "figures"
    tableaux.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    naive = references[references["id"] == "E002"]
    par_population = naive.groupby("population", sort=False).agg(
        pr_auc=("pr_auc", "mean"), pr_auc_hasard=("pr_auc_hasard", "mean"), roc_auc=("roc_auc", "mean"),
        brier=("brier", "mean"), brier_hasard=("brier_hasard", "mean"),
        plis_pr_auc_au_dessus_du_hasard=("pr_auc", lambda s: int((s > naive.loc[s.index, "pr_auc_hasard"]).sum())),
        plis_roc_au_dessus_de_0_5=("roc_auc", lambda s: int((s > 0.5).sum())), plis=("pli", "size"))
    par_population.round(4).to_csv(tableaux / "references_par_population.csv")

    colonnes = [c for c in journal.columns if c.endswith("_plis")]
    print("\nJournal (références) :")
    print(journal[journal["id"].isin(["E001", "E002"])][["id", "modele", "commit"] + colonnes].to_string(index=False))
    print("\nRègle naïve (E002), moyennes sur les plis par population :")
    print(par_population.round(3).to_string())

    toutes = references[references["population"] == "toutes"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, metrique, titre in ((axes[0], "pr_auc", "PR-AUC (trouver les rares y = 1)"),
                                (axes[1], "roc_auc", "ROC-AUC (classer un y = 1 avant un y = 0)")):
        for id_, nom in (("E002", "règle naïve (activité seule)"), ("E001", "hasard")):
            d = toutes[toutes["id"] == id_]
            ax.plot(d["annee_validee"].astype(str), d[metrique], marker="o", markersize=5, linewidth=2,
                    color=COULEURS[id_], label=nom)
        ax.set_title(titre, fontsize=10)
        ax.set_xlabel("année validée (pli)", color=GRIS)
        ax.set_ylim(0, None if metrique == "pr_auc" else 1)
        ax.grid(axis="y", color=GRILLE)
        ax.set_axisbelow(True)
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Références à battre, pli par pli (entraînement, toutes les lignes)", fontsize=11)
    fig.tight_layout()
    fig.savefig(figures / "references_par_pli.png", dpi=130)
    plt.close(fig)
    print(f"\nJournal dans {dossier.relative_to(racine)} ; tableau et figure dans "
          f"{tableaux.parent.relative_to(racine)}")


if __name__ == "__main__":
    main()
