"""Tests unitaires de src/chargement.py : chaque fonction est testée seule.

Aucun test n'utilise Internet : le téléchargement est simulé (monkeypatch).
"""

import hashlib
import io

import pytest

from src import chargement
from src.chargement import (
    Md5Incorrect,
    etat_archive,
    lire_sources,
    md5_fichier,
    recuperer_archive,
    telecharger_fichier,
)

pytestmark = pytest.mark.unitaire

CONTENU = b"contenu d'une fausse archive"
MD5_CONTENU = hashlib.md5(CONTENU).hexdigest()
EN_TETE = "annee;fichier;octets;md5;derniere_modif_serveur;url\n"


def ecrire_sources(chemin, lignes):
    chemin.write_text(EN_TETE + "".join(lignes), encoding="utf-8")
    return chemin


def faux_serveur(monkeypatch, contenu):
    """Remplace urllib.request.urlopen : renvoie toujours `contenu`, et compte les appels."""
    appels = []

    def urlopen(requete, timeout=None):
        appels.append(requete.full_url)
        return io.BytesIO(contenu)

    monkeypatch.setattr(chargement.urllib.request, "urlopen", urlopen)
    return appels


def une_source(md5=MD5_CONTENU):
    return {"annee": 2013, "fichier": "sae_2013.7z", "octets": len(CONTENU),
            "md5": md5, "url": "https://exemple.invalid/sae_2013.7z"}


# --- lire_sources -------------------------------------------------------------

def test_lire_sources_lit_et_convertit_les_types(tmp_path):
    f = ecrire_sources(tmp_path / "s.csv", [
        f"2013;a.7z;100;{MD5_CONTENU.upper()};date;https://x/a\n",
        f"2014;b.7z;200;{MD5_CONTENU};date;https://x/b\n",
    ])
    sources = lire_sources(f)
    assert len(sources) == 2
    assert sources[0]["annee"] == 2013 and sources[0]["octets"] == 100
    assert sources[0]["md5"] == MD5_CONTENU          # mis en minuscules


def test_lire_sources_signale_un_fichier_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        lire_sources(tmp_path / "absent.csv")


def test_lire_sources_refuse_des_colonnes_inattendues(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("annee;fichier\n2013;a.7z\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Colonnes inattendues"):
        lire_sources(f)


def test_lire_sources_refuse_une_liste_vide(tmp_path):
    with pytest.raises(ValueError, match="aucune archive"):
        lire_sources(ecrire_sources(tmp_path / "s.csv", []))


def test_lire_sources_refuse_une_annee_en_double(tmp_path):
    ligne = f"2013;a.7z;100;{MD5_CONTENU};date;https://x/a\n"
    with pytest.raises(ValueError, match="deux fois"):
        lire_sources(ecrire_sources(tmp_path / "s.csv", [ligne, ligne]))


def test_lire_sources_lit_le_vrai_fichier_du_projet():
    from src.config import charger_config, chemin_donnees
    sources = lire_sources(chemin_donnees(charger_config(), "fichier_sources"))
    assert [s["annee"] for s in sources] == list(range(2013, 2026))
    assert all(len(s["md5"]) == 32 for s in sources)


# --- md5_fichier --------------------------------------------------------------

def test_md5_fichier_valeur_connue(tmp_path):
    f = tmp_path / "abc.txt"
    f.write_bytes(b"abc")
    assert md5_fichier(f) == "900150983cd24fb0d6963f7d28e17f72"   # md5 de référence de « abc »


def test_md5_fichier_ne_depend_pas_de_la_taille_des_blocs(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(CONTENU * 1000)
    assert md5_fichier(f, taille_bloc=7) == md5_fichier(f) == hashlib.md5(CONTENU * 1000).hexdigest()


# --- etat_archive -------------------------------------------------------------

def test_etat_archive_absente(tmp_path):
    assert etat_archive(tmp_path / "rien.7z", MD5_CONTENU) == "absente"


def test_etat_archive_ok(tmp_path):
    f = tmp_path / "a.7z"
    f.write_bytes(CONTENU)
    assert etat_archive(f, MD5_CONTENU.upper()) == "ok"


def test_etat_archive_md5_different(tmp_path):
    f = tmp_path / "a.7z"
    f.write_bytes(b"autre chose")
    assert etat_archive(f, MD5_CONTENU) == "md5_different"


# --- telecharger_fichier ------------------------------------------------------

def test_telecharger_fichier_ecrit_le_contenu(tmp_path, monkeypatch):
    faux_serveur(monkeypatch, CONTENU)
    destination = tmp_path / "sous_dossier" / "a.7z"
    telecharger_fichier("https://exemple.invalid/a.7z", destination)
    assert destination.read_bytes() == CONTENU
    assert not (tmp_path / "sous_dossier" / "a.7z.partiel").exists()


def test_telecharger_fichier_ne_laisse_rien_en_cas_d_erreur(tmp_path, monkeypatch):
    def urlopen(requete, timeout=None):
        raise OSError("réseau coupé")
    monkeypatch.setattr(chargement.urllib.request, "urlopen", urlopen)
    destination = tmp_path / "a.7z"
    with pytest.raises(OSError):
        telecharger_fichier("https://exemple.invalid/a.7z", destination)
    assert list(tmp_path.iterdir()) == []         # ni fichier final, ni fichier .partiel


# --- recuperer_archive --------------------------------------------------------

def test_recuperer_archive_ne_retelecharge_pas_une_archive_correcte(tmp_path, monkeypatch):
    (tmp_path / "sae_2013.7z").write_bytes(CONTENU)
    appels = faux_serveur(monkeypatch, CONTENU)
    assert recuperer_archive(une_source(), tmp_path) == "deja_presente"
    assert appels == []                            # aucun téléchargement


def test_recuperer_archive_telecharge_une_archive_absente(tmp_path, monkeypatch):
    appels = faux_serveur(monkeypatch, CONTENU)
    assert recuperer_archive(une_source(), tmp_path) == "telechargee"
    assert appels == ["https://exemple.invalid/sae_2013.7z"]
    assert (tmp_path / "sae_2013.7z").read_bytes() == CONTENU


def test_recuperer_archive_remplace_une_archive_abimee(tmp_path, monkeypatch):
    (tmp_path / "sae_2013.7z").write_bytes(b"archive abimee")
    faux_serveur(monkeypatch, CONTENU)
    assert recuperer_archive(une_source(), tmp_path) == "telechargee"
    assert md5_fichier(tmp_path / "sae_2013.7z") == MD5_CONTENU


def test_recuperer_archive_refuse_un_md5_incorrect_et_supprime_le_fichier(tmp_path, monkeypatch):
    faux_serveur(monkeypatch, b"version differente publiee par la DREES")
    with pytest.raises(Md5Incorrect, match="attendu"):
        recuperer_archive(une_source(), tmp_path)
    assert not (tmp_path / "sae_2013.7z").exists()
