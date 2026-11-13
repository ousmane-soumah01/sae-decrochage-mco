"""Étape 01 : extraire des archives les seules tables utiles au projet.

Lancement, depuis la racine du dépôt (après scripts/00_telecharger.py) :
    python scripts/01_extraire.py

Pour chaque année de 2013 à 2025, extrait dans donnees/extraites/<annee>/ les
tables de config.yaml (ID, MCO, MCOPED, MCOGER, MCOAVC, URGENCES, SSR ou SMR),
depuis le dossier « Bases CSV » de l'archive.

Écrit la liste des fichiers extraits (année, table, fichier, taille) dans
resultats/01_qualite_donnees/tableaux/extraction.csv.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.chargement import extraire_tables, lire_sources, tables_attendues  # noqa: E402
from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402


def main():
    config = charger_config()
    d = config["donnees"]
    sources = lire_sources(chemin_donnees(config, "fichier_sources"))
    brutes = chemin_donnees(config, "dossier_brutes")
    extraites = chemin_donnees(config, "dossier_extraites")

    bilan = []
    for source in sources:
        annee = source["annee"]
        archive = brutes / source["fichier"]
        if not archive.exists():
            sys.exit(f"Archive absente : {archive}. Lancer d'abord scripts/00_telecharger.py")

        tables = tables_attendues(d["tables"], annee)
        fichiers = extraire_tables(archive, annee, tables, extraites, d["dossier_csv"])
        for table, chemin in fichiers.items():
            bilan.append({"annee": annee, "table": table, "fichier": chemin.name,
                          "octets": chemin.stat().st_size})
        print(f"  {annee}  {len(fichiers)} tables extraites")

    tableaux = racine_projet() / "resultats" / "01_qualite_donnees" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    sortie = tableaux / "extraction.csv"
    bilan = pd.DataFrame(bilan)
    bilan.to_csv(sortie, index=False, encoding="utf-8")

    print("\nFichier extrait pour chaque table et chaque année :")
    print(bilan.pivot(index="annee", columns="table", values="fichier").fillna("-").to_string())
    print(f"\n{len(bilan)} fichiers extraits dans {extraites}")
    print(f"Liste écrite dans {sortie.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
