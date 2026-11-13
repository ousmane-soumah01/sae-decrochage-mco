"""Étape 00 : récupérer les archives de la SAE et vérifier leur empreinte md5.

Lancement, depuis la racine du dépôt :
    python scripts/00_telecharger.py

Pour chaque année de donnees/sources_donnees_brutes.csv :
  - si l'archive est déjà dans donnees/brutes/ avec le bon md5 : rien à faire ;
  - sinon : téléchargement depuis la DREES, puis vérification du md5.
Le script s'arrête avec une erreur si une empreinte ne correspond pas.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chargement import Md5Incorrect, lire_sources, recuperer_archive  # noqa: E402
from src.config import charger_config, chemin_donnees  # noqa: E402


def main():
    config = charger_config()
    sources = lire_sources(chemin_donnees(config, "fichier_sources"))
    dossier = chemin_donnees(config, "dossier_brutes")
    print(f"{len(sources)} archives attendues dans {dossier}\n")

    erreurs = 0
    for source in sources:
        try:
            etat = recuperer_archive(source, dossier)
            message = "OK (déjà présente)" if etat == "deja_presente" else "OK (téléchargée)"
            print(f"  {source['annee']}  {message}")
        except Md5Incorrect as e:
            erreurs += 1
            print(f"  {source['annee']}  ERREUR md5 : {e}")
        except OSError as e:          # réseau coupé, serveur indisponible, disque plein...
            erreurs += 1
            print(f"  {source['annee']}  ERREUR de téléchargement : {e}")

    if erreurs:
        print(f"\n{erreurs} archive(s) en erreur : ne pas analyser avant d'avoir compris pourquoi.")
        sys.exit(1)
    print(f"\nLes {len(sources)} archives sont présentes et identiques à celles du projet.")


if __name__ == "__main__":
    main()
