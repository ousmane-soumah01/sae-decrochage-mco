"""Tests unitaires de src/chargement.py : chaque fonction est testée seule.

Aucun test n'utilise Internet : le téléchargement est simulé (monkeypatch).
"""

import hashlib
import io

import pandas as pd
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


# =============================================================================
# Partie 2 : extraction des tables
# =============================================================================

import py7zr  # noqa: E402

from src.chargement import extraire_tables, tables_attendues, trouver_csv  # noqa: E402

BASE = "SAE 2025 Bases statistiques - formats SAS-CSV/Bases statistiques"
TABLES_CONFIG = ["ID", "MCO", "MCOPED", "SSR", "SMR"]


def fausse_archive(chemin, fichiers):
    """Crée une archive .7z ; fichiers = {chemin_dans_archive: contenu (texte)}."""
    with py7zr.SevenZipFile(chemin, "w") as z:
        for nom, contenu in fichiers.items():
            z.writestr(contenu.encode("cp1252"), nom)
    return chemin


# --- tables_attendues ---------------------------------------------------------

def test_tables_attendues_avant_2025_prend_ssr():
    assert tables_attendues(TABLES_CONFIG, 2024) == ["ID", "MCO", "MCOPED", "SSR"]


def test_tables_attendues_a_partir_de_2025_prend_smr():
    assert tables_attendues(TABLES_CONFIG, 2025) == ["ID", "MCO", "MCOPED", "SMR"]


# --- trouver_csv --------------------------------------------------------------

NOMS = [
    f"{BASE}/Bases CSV/MCO_2025r.csv",
    f"{BASE}/Bases CSV ancienne casse/MCO_2025r.csv",
    f"{BASE}/Bases CSV/MCOPED_2025a.csv",
    f"{BASE}/Bases CSV/MCOSURV_2025r.csv",
]


def test_trouver_csv_ignore_le_dossier_ancienne_casse():
    assert trouver_csv(NOMS, "MCO", 2025) == f"{BASE}/Bases CSV/MCO_2025r.csv"


def test_trouver_csv_accepte_la_lettre_a():
    assert trouver_csv(NOMS, "MCOPED", 2025).endswith("MCOPED_2025a.csv")


def test_trouver_csv_ne_confond_pas_mco_et_mcosurv():
    # « MCO » ne doit pas attraper « MCOSURV » : le motif exige « MCO_2025 ».
    assert trouver_csv(NOMS, "MCO", 2025).endswith("/MCO_2025r.csv")


def test_trouver_csv_signale_une_table_absente():
    with pytest.raises(ValueError, match="introuvable"):
        trouver_csv(NOMS, "ID", 2025)


def test_trouver_csv_signale_une_table_en_double():
    noms = NOMS + [f"{BASE}/Bases CSV/MCO_2025a.csv"]
    with pytest.raises(ValueError, match="plusieurs fois"):
        trouver_csv(noms, "MCO", 2025)


# --- extraire_tables ----------------------------------------------------------

def test_extraire_tables_extrait_a_plat_les_seules_tables_demandees(tmp_path):
    archive = fausse_archive(tmp_path / "sae_2025.7z", {
        f"{BASE}/Bases CSV/ID_2025r.csv": "FI;AN\n010000024;2025\n",
        f"{BASE}/Bases CSV/MCO_2025r.csv": "FI;AN;JOU_MCO\n010000024;2025;100\n",
        f"{BASE}/Bases CSV ancienne casse/MCO_2025r.csv": "fi;an;jou_mco\n010000024;2025;100\n",
        f"{BASE}/Bases CSV/URGENCES_2025r.csv": "FI;AN\n010000024;2025\n",
    })
    fichiers = extraire_tables(archive, 2025, ["ID", "MCO"], tmp_path / "extraites")
    dossier = tmp_path / "extraites" / "2025"
    assert set(fichiers) == {"ID", "MCO"}
    assert sorted(p.name for p in dossier.iterdir()) == ["ID_2025r.csv", "MCO_2025r.csv"]
    assert fichiers["MCO"].read_text(encoding="cp1252").startswith("FI;AN;JOU_MCO")   # pas l'ancienne casse


def test_extraire_tables_signale_une_table_absente(tmp_path):
    archive = fausse_archive(tmp_path / "sae_2025.7z", {f"{BASE}/Bases CSV/ID_2025r.csv": "FI\n1\n"})
    with pytest.raises(ValueError, match="MCO 2025 introuvable"):
        extraire_tables(archive, 2025, ["ID", "MCO"], tmp_path / "extraites")


# =============================================================================
# Partie 3 : lecture d'une table extraite
# =============================================================================

from src.chargement import lire_table, trouver_table_extraite  # noqa: E402


# --- lire_table ---------------------------------------------------------------

def test_lire_table_garde_le_zero_de_tete_et_les_accents(tmp_path):
    f = tmp_path / "ID_2024r.csv"
    f.write_bytes("FI;rs;An\n010000024;CH CŒUR DE L’AIN;2024\n".encode("cp1252"))
    t = lire_table(f)
    assert list(t.columns) == ["fi", "rs", "an"]          # mis en minuscules
    assert t.loc[0, "fi"] == "010000024"                   # zéro de tête conservé (texte)
    assert t.loc[0, "rs"] == "CH CŒUR DE L’AIN"            # Œ et ’ lus en Windows-1252


def test_lire_table_seule_une_case_vide_est_manquante(tmp_path):
    f = tmp_path / "MCO_2024r.csv"
    f.write_bytes("FI;JOU_MCO;LIBELLE\n1;;NA\n".encode("cp1252"))
    t = lire_table(f)
    assert pd.isna(t.loc[0, "jou_mco"])                    # case vide -> manquante
    assert t.loc[0, "libelle"] == "NA"                     # « NA » reste du texte


def test_lire_table_refuse_des_colonnes_en_double(tmp_path):
    f = tmp_path / "MCO_2024r.csv"
    f.write_bytes("FI;fi\n1;1\n".encode("cp1252"))
    with pytest.raises(ValueError, match="colonnes en double"):
        lire_table(f)


# --- octets_invalides ---------------------------------------------------------

from src.chargement import octets_invalides  # noqa: E402


def test_octets_invalides_fichier_lisible(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes("PRÉSIDENT".encode("cp1252"))
    assert octets_invalides(f, "cp1252") == []


def test_octets_invalides_trouve_une_faute_de_frappe(tmp_path):
    # « PR\x90ESIDENT » : 0x90 n'existe pas en Windows-1252
    f = tmp_path / "a.csv"
    f.write_bytes(b"DU PR\x90ESIDENT MAGNAUD")
    assert octets_invalides(f, "cp1252") == [5]


def test_octets_invalides_compte_chaque_octet(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes(b"\x90ab\x81cd\x8f")
    assert octets_invalides(f, "cp1252") == [0, 3, 6]


def test_octets_invalides_detecte_un_fichier_windows_lu_en_utf8(tmp_path):
    f = tmp_path / "a.csv"
    f.write_bytes("é".encode("cp1252"))          # un seul octet 0xE9, invalide en UTF-8
    assert octets_invalides(f, "utf-8") == [0]


# --- lire_table : encodage et octets illisibles -------------------------------

def test_lire_table_strict_refuse_un_octet_illisible(tmp_path):
    f = tmp_path / "ID_2016r.csv"
    f.write_bytes(b"FI;ADR\n1;PR\x90ESIDENT\n")
    with pytest.raises(UnicodeDecodeError):
        lire_table(f)


def test_lire_table_replace_remplace_un_octet_illisible(tmp_path):
    f = tmp_path / "ID_2016r.csv"
    f.write_bytes(b"FI;ADR\n1;PR\x90ESIDENT\n")
    t = lire_table(f, erreurs="replace")
    assert t.loc[0, "adr"] == "PR\ufffdESIDENT"   # « � »
    assert len(t) == 1


def test_lire_table_lit_un_fichier_utf8(tmp_path):
    f = tmp_path / "ID_2025r.csv"
    f.write_bytes("FI;RS\n010000024;CENTRE HOSPITALIER DE BOURG-EN-BRESSE é\n".encode("utf-8"))
    t = lire_table(f, encodage="utf-8")
    assert t.loc[0, "rs"].endswith("é")


# --- trouver_table_extraite ---------------------------------------------------

def test_trouver_table_extraite_trouve_la_lettre_a(tmp_path):
    (tmp_path / "2013").mkdir()
    (tmp_path / "2013" / "MCOPED_2013a.csv").write_text("FI\n", encoding="cp1252")
    (tmp_path / "2013" / "MCO_2013r.csv").write_text("FI\n", encoding="cp1252")
    assert trouver_table_extraite(tmp_path, "MCOPED", 2013).name == "MCOPED_2013a.csv"
    assert trouver_table_extraite(tmp_path, "MCO", 2013).name == "MCO_2013r.csv"


def test_trouver_table_extraite_signale_une_table_absente(tmp_path):
    with pytest.raises(FileNotFoundError, match="01_extraire"):
        trouver_table_extraite(tmp_path, "MCO", 2013)
