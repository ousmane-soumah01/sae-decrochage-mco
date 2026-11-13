"""Tests unitaires de src/config.py : chaque fonction est testée seule."""

import copy

import pytest
import yaml

from src.config import (
    charger_config,
    chemin_donnees,
    encodage_de_l_annee,
    racine_projet,
    verifier_config,
)

pytestmark = pytest.mark.unitaire

# Une petite configuration valide, indépendante du vrai config.yaml.
CONFIG_MINIMALE = {
    "projet": {"nom": "essai", "graine": 42},
    "donnees": {
        "fichier_sources": "donnees/sources_donnees_brutes.csv",
        "dossier_brutes": "donnees/brutes",
        "dossier_extraites": "donnees/extraites",
        "dossier_preparees": "donnees/preparees",
        "annee_debut": 2013,
        "annee_fin": 2025,
        "encodage_csv": "cp1252",
        "encodage_csv_utf8_a_partir_de": 2025,
        "separateur_csv": ";",
        "cle": ["fi", "an"],
        "tables": ["ID", "MCO"],
    },
    "activite": {
        "colonne_journees_complete": "jou_mco",
        "colonne_venues_partielle": "sejhp_mco",
        "colonne_sejours_0_jour": "sej0_mco",
        "poids_partielle": 0.5,
        "poids_sejours_0_jour": 0.5,
    },
    "perimetre": {"seuil_petits_etablissements": 1000},
}


@pytest.fixture
def config():
    """Copie neuve de la configuration minimale pour chaque test."""
    return copy.deepcopy(CONFIG_MINIMALE)


# --- racine_projet ---

def test_racine_projet_contient_config_et_src():
    racine = racine_projet()
    assert (racine / "config.yaml").exists()
    assert (racine / "src" / "config.py").exists()


# --- verifier_config ---

def test_verifier_config_accepte_une_config_valide(config):
    verifier_config(config)          # ne doit rien lever


def test_verifier_config_refuse_autre_chose_qu_un_dictionnaire():
    with pytest.raises(ValueError, match="dictionnaire"):
        verifier_config(None)


def test_verifier_config_signale_une_section_manquante(config):
    del config["donnees"]
    with pytest.raises(ValueError, match="Section manquante.*donnees"):
        verifier_config(config)


def test_verifier_config_signale_une_cle_manquante(config):
    del config["donnees"]["tables"]
    with pytest.raises(ValueError, match="donnees.tables"):
        verifier_config(config)


def test_verifier_config_refuse_des_annees_inversees(config):
    config["donnees"]["annee_debut"] = 2025
    config["donnees"]["annee_fin"] = 2013
    with pytest.raises(ValueError, match="annee_debut"):
        verifier_config(config)


# --- charger_config ---

def test_charger_config_lit_un_fichier_valide(tmp_path, config):
    fichier = tmp_path / "config.yaml"
    fichier.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    assert charger_config(fichier)["donnees"]["annee_debut"] == 2013


def test_charger_config_signale_un_fichier_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_config(tmp_path / "absent.yaml")


def test_charger_config_lit_le_vrai_config_du_projet():
    # Le config.yaml du dépôt doit toujours être valide.
    config = charger_config()
    assert config["donnees"]["annee_debut"] == 2013
    assert config["donnees"]["annee_fin"] == 2025
    assert config["donnees"]["cle"] == ["fi", "an"]
    assert config["activite"]["poids_partielle"] == 0.5
    assert config["perimetre"]["seuil_petits_etablissements"] == 1000


# --- chemin_donnees ---

def test_chemin_donnees_renvoie_un_chemin_sous_la_racine(config):
    assert chemin_donnees(config, "dossier_brutes") == racine_projet() / "donnees" / "brutes"


def test_chemin_donnees_signale_une_cle_inconnue(config):
    with pytest.raises(KeyError):
        chemin_donnees(config, "dossier_inexistant")


# --- encodage_de_l_annee ---

@pytest.mark.parametrize("annee,encodage", [(2013, "cp1252"), (2024, "cp1252"), (2025, "utf-8")])
def test_encodage_de_l_annee_applique_la_configuration(config, annee, encodage):
    # La configuration minimale déclare cp1252, puis UTF-8 à partir de 2025.
    assert encodage_de_l_annee(config, annee) == encodage

@pytest.mark.parametrize("poids", [-0.1, 1.5])
def test_verifier_config_refuse_un_poids_hors_de_0_1(config, poids):
    config["activite"]["poids_partielle"] = poids
    with pytest.raises(ValueError, match="entre 0 et 1"):
        verifier_config(config)


def test_verifier_config_signale_une_cle_d_activite_manquante(config):
    del config["activite"]["poids_sejours_0_jour"]
    with pytest.raises(ValueError, match="activite.poids_sejours_0_jour"):
        verifier_config(config)

def test_verifier_config_refuse_un_seuil_nul(config):
    config["perimetre"]["seuil_petits_etablissements"] = 0
    with pytest.raises(ValueError, match="strictement positif"):
        verifier_config(config)
