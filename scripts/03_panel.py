"""Étape 03 : construire le panel, une ligne par établissement et par année.

Lancement, depuis la racine du dépôt (après scripts/01_extraire.py) :
    python scripts/03_panel.py

Pour l'instant : empilement des 13 années de la table MCO, avec deux vérifications
(le script s'arrête si l'une échoue) :
  - le panel a autant de lignes que les 13 fichiers réunis ;
  - le couple (fi, an) n'apparaît jamais deux fois.
Produit donnees/preparees/panel_mco.parquet (non versionné, régénérable).
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chargement import empiler_table, lire_table, trouver_table_extraite  # noqa: E402
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402


def main():
    config = charger_config()
    d = config["donnees"]
    extraites = chemin_donnees(config, "dossier_extraites")
    annees = list(range(d["annee_debut"], d["annee_fin"] + 1))

    # Empilement
    panel = empiler_table(config, "MCO", annees, extraites)

    # Vérification 1 : autant de lignes que les 13 fichiers réunis
    attendu = sum(len(lire_table(trouver_table_extraite(extraites, "MCO", a), encodage_de_l_annee(config, a),
                                 d["separateur_csv"], erreurs="replace")) for a in annees)
    if len(panel) != attendu:
        sys.exit(f"ARRÊT : {len(panel)} lignes empilées, {attendu} attendues.")

    # Vérification 2 : (fi, an) jamais en double
    doublons = int(panel.duplicated(d["cle"]).sum())
    if doublons:
        sys.exit(f"ARRÊT : {doublons} ligne(s) en double sur la clé {d['cle']}.")

    preparees = chemin_donnees(config, "dossier_preparees")
    preparees.mkdir(parents=True, exist_ok=True)
    sortie = preparees / "panel_mco.parquet"
    panel.to_parquet(sortie, index=False)

    print(f"Panel : {len(panel)} lignes (= {attendu}, somme des 13 fichiers MCO), "
          f"{panel.shape[1]} colonnes, 0 doublon sur {d['cle']}\n")
    print("Lignes par année :")
    print(panel.groupby("an").size().to_string())
    print(f"\nPanel écrit dans {sortie.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
