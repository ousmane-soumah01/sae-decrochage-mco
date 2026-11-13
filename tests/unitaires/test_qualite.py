"""Tests unitaires de src/qualite.py : chaque fonction est testée seule."""

import pytest

from src.qualite import CANDIDATS_ENCODAGE, encodages_valides, evaluer_encodage

pytestmark = pytest.mark.unitaire


# Un fichier Windows-1252 avec « ’ » et « Œ » (octets 0x92 et 0x8C) : c'est ce qui
# sépare Windows-1252 de Latin-1 et d'ISO-8859-15.
TEXTE = "BOR;AN;FI;RS\nID;2024;1;CH L’ÉTANG DE CRICQUEBŒUF\n"


def ecrire_fichier(tmp_path, contenu, nom="ID_2024r.csv"):
    f = tmp_path / nom
    f.write_bytes(contenu)
    return f


def test_les_7_candidats():
    assert CANDIDATS_ENCODAGE == ["utf-8", "utf-16", "cp1252", "latin-1",
                                  "iso8859_15", "cp850", "mac_roman"]


def test_fichier_windows_seul_cp1252_marche(tmp_path):
    f = ecrire_fichier(tmp_path, TEXTE.encode("cp1252"))
    assert encodages_valides(f) == ["cp1252"]


def test_fichier_utf8_seul_utf8_marche(tmp_path):
    f = ecrire_fichier(tmp_path, TEXTE.encode("utf-8"), "ID_2025r.csv")
    assert encodages_valides(f) == ["utf-8"]


def test_fichier_sans_accent_marche_avec_tous_sauf_utf16(tmp_path):
    f = ecrire_fichier(tmp_path, b"BOR;AN;FI\nMCO;2016;010000024\n", "MCO_2016r.csv")
    assert encodages_valides(f) == ["utf-8", "cp1252", "latin-1", "iso8859_15", "cp850", "mac_roman"]


def test_sans_octet_0x80_0x9f_windows_latin1_et_iso_marchent_tous(tmp_path):
    # Pas de « ’ » ni de « Œ » : les trois donnent exactement le même texte.
    # « ç » et « à » sont nécessaires : avec seulement « ÉÈÔ », Mac Roman donne « …»‘ »,
    # des signes français, et passerait.
    f = ecrire_fichier(tmp_path, "BOR;AN;FI\nSSR;2024;ÉÈÔ çà\n".encode("cp1252"), "SSR_2024r.csv")
    assert encodages_valides(f) == ["cp1252", "latin-1", "iso8859_15"]


def test_faute_de_frappe_isolee_marche_seulement_a_un_octet_pres(tmp_path):
    # Un octet qui n'existe dans aucun encodage (0x90), au milieu d'un fichier Windows-1252.
    contenu = ("BOR;AN;FI;ADR\nID;2016;1;DU PR".encode("cp1252") + b"\x90"
               + "ESIDENT ÉTÉ çà\n".encode("cp1252"))
    f = ecrire_fichier(tmp_path, contenu, "ID_2016r.csv")
    assert encodages_valides(f) == []
    assert encodages_valides(f, octets_illisibles_toleres=10) == ["cp1252"]


# Le détail des trois critères, sur le fichier Windows

def test_evaluer_utf8_bute_sur_les_accents():
    e = evaluer_encodage(TEXTE.encode("cp1252"), "utf-8")
    assert e["octets_illisibles"] == 3                     # ’, É et Œ : un octet seul, interdit en UTF-8


def test_evaluer_latin1_donne_des_caracteres_de_controle():
    e = evaluer_encodage(TEXTE.encode("cp1252"), "latin-1")
    assert e["octets_illisibles"] == 0 and e["caracteres_controle"] == 2    # ’ et Œ invisibles


def test_evaluer_cp850_donne_des_caracteres_non_francais():
    e = evaluer_encodage(TEXTE.encode("cp1252"), "cp850")
    assert e["caracteres_non_francais"] > 0


def test_evaluer_utf16_a_un_entete_illisible():
    e = evaluer_encodage(TEXTE.encode("cp1252"), "utf-16")
    assert not e["entete_correcte"]


def test_evaluer_cp1252_sur_un_fichier_utf8_donne_du_charabia():
    e = evaluer_encodage(TEXTE.encode("utf-8"), "cp1252")
    assert e["caracteres_non_francais"] > 0               # « â€™ », « Ã‰ »...
