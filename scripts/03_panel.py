"""Étape 03 : construire le panel, une ligne par établissement et par année.

Lancement, depuis la racine du dépôt (après scripts/01_extraire.py) :
    python scripts/03_panel.py

Le panel part de la table MCO (src.variables.construire_panel) : empilement des 13 années,
conversion des quantités en nombres, décisions 1 et 2, identité (table ID) et région
actuelle (décision 4), indicateurs des autres tables (décision 5) ;
décisions dans docs/nettoyage_donnees.md.
Deux vérifications (le script s'arrête si l'une échoue) :
  - le panel a autant de lignes que les 13 fichiers MCO réunis ;
  - le couple (fi, an) n'apparaît jamais deux fois.
Produit :
  - donnees/preparees/panel_mco.parquet (non versionné, régénérable) ;
  - resultats/01_qualite_donnees/tableaux/panel_controles.csv : ce que chaque étape a fait.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.chargement import lire_table, trouver_table_extraite  # noqa: E402
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402
from src.variables import construire_panel  # noqa: E402


def main():
    config = charger_config()
    d = config["donnees"]
    extraites = chemin_donnees(config, "dossier_extraites")
    annees = list(range(d["annee_debut"], d["annee_fin"] + 1))

    panel, controles = construire_panel(config, extraites, annees)
    controles = pd.DataFrame(controles)

    # Vérification 1 : autant de lignes que les 13 fichiers réunis
    attendu = sum(len(lire_table(trouver_table_extraite(extraites, "MCO", a), encodage_de_l_annee(config, a),
                                 d["separateur_csv"], erreurs="replace")) for a in annees)
    if len(panel) != attendu:
        sys.exit(f"ARRÊT : {len(panel)} lignes dans le panel, {attendu} attendues.")

    # Vérification 2 : (fi, an) jamais en double
    doublons = int(panel.duplicated(d["cle"]).sum())
    if doublons:
        sys.exit(f"ARRÊT : {doublons} ligne(s) en double sur la clé {d['cle']}.")

    preparees = chemin_donnees(config, "dossier_preparees")
    preparees.mkdir(parents=True, exist_ok=True)
    sortie = preparees / "panel_mco.parquet"
    panel.to_parquet(sortie, index=False)
    tableaux = racine_projet() / "resultats" / "01_qualite_donnees" / "tableaux"
    controles.to_csv(tableaux / "panel_controles.csv", index=False, encoding="utf-8")

    print(f"Panel : {len(panel)} lignes (= {attendu}, somme des 13 fichiers MCO), "
          f"{panel.shape[1]} colonnes, 0 doublon sur {d['cle']}\n")

    conversion = controles[controles.etape == "conversion"]
    print(f"Conversion en nombres : {conversion.valeur.sum()} valeur(s) non numérique(s) "
          f"sur les {len(conversion)} quantités")

    capacites = controles[controles.etape == "capacites"]
    mises_a_zero = capacites[capacites.mesure.str.contains("mis à 0")].valeur.sum()
    laissees = capacites[capacites.mesure.str.contains("laissé vide")].valeur.sum()
    print(f"Décision 1 (capacités vides) : {mises_a_zero} cases mises à 0, {laissees} laissées vides")

    print("\nDécision 2 (incohérences repérées, non corrigées), nombre de lignes :")
    print(controles[controles.etape == "incoherences"][["mesure", "valeur"]].to_string(index=False, header=False))

    identite = controles[controles.etape.isin(["identite", "jointures"])]
    print("\nIdentité (table ID) et région actuelle :")
    print(identite[["mesure", "valeur"]].to_string(index=False, header=False))
    print("\nIndicateurs tirés des autres tables (décision 5), nombre de lignes du panel :")
    print(controles[controles.etape == "indicateurs"][["mesure", "valeur"]]
          .to_string(index=False, header=False))

    print("\nÉtablissements par région actuelle (2025) :")
    print(panel[panel.an == panel.an.max()].groupby("reg_actuelle").size().to_string())

    print(f"\nPanel écrit dans {sortie.relative_to(racine_projet())}")
    print(f"Contrôles écrits dans {(tableaux / 'panel_controles.csv').relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
