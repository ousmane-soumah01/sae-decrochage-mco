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
  - figures/y1_par_quintile_activite.png : part de décrochages et de sorties par quintile d'activité ;
  - figures/nuages_de_points.png : nuages de points de 6 variables clés, par classe ;
  - ACP descriptive des variables numériques continues (log des quantités, centrées-réduites ; les
    indicateurs et les catégorielles ne servent qu'à décrire) : tableaux/acp_variance.csv,
    tableaux/acp_charges.csv (corrélations des variables avec les 4 premières composantes),
    tableaux/acp_amas.csv (profil des deux amas du plan 1-2 où se concentrent les y = 1),
    figures/acp.png. L'ACP n'est pas utilisée par les modèles (sauf en variante, apprise dans chaque pli).
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
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.variables import CATEGORIELLES, QUANTITES_MCO  # noqa: E402

CORRELATIONS = ["pearson", "spearman", "kendall"]
SEUILS_OCCUPATION = [1.0, 1.2, 1.5, 3.0, 10.0]
SEUILS_JLI = [0.5, 0.8]            # journées exploitables < seuil x lits x 365 : trop basses
COULEURS = {"decrochage": "#2a78d6", "sortie": "#eb6834"}
GRIS, GRILLE = "#6b6a64", "#e6e5e0"
CLASSES = {"stable": ("stables", "#b9b8b2"), "decrochage": ("décrochages", "#2a78d6"), "sortie": ("sorties", "#eb6834")}
# Nuages de points : 6 variables clés (taille, mode de prise en charge, place dans l'entité)
VARIABLES_NUAGES = {"log_activite": "log(1 + activité)", "taux_occupation_mco": "taux d'occupation",
                    "duree_moyenne_sejour_mco": "durée moyenne de séjour", "part_partielle_mco": "part de la partielle",
                    "part_journees_chi": "part des journées de chirurgie", "sites_entite": "log(1 + sites de l'entité)"}
# ACP : variables numériques continues ; les quantités passent par log(1 + x)
ACP_EN_LOG = QUANTITES_MCO + ["activite", "sites_entite"]
ACP_CONTINUES = ACP_EN_LOG + ["taux_occupation_mco", "part_partielle_mco", "duree_moyenne_sejour_mco",
                              "part_journees_med", "part_journees_chi", "part_journees_obs", "part_site_dans_entite"]
ACP_PLAFONNEES = ["taux_occupation_mco", "duree_moyenne_sejour_mco"]     # au 99e centile, pour l'ACP seulement
# Amas du plan 1-2 où se concentrent les y = 1 (lus sur la figure, décrits dans acp_amas.csv)
AMAS = {"petits établissements de médecine (CP1 < -4, CP2 < 0)": lambda c1, c2: (c1 < -4) & (c2 < 0),
        "petites cliniques de chirurgie ambulatoire (CP1 < -1, CP2 > 4)": lambda c1, c2: (c1 < -1) & (c2 > 4)}


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

    nuages_de_points(e, figures)
    acp_descriptive(e, tableaux, figures)

    print(f"\nTableaux écrits dans {tableaux.relative_to(racine_projet())}, figures dans "
          f"{figures.relative_to(racine_projet())}")


def habiller(ax):
    ax.grid(color=GRILLE)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)


def dessiner_par_classe(ax, x, y, classe):
    """Les stables d'abord, petits et pâles ; décrochages et sorties par-dessus, pour rester visibles."""
    for c, (nom, couleur) in CLASSES.items():
        m = (classe == c).to_numpy()
        ax.scatter(x[m], y[m], s=2 if c == "stable" else 6, alpha=0.25 if c == "stable" else 0.8,
                   color=couleur, linewidths=0, label=nom)


def nuages_de_points(e, figures):
    """6. Nuages de points des variables clés, par classe (affichage : taux d'occupation jusqu'à 1,5,
    durée de séjour jusqu'à 25 jours ; les valeurs ne sont pas modifiées ailleurs)."""
    v = e[list(VARIABLES_NUAGES)].copy()
    v["taux_occupation_mco"] = v["taux_occupation_mco"].clip(upper=1.5)
    v["duree_moyenne_sejour_mco"] = v["duree_moyenne_sejour_mco"].clip(upper=25)
    v["sites_entite"] = np.log1p(v["sites_entite"])
    k = len(VARIABLES_NUAGES)
    fig, ax = plt.subplots(k, k, figsize=(15, 15))
    for i, a in enumerate(VARIABLES_NUAGES):
        for j, b in enumerate(VARIABLES_NUAGES):
            x = ax[i, j]
            if i == j:
                for c, (nom, couleur) in CLASSES.items():
                    x.hist(v.loc[e["classe"] == c, a].dropna(), bins=40, density=True, histtype="step",
                           color=couleur, linewidth=1.5)
            else:
                dessiner_par_classe(x, v[b].to_numpy(), v[a].to_numpy(), e["classe"])
            if j == 0:
                x.set_ylabel(VARIABLES_NUAGES[a], fontsize=8, color=GRIS)
            if i == k - 1:
                x.set_xlabel(VARIABLES_NUAGES[b], fontsize=8, color=GRIS)
            x.tick_params(labelsize=6)
            habiller(x)
    ax[0, 1].legend(markerscale=4, frameon=False, fontsize=8)
    fig.suptitle(f"Entraînement ({len(e)} lignes) : nuages de points de 6 variables, par classe\n"
                 "(taux d'occupation affiché jusqu'à 1,5, durée de séjour jusqu'à 25 jours)", fontsize=12)
    fig.tight_layout()
    fig.savefig(figures / "nuages_de_points.png", dpi=90)
    plt.close(fig)


def acp_descriptive(e, tableaux, figures):
    """7. ACP descriptive : variance expliquée, charges, plans 1-2 et 3-4, profil des deux amas."""
    X = e[ACP_CONTINUES].copy()
    X[ACP_EN_LOG] = np.log1p(X[ACP_EN_LOG])
    for c in ACP_PLAFONNEES:
        X[c] = X[c].clip(upper=X[c].quantile(0.99))
    Z = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X))
    acp = PCA().fit(Z)
    C = acp.transform(Z)
    ve = acp.explained_variance_ratio_
    variance = pd.DataFrame({"composante": range(1, len(ve) + 1), "valeur_propre": acp.explained_variance_,
                             "variance_expliquee_pct": 100 * ve, "cumul_pct": 100 * np.cumsum(ve)})
    variance.round(3).to_csv(tableaux / "acp_variance.csv", index=False)
    charges = pd.DataFrame(acp.components_[:4].T * np.sqrt(acp.explained_variance_[:4]), index=ACP_CONTINUES,
                           columns=["cp1", "cp2", "cp3", "cp4"])
    charges.index.name = "variable"
    charges.round(3).to_csv(tableaux / "acp_charges.csv")
    print(f"\n7. ACP de {len(ACP_CONTINUES)} variables continues : variance expliquée (%) des 5 premières composantes "
          f"{np.round(100 * ve[:5], 1).tolist()} ; cumul : 2 composantes {100 * ve[:2].sum():.1f} %, "
          f"5 : {100 * ve[:5].sum():.1f} %, 90 % atteints avec {int(np.searchsorted(np.cumsum(ve), 0.9) + 1)} ; "
          f"valeurs propres > 1 : {int((acp.explained_variance_ > 1).sum())}")
    for cp in ["cp1", "cp2", "cp3"]:
        tri = charges[cp].sort_values(key=abs, ascending=False).head(5)
        print(f"   {cp} : " + ", ".join(f"{n} {x:+.2f}" for n, x in tri.items()))

    lignes = []
    for nom, choisir in {**AMAS, "tout l'entraînement": lambda c1, c2: np.ones(len(c1), dtype=bool)}.items():
        g = e[choisir(C[:, 0], C[:, 1])]
        lignes.append({"amas": nom, "lignes": len(g), "y1": int(g["y"].sum()), "y1_pct": 100 * g["y"].mean(),
                       "activite_mediane": g["activite"].median(),
                       "duree_sejour_mediane": g["duree_moyenne_sejour_mco"].median(),
                       "part_partielle_mediane": g["part_partielle_mco"].median(),
                       "part_chirurgie_mediane": g["part_journees_chi"].median(),
                       "urgences_pct": 100 * g["a_urgences"].mean(), "smr_pct": 100 * g["a_smr"].mean(),
                       "catr_principales": ", ".join(f"{k} ({n})" for k, n in g["catr"].value_counts().head(3).items())})
    amas = pd.DataFrame(lignes)
    amas.round(2).to_csv(tableaux / "acp_amas.csv", index=False)
    print("   Amas du plan 1-2 :")
    print(amas.drop(columns="catr_principales").round(1).to_string(index=False))

    fig, ax = plt.subplots(2, 2, figsize=(13, 11))
    n = min(15, len(ve))
    ax[0, 0].bar(range(1, n + 1), 100 * ve[:n], color="#2a78d6", label="par composante")
    ax[0, 0].plot(range(1, n + 1), 100 * np.cumsum(ve[:n]), color="#eb6834", marker="o", markersize=4, label="cumul")
    ax[0, 0].set_title("Variance expliquée (%)", fontsize=10)
    ax[0, 0].set_xlabel("composante", color=GRIS)
    ax[0, 0].legend(frameon=False, fontsize=8)
    for x, (p, q) in zip([ax[0, 1], ax[1, 0]], [(0, 1), (2, 3)]):
        dessiner_par_classe(x, C[:, p], C[:, q], e["classe"])
        x.set_xlabel(f"CP{p + 1} ({100 * ve[p]:.1f} %)", color=GRIS)
        x.set_ylabel(f"CP{q + 1} ({100 * ve[q]:.1f} %)", color=GRIS)
        x.set_title(f"Plan {p + 1}-{q + 1}, par classe", fontsize=10)
    ax[0, 1].legend(markerscale=4, frameon=False, fontsize=8)
    x = ax[1, 1]
    x.add_patch(plt.Circle((0, 0), 1, fill=False, color=GRIS, linewidth=0.8))
    meilleures = charges.assign(norme=np.hypot(charges["cp1"], charges["cp2"])).nlargest(14, "norme")
    for nom, r in meilleures.iterrows():
        x.arrow(0, 0, r["cp1"], r["cp2"], color="#2a78d6", head_width=0.02, linewidth=0.8, length_includes_head=True)
        x.text(1.07 * r["cp1"], 1.07 * r["cp2"], nom, fontsize=7, color="#2b2a27", ha="center")
    x.set_xlim(-1.15, 1.15)
    x.set_ylim(-1.15, 1.15)
    x.set_aspect("equal")
    x.set_title("Cercle des corrélations, plan 1-2 (14 variables les mieux représentées)", fontsize=10)
    for a in ax.flat:
        habiller(a)
    fig.suptitle("Entraînement : ACP descriptive des variables numériques continues "
                 "(log des quantités, centrées-réduites)", fontsize=12)
    fig.tight_layout()
    fig.savefig(figures / "acp.png", dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    main()
