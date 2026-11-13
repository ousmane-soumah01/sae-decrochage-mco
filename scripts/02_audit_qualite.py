"""Étape 02 : audit de qualité de toutes les tables, année par année, AVANT l'empilement.

Lancement, depuis la racine du dépôt (après scripts/01_extraire.py) :
    python scripts/02_audit_qualite.py

Rien n'est corrigé ici : on mesure, puis on décide et on documente.
Contrôles :
  1. présence des colonnes selon les années      -> colonnes_par_annee.csv
  2. part de valeurs manquantes                  -> manquants.csv
     (+ figure des quantités d'activité et de capacité de la table MCO)
Sorties dans resultats/01_qualite_donnees/ (tableaux/ et figures/).
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")                       # figures écrites dans des fichiers, sans fenêtre
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.chargement import lire_table, tables_attendues, trouver_table_extraite  # noqa: E402
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402
from src.qualite import presence_colonnes, resume_presence, taux_manquants  # noqa: E402

# Quantités d'activité et de capacité de la table MCO (journées, séjours, séjours de 0 jour,
# venues de partielle, lits, places, journées exploitables, par discipline, et séances).
QUANTITES_MCO = [f"{m}_{d}" for m in ("jou", "sejhc", "sej0", "sejhp", "lit", "pla", "jli")
                 for d in ("med", "chi", "obs", "mco")] + ["sea_mco"]


def nom_stable(table):
    """SSR (2013-2024) et SMR (2025) sont la même table : un seul nom pour l'audit."""
    return "SSR_SMR" if table in ("SSR", "SMR") else table


def figure_manquants(grille, dossier):
    """Carte colonne x année de la part de cases vides (une seule couleur, du clair au foncé)."""
    dossier.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 9))
    image = ax.imshow(100 * grille.values, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(len(grille.columns)), grille.columns, rotation=45)
    ax.set_yticks(range(len(grille.index)), grille.index)
    for i in range(grille.shape[0]):
        for j in range(grille.shape[1]):
            valeur = 100 * grille.values[i, j]
            if valeur >= 0.05:
                ax.text(j, i, f"{valeur:.1f}", ha="center", va="center", fontsize=7,
                        color="white" if valeur > 50 else "#2b2b2a")
    ax.set_title("Table MCO : part de cases vides (%) des quantités d'activité et de capacité",
                 loc="left", fontsize=11)
    fig.colorbar(image, label="part de cases vides (%)")
    fig.tight_layout()
    fig.savefig(dossier / "manquants_quantites_mco.png", dpi=130)
    plt.close(fig)


def main():
    config = charger_config()
    d = config["donnees"]
    extraites = chemin_donnees(config, "dossier_extraites")
    annees = range(d["annee_debut"], d["annee_fin"] + 1)

    colonnes = {}            # {table: {annee: [colonnes]}}
    manquants = []
    for annee in annees:
        encodage = encodage_de_l_annee(config, annee)
        for table in tables_attendues(d["tables"], annee):
            chemin = trouver_table_extraite(extraites, table, annee)
            lue = lire_table(chemin, encodage, d["separateur_csv"], erreurs="replace")
            colonnes.setdefault(nom_stable(table), {})[annee] = list(lue.columns)
            for colonne, taux in taux_manquants(lue).items():
                manquants.append({"table": nom_stable(table), "annee": annee,
                                  "colonne": colonne, "taux_manquants": round(taux, 4)})

    # 1. Présence des colonnes
    presence = pd.concat([resume_presence(presence_colonnes(par_annee)).assign(table=t)
                          for t, par_annee in colonnes.items()])
    presence = presence[["table", "colonne", "nb_annees", "premiere", "derniere",
                         "presente_toutes_annees", "annees_absentes"]]

    tableaux = racine_projet() / "resultats" / "01_qualite_donnees" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    sortie = tableaux / "colonnes_par_annee.csv"
    presence.to_csv(sortie, index=False, encoding="utf-8")

    print("1. Présence des colonnes, par table :")
    resume = presence.groupby("table").agg(
        colonnes=("colonne", "size"),
        toutes_les_annees=("presente_toutes_annees", "sum"),
    )
    resume["certaines_annees_seulement"] = resume["colonnes"] - resume["toutes_les_annees"]
    print(resume.to_string())
    print(f"\nDétail colonne par colonne dans {sortie.relative_to(racine_projet())}")

    # 2. Valeurs manquantes
    manquants = pd.DataFrame(manquants)
    manquants.to_csv(tableaux / "manquants.csv", index=False, encoding="utf-8")
    grille = (manquants[(manquants.table == "MCO") & manquants.colonne.isin(QUANTITES_MCO)]
              .pivot(index="colonne", columns="annee", values="taux_manquants")
              .reindex(QUANTITES_MCO))
    figure_manquants(grille, racine_projet() / "resultats" / "01_qualite_donnees" / "figures")

    print("\n2. Part de cases vides (%) des quantités MCO, minimum et maximum sur les 13 années :")
    etendue = (100 * grille).agg(["min", "max"], axis=1).round(1)
    print(etendue.to_string())
    print("Détail dans resultats/01_qualite_donnees/tableaux/manquants.csv "
          "et figures/manquants_quantites_mco.png")


if __name__ == "__main__":
    main()
