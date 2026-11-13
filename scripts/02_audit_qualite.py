"""Étape 02 : audit de qualité de toutes les tables, année par année, AVANT l'empilement.

Lancement, depuis la racine du dépôt (après scripts/01_extraire.py) :
    python scripts/02_audit_qualite.py

Rien n'est corrigé ici : on mesure, puis on décide et on documente.
Contrôles :
  1. présence des colonnes selon les années      -> colonnes_par_annee.csv
Sorties dans resultats/01_qualite_donnees/tableaux/.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.chargement import lire_table, tables_attendues, trouver_table_extraite  # noqa: E402
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402
from src.qualite import presence_colonnes, resume_presence  # noqa: E402


def nom_stable(table):
    """SSR (2013-2024) et SMR (2025) sont la même table : un seul nom pour l'audit."""
    return "SSR_SMR" if table in ("SSR", "SMR") else table


def main():
    config = charger_config()
    d = config["donnees"]
    extraites = chemin_donnees(config, "dossier_extraites")
    annees = range(d["annee_debut"], d["annee_fin"] + 1)

    colonnes = {}            # {table: {annee: [colonnes]}}
    for annee in annees:
        encodage = encodage_de_l_annee(config, annee)
        for table in tables_attendues(d["tables"], annee):
            chemin = trouver_table_extraite(extraites, table, annee)
            lue = lire_table(chemin, encodage, d["separateur_csv"], erreurs="replace")
            colonnes.setdefault(nom_stable(table), {})[annee] = list(lue.columns)

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


if __name__ == "__main__":
    main()
