"""Étape 07 : explorer les variables, sur l'entraînement seulement.

Lancement, depuis la racine du dépôt (après scripts/05_table_modelisation.py) :
    python scripts/07_exploration.py

Lignes : partie « entrainement » de la table de modélisation (le test et les passages Covid
ne sont jamais regardés ici). Décisions : docs/decisions.md.
Produit, dans resultats/03_exploration/ :
  - tableaux/correlations_paires.csv : chaque paire de variables numériques, avec les
    corrélations de Pearson (lien linéaire), Spearman (rangs) et Kendall (paires bien
    ordonnées ; à peu près 0,8 x Spearman, donc un seuil plus bas pour le même lien) ;
  - tableaux/lien_cible.csv : chaque variable seule, son AUC (décrochages et sorties contre
    stables, puis chacun à part), sa corrélation de Kendall et de Spearman avec y, ses cases vides ;
  - tableaux/modalites_categorielles.csv : lignes et y = 1 par modalité de stjr, catr, reg_actuelle,
    telle que déclarée (panel) et après regroupement des modalités rares (table de modélisation) ;
  - tableaux/indicateurs_par_classe.csv : chaque indicateur à 1, réparti en stables, décrochages, sorties ;
  - tableaux/taux_occupation.csv : lignes et y = 1 au-dessus de plusieurs taux d'occupation, et
    part expliquée par des journées exploitables trop basses ;
  - figures/y1_par_quintile_activite.png : part de décrochages et de sorties par quintile d'activité.
"""

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
from sklearn.metrics import roc_auc_score  # noqa: E402

from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.variables import CATEGORIELLES  # noqa: E402

CORRELATIONS = ["pearson", "spearman", "kendall"]
SEUILS_OCCUPATION = [1.0, 1.2, 1.5, 3.0, 10.0]
SEUILS_JLI = [0.5, 0.8]            # journées exploitables < seuil x lits x 365 : trop basses
COULEURS = {"decrochage": "#2a78d6", "sortie": "#eb6834"}
GRIS, GRILLE = "#6b6a64", "#e6e5e0"


def auc_d_une_variable(x, y):
    """AUC de la variable seule (cases vides retirées), tournée pour être >= 0,5, et son sens."""
    m = x.notna()
    if x[m].nunique() < 2 or y[m].nunique() < 2:
        return np.nan, ""
    auc = roc_auc_score(y[m], x[m])
    return max(auc, 1 - auc), "+" if auc >= 0.5 else "-"


def main():
    config = charger_config()
    table = pd.read_parquet(chemin_donnees(config, "dossier_preparees") / "modelisation_mco.parquet")
    e = table[table["partie"] == "entrainement"].reset_index(drop=True)
    panel = pd.read_parquet(chemin_donnees(config, "dossier_preparees") / "panel_mco.parquet")
    brutes = panel[["fi", "an"] + CATEGORIELLES].rename(columns={"an": "t", **{c: f"{c}_brut" for c in CATEGORIELLES}})
    e = e.merge(brutes, on=["fi", "t"], how="left", validate="one_to_one")
    numeriques = [c for c in e.columns if c not in ["fi", "t", "y", "partie", "classe"] + CATEGORIELLES
                  + [f"{c}_brut" for c in CATEGORIELLES]]
    sortie = racine_projet() / "resultats" / "03_exploration"
    tableaux, figures = sortie / "tableaux", sortie / "figures"
    tableaux.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    print(f"Entraînement : {len(e)} lignes, {int(e['y'].sum())} y = 1 ; {e['classe'].value_counts().to_dict()}")

    # 1. Paires de variables : trois corrélations
    haut = np.triu(np.ones((len(numeriques),) * 2, dtype=bool), 1)
    paires = pd.concat({m: e[numeriques].corr(method=m).where(haut).stack() for m in CORRELATIONS}, axis=1)
    paires.index.names = ["variable_1", "variable_2"]
    paires = paires.reset_index().sort_values("spearman", key=abs, ascending=False)
    paires.round(4).to_csv(tableaux / "correlations_paires.csv", index=False)
    print("\n1. Paires de variables numériques :", len(paires))
    for m in CORRELATIONS:
        print(f"   |{m}| >= 0,9 : {int((paires[m].abs() >= 0.9).sum())} ; >= 0,8 : {int((paires[m].abs() >= 0.8).sum())}")
    assez = paires["spearman"].abs() >= 0.3
    print(f"   Kendall / Spearman, médiane sur les paires |Spearman| >= 0,3 : "
          f"{(paires.loc[assez, 'kendall'] / paires.loc[assez, 'spearman']).median():.3f}")

    # 2. Lien de chaque variable avec la cible
    stables = e["classe"] == "stable"
    lignes = []
    for c in numeriques:
        auc, sens = auc_d_une_variable(e[c], e["y"])
        auc_d, _ = auc_d_une_variable(e.loc[stables | (e["classe"] == "decrochage"), c],
                                      e.loc[stables | (e["classe"] == "decrochage"), "y"])
        auc_s, _ = auc_d_une_variable(e.loc[stables | (e["classe"] == "sortie"), c],
                                      e.loc[stables | (e["classe"] == "sortie"), "y"])
        vide = e[c].isna()
        lignes.append({"variable": c, "auc": auc, "sens": sens, "auc_decrochages": auc_d, "auc_sorties": auc_s,
                       "kendall_y": e[[c, "y"]].corr(method="kendall").iloc[0, 1],
                       "spearman_y": e[[c, "y"]].corr(method="spearman").iloc[0, 1],
                       "vides_pct": 100 * vide.mean(),
                       "y1_si_vide_pct": 100 * e.loc[vide, "y"].mean() if vide.any() else np.nan})
    lien = pd.DataFrame(lignes).sort_values("auc", ascending=False)
    lien.round(4).to_csv(tableaux / "lien_cible.csv", index=False)
    print("\n2. Lien avec la cible, 15 premières variables (AUC d'une variable seule ; sens - : plus petit = plus de y = 1) :")
    print(lien.head(15).round(3).to_string(index=False))

    # 3. Modalités des variables catégorielles, déclarées et regroupées
    lignes = []
    for c in CATEGORIELLES:
        g = e.groupby([f"{c}_brut", c]).agg(lignes=("y", "size"), y1=("y", "sum"),
                             decrochages=("classe", lambda s: int((s == "decrochage").sum())),
                             sorties=("classe", lambda s: int((s == "sortie").sum())))
        g["y1_pct"] = 100 * g["y1"] / g["lignes"]
        lignes.append(g.reset_index().rename(columns={f"{c}_brut": "modalite", c: "modalite_regroupee"})
                      .assign(variable=c))
    modalites = pd.concat(lignes)[["variable", "modalite", "modalite_regroupee", "lignes", "y1", "y1_pct",
                                   "decrochages", "sorties"]]
    modalites = modalites.sort_values(["variable", "lignes"], ascending=[True, False])
    modalites.round(2).to_csv(tableaux / "modalites_categorielles.csv", index=False)
    print("\n3. Modalités déclarées de moins de 100 lignes, et leur regroupement :")
    print(modalites[modalites["lignes"] < 100].round(1).to_string(index=False))

    # 4. Indicateurs par classe
    indicateurs = [c for c in numeriques if c.startswith(("a_", "inc_"))]
    lignes = []
    for c in indicateurs:
        un = e[c] == 1
        compte = e.loc[un, "classe"].value_counts()
        lignes.append({"indicateur": c, "lignes_a_1": int(un.sum()), "stables": int(compte.get("stable", 0)),
                       "decrochages": int(compte.get("decrochage", 0)), "sorties": int(compte.get("sortie", 0)),
                       "y1_pct_si_1": 100 * e.loc[un, "y"].mean() if un.any() else np.nan,
                       "y1_pct_si_0": 100 * e.loc[~un, "y"].mean()})
    par_classe = pd.DataFrame(lignes)
    par_classe.round(2).to_csv(tableaux / "indicateurs_par_classe.csv", index=False)
    print("\n4. Indicateurs à 1, par classe :")
    print(par_classe.round(1).to_string(index=False))

    # 5. Taux d'occupation impossible
    occupation = e["taux_occupation_mco"]
    jli_par_lit = e["jli_mco"] / (365 * e["lit_mco"].where(e["lit_mco"] > 0))
    lignes = []
    for s in SEUILS_OCCUPATION:
        au_dessus = occupation > s
        ligne = {"taux_occupation_superieur_a": s, "lignes": int(au_dessus.sum()),
                 "y1_pct": 100 * e.loc[au_dessus, "y"].mean() if au_dessus.any() else np.nan}
        for seuil in SEUILS_JLI:
            ligne[f"dont_jli_sous_{seuil}_lits_x_365"] = int((au_dessus & (jli_par_lit < seuil)).sum())
        lignes.append(ligne)
    occupation_t = pd.DataFrame(lignes)
    occupation_t.round(2).to_csv(tableaux / "taux_occupation.csv", index=False)
    print(f"\n5. Taux d'occupation : médiane {occupation.median():.3f}, 99e centile {occupation.quantile(0.99):.3f}, "
          f"maximum {occupation.max():.1f}")
    print(occupation_t.round(1).to_string(index=False))

    # Figure : décrochages et sorties par quintile d'activité
    quintile = pd.qcut(e["activite"].rank(method="first"), 5, labels=False)
    parts = pd.DataFrame({k: 100 * (e["classe"] == k).groupby(quintile).mean() for k in COULEURS})
    bornes = e.groupby(quintile)["activite"].agg(["min", "max"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bas = np.zeros(len(parts))
    for k, nom in (("decrochage", "décrochages"), ("sortie", "sorties")):
        ax.bar(parts.index, parts[k], bottom=bas, width=0.6, color=COULEURS[k], label=nom,
               edgecolor="white", linewidth=2)
        bas += parts[k].to_numpy()
    for x, total in enumerate(bas):
        ax.text(x, total + 0.3, f"{total:.1f} %", ha="center", va="bottom", fontsize=9, color="#2b2a27")
    ax.set_ylim(0, 1.12 * bas.max())
    ax.set_xticks(parts.index)
    ax.set_xticklabels([f"Q{i + 1}\n{bornes.loc[i, 'min']:,.0f} – {bornes.loc[i, 'max']:,.0f}".replace(",", " ")
                        for i in parts.index], fontsize=8, color=GRIS)
    ax.set_ylabel("part des lignes (%)", color=GRIS)
    ax.set_title("Entraînement : décrochages et sorties par quintile d'activité (journées-équivalentes)", fontsize=10)
    ax.grid(axis="y", color=GRILLE)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(figures / "y1_par_quintile_activite.png", dpi=130)
    plt.close(fig)
    print("\n   Part de y = 1 par quintile d'activité (%) :", parts.sum(axis=1).round(1).tolist())

    print(f"\nTableaux écrits dans {tableaux.relative_to(racine_projet())}, figure dans "
          f"{figures.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
