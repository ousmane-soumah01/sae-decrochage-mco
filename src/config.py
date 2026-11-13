"""Lecture et vérification des règles du projet (config.yaml).

Toutes les règles sont écrites une seule fois, dans config.yaml. Les autres
modules ne les réécrivent jamais : ils appellent charger_config().

Exemple :
    from src.config import charger_config, chemin_donnees
    config = charger_config()
    config["donnees"]["annee_debut"]            # 2013
    chemin_donnees(config, "dossier_brutes")    # <racine>/donnees/brutes
"""

from pathlib import Path

import yaml

# Sections et clés que config.yaml doit obligatoirement contenir.
CLES_OBLIGATOIRES = {
    "projet": ["nom", "graine"],
    "donnees": ["fichier_sources", "dossier_brutes", "dossier_extraites",
                "dossier_preparees", "annee_debut", "annee_fin",
                "encodage_csv", "encodage_csv_utf8_a_partir_de",
                "separateur_csv", "cle", "tables"],
}


def racine_projet():
    """Dossier racine du dépôt (celui qui contient config.yaml).

    Ce fichier est dans <racine>/src/ : la racine est le dossier parent de src/.
    Fonctionne quel que soit le dossier d'où l'on lance Python.
    """
    return Path(__file__).resolve().parent.parent


def verifier_config(config):
    """Vérifie que la configuration est complète et cohérente.

    Ne renvoie rien si tout va bien ; sinon lève ValueError avec un message
    qui dit exactement ce qui ne va pas.
    """
    if not isinstance(config, dict):
        raise ValueError("La configuration doit être un dictionnaire (config.yaml vide ?).")

    # 1. Présence des sections et des clés
    for section, cles in CLES_OBLIGATOIRES.items():
        if section not in config:
            raise ValueError(f"Section manquante dans config.yaml : « {section} ».")
        for cle in cles:
            if cle not in config[section]:
                raise ValueError(f"Clé manquante dans config.yaml : « {section}.{cle} ».")

    # 2. Années
    donnees = config["donnees"]
    if donnees["annee_debut"] >= donnees["annee_fin"]:
        raise ValueError("donnees.annee_debut doit être strictement avant donnees.annee_fin.")


def charger_config(chemin=None):
    """Lit config.yaml, le vérifie et le renvoie sous forme de dictionnaire.

    chemin : chemin d'un fichier de configuration ; par défaut <racine>/config.yaml.
    """
    chemin = Path(chemin) if chemin is not None else racine_projet() / "config.yaml"
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {chemin}")
    with open(chemin, encoding="utf-8") as fichier:
        config = yaml.safe_load(fichier)
    verifier_config(config)
    return config


def chemin_donnees(config, cle):
    """Chemin complet d'un fichier ou dossier de données déclaré dans config.yaml.

    cle : « dossier_brutes », « dossier_extraites », « dossier_preparees »
          ou « fichier_sources ».
    """
    if cle not in config["donnees"]:
        raise KeyError(f"donnees.{cle} n'existe pas dans config.yaml.")
    return racine_projet() / config["donnees"][cle]


def encodage_de_l_annee(config, annee):
    """Encodage des CSV de la SAE pour une année, tel que déclaré dans config.yaml.

    donnees.encodage_csv avant donnees.encodage_csv_utf8_a_partir_de, UTF-8 à partir
    de cette année. Ces valeurs sont démontrées fichier par fichier par
    scripts/01_extraire.py (src.qualite.encodages_valides).
    """
    donnees = config["donnees"]
    if annee >= donnees["encodage_csv_utf8_a_partir_de"]:
        return "utf-8"
    return donnees["encodage_csv"]
