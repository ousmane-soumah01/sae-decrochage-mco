"""Étape 06 : écrire le dictionnaire des colonnes du panel (docs/dictionnaire.md).

Lancement, depuis la racine du dépôt (après scripts/03_panel.py) :
    python scripts/06_dictionnaire.py

Une ligne par colonne : groupe, définition (libellé DREES quand il existe), unité, source,
règle, et part de cases vides mesurée sur le panel. Les définitions sont dans
src/dictionnaire.py. Le script s'arrête si une colonne du panel n'est pas documentée,
ou si une définition porte sur une colonne absente.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.dictionnaire import colonnes_sans_definition, table_dictionnaire, vers_markdown  # noqa: E402


def main():
    config = charger_config()
    panel = pd.read_parquet(chemin_donnees(config, "dossier_preparees") / "panel_mco.parquet")

    sans_definition, orphelines = colonnes_sans_definition(panel)
    if sans_definition or orphelines:
        sys.exit(f"ARRÊT : colonnes sans définition {sans_definition}, définitions sans colonne {orphelines}. "
                 "Compléter src/dictionnaire.py ou relancer scripts/03_panel.py.")

    dico = table_dictionnaire(panel)
    sortie = racine_projet() / "docs" / "dictionnaire.md"
    sortie.write_text(vers_markdown(dico, len(panel)), encoding="utf-8")

    print(f"Dictionnaire : {len(dico)} colonnes du panel documentées")
    print(dico["groupe"].value_counts().reindex(dico["groupe"].unique()).to_string())
    print(f"\nÉcrit dans {sortie.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
