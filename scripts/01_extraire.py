"""Étape 01 : extraire des archives les seules tables utiles au projet, et vérifier leur encodage.

Lancement, depuis la racine du dépôt (après scripts/00_telecharger.py) :
    python scripts/01_extraire.py

Pour chaque année de 2013 à 2025, extrait dans donnees/extraites/<annee>/ les
tables de config.yaml (ID, MCO, MCOPED, MCOGER, MCOAVC, URGENCES, SSR ou SMR),
depuis le dossier « Bases CSV » de l'archive.

Puis, AVANT toute lecture, vérifie l'encodage de chaque fichier : les 7 encodages
candidats sont essayés (src.qualite.encodages_valides), on garde ceux qui marchent,
et le script s'arrête si l'encodage déclaré dans config.yaml n'en fait pas partie.

Écrit dans resultats/01_qualite_donnees/tableaux/ :
  - extraction.csv : la liste des fichiers extraits (année, table, fichier, taille) ;
  - encodages.csv  : pour chaque fichier, les encodages qui marchent.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.chargement import (  # noqa: E402
    extraire_tables,
    lire_sources,
    lire_table,
    octets_invalides,
    tables_attendues,
)
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402
from src.qualite import CANDIDATS_ENCODAGE, encodages_valides  # noqa: E402

# Nombre d'octets illisibles tolérés pour qu'un encodage « marche quand même » :
# une faute de frappe isolée ne doit pas bloquer tout le projet. Au-delà : arrêt.
OCTETS_ILLISIBLES_TOLERES = 10


def verifier_encodage(chemin, attendu):
    """Encodages qui marchent pour un fichier, et verdict par rapport à config.yaml."""
    valides = encodages_valides(chemin)
    tolere = [] if valides else encodages_valides(chemin, octets_illisibles_toleres=OCTETS_ILLISIBLES_TOLERES)
    return {"encodages_valides": " ".join(valides),
            "valides_a_quelques_octets_pres": " ".join(tolere),
            "encodage_config": attendu,
            "conforme": attendu in valides or attendu in tolere}


def main():
    config = charger_config()
    d = config["donnees"]
    sources = lire_sources(chemin_donnees(config, "fichier_sources"))
    brutes = chemin_donnees(config, "dossier_brutes")
    extraites = chemin_donnees(config, "dossier_extraites")

    bilan, encodages = [], []
    for source in sources:
        annee = source["annee"]
        archive = brutes / source["fichier"]
        if not archive.exists():
            sys.exit(f"Archive absente : {archive}. Lancer d'abord scripts/00_telecharger.py")

        tables = tables_attendues(d["tables"], annee)
        fichiers = extraire_tables(archive, annee, tables, extraites, d["dossier_csv"])

        # 1. Encodage, AVANT toute lecture
        attendu = encodage_de_l_annee(config, annee)
        for table, chemin in fichiers.items():
            verdict = verifier_encodage(chemin, attendu)
            encodages.append({"annee": annee, "table": table, "fichier": chemin.name, **verdict})
            if not verdict["conforme"]:
                sys.exit(f"ARRÊT : {chemin.name} ne se lit pas en {attendu} (config.yaml). "
                         f"Encodages qui marchent : {verdict['encodages_valides'] or 'aucun'}.")

        # 2. Lecture et bilan
        for table, chemin in fichiers.items():
            invalides = octets_invalides(chemin, attendu)
            # Un octet illisible est remplacé par « � » et compté : on ne bloque pas
            # tout le projet pour une faute de frappe, mais on la documente.
            donnees = lire_table(chemin, attendu, d["separateur_csv"], erreurs="replace")
            bilan.append({"annee": annee, "table": table, "fichier": chemin.name,
                          "encodage": attendu, "octets": chemin.stat().st_size,
                          "lignes": len(donnees), "colonnes": donnees.shape[1],
                          "octets_illisibles": len(invalides),
                          "positions_illisibles": " ".join(map(str, invalides))})
            if invalides:
                print(f"  {annee}  ATTENTION {chemin.name} : {len(invalides)} octet(s) illisible(s) "
                      f"en {attendu}, remplacé(s) par « � » (positions {invalides})")
        print(f"  {annee}  {len(fichiers)} tables extraites, encodage {attendu} vérifié, tables lues")

    tableaux = racine_projet() / "resultats" / "01_qualite_donnees" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(bilan).to_csv(tableaux / "extraction.csv", index=False, encoding="utf-8")
    encodages = pd.DataFrame(encodages)
    encodages.to_csv(tableaux / "encodages.csv", index=False, encoding="utf-8")

    # Résumé : pour chaque année, les encodages qui marchent pour TOUS ses fichiers
    print(f"\nEncodages essayés : {', '.join(CANDIDATS_ENCODAGE)}")
    print("Encodages qui marchent pour tous les fichiers de l'année :")
    for annee, groupe in encodages.groupby("annee"):
        ensembles = [set((v or t).split()) for v, t in
                     zip(groupe.encodages_valides, groupe.valides_a_quelques_octets_pres)]
        communs = [c for c in CANDIDATS_ENCODAGE if all(c in e for e in ensembles)]
        a_peu_pres = groupe[groupe.valides_a_quelques_octets_pres.str.len() > 0]
        note = f"  (à quelques octets près : {', '.join(a_peu_pres.fichier)})" if len(a_peu_pres) else ""
        print(f"  {annee} : {', '.join(communs) or 'aucun'}  ->  config.yaml : "
              f"{groupe.encodage_config.iloc[0]}{note}")

    print(f"Détail fichier par fichier dans {(tableaux / 'encodages.csv').relative_to(racine_projet())}")

    bilan = pd.DataFrame(bilan)
    print("\nNombre de lignes par table et par année :")
    print(bilan.pivot(index="annee", columns="table", values="lignes").fillna(0).astype(int).to_string())
    print(f"\n{len(bilan)} fichiers extraits et lus dans {extraites}")
    print(f"Bilan (lignes, colonnes, octets illisibles) dans "
          f"{(tableaux / 'extraction.csv').relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
