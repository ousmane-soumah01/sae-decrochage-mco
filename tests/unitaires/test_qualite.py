"""Tests unitaires de src/qualite.py : chaque fonction est testée seule."""

import pandas as pd
import pytest

from src.qualite import (
    CANDIDATS_ENCODAGE,
    absents,
    annees_incoherentes,
    controles_activite_mco,
    doublons_cle,
    encodages_valides,
    evaluer_encodage,
    finess_invalides,
    presence_colonnes,
    profil_types,
    resume_presence,
    taux_manquants,
)

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


# --- presence_colonnes / resume_presence --------------------------------------

COLONNES = {2013: ["fi", "an", "lit_mco"], 2014: ["fi", "an"], 2015: ["fi", "an", "lit_mco", "jli_mco"]}


def test_presence_colonnes_tableau_colonne_par_annee():
    p = presence_colonnes(COLONNES)
    assert list(p.columns) == [2013, 2014, 2015]
    assert p.loc["lit_mco"].tolist() == [True, False, True]
    assert p.loc["fi"].all()


def test_resume_presence_repere_les_colonnes_irregulieres():
    r = resume_presence(presence_colonnes(COLONNES)).set_index("colonne")
    assert r.loc["fi", "presente_toutes_annees"]
    assert r.loc["lit_mco", "annees_absentes"] == "2014"
    assert (r.loc["jli_mco", "premiere"], r.loc["jli_mco", "nb_annees"]) == (2015, 1)


# --- taux_manquants -------------------------------------------------------------

def test_taux_manquants():
    t = pd.DataFrame({"a": ["1", None, None, "4"], "b": ["1", "2", "3", "4"]})
    assert taux_manquants(t).to_dict() == {"a": 0.5, "b": 0.0}


# --- profil_types -----------------------------------------------------------------

def test_profil_types_classe_chaque_colonne():
    t = pd.DataFrame({
        "num": ["1", "2,5", "3"],
        "texte": ["a", "b", "c"],
        "mixte": ["1", "2", "x"],
        "vide": [None, None, None],
    })
    p = profil_types(t).set_index("colonne")
    assert p.loc["num", "type"] == "numerique"
    assert p.loc["texte", "type"] == "texte"
    assert p.loc["mixte", "type"] == "mixte"
    assert p.loc["mixte", "part_numerique"] == pytest.approx(2 / 3, abs=1e-4)
    assert p.loc["vide", "type"] == "vide"


# --- doublons_cle -----------------------------------------------------------------

def test_doublons_cle_renvoie_toutes_les_lignes_concernees():
    t = pd.DataFrame({"fi": ["1", "1", "2"], "gde": ["A", "B", "A"]})
    assert len(doublons_cle(t, ["fi"])) == 2            # fi « 1 » en double
    assert doublons_cle(t, ["fi", "gde"]).empty         # (fi, gde) unique


# --- finess_invalides -------------------------------------------------------------

def test_finess_invalides():
    s = pd.Series(["010000024", "2A0000017", "2B1234567", "10000024", "01000002X", None])
    assert finess_invalides(s).tolist() == [False, False, False, True, True, True]


# --- annees_incoherentes ----------------------------------------------------------

def test_annees_incoherentes():
    t = pd.DataFrame({"an": ["2015", "2015", "2014"]})
    assert annees_incoherentes(t, 2015) == 1


# --- absents --------------------------------------------------------------------

def test_absents():
    a = pd.Series(["1", "2", "3", "3", None])
    b = pd.Series(["2"])
    assert absents(a, b) == ["1", "3"]


# --- controles_activite_mco -----------------------------------------------------

def test_controles_activite_mco_compte_chaque_regle():
    # Chaque ligne n'enfreint qu'UNE règle (la valeur négative est sur sejhp_mco :
    # un nombre de séjours négatif ferait aussi passer sej0 > sejhc).
    t = pd.DataFrame({
        #           normal  vide   sej0>hc  jou trop bas  journées sans séjour  négatif
        "sejhc_mco": ["10",  None,  "2",     "10",         "0",                  "1"],
        "sej0_mco":  ["2",   None,  "5",     "0",          "0",                  "0"],
        "jou_mco":   ["30",  None,  "0",     "5",          "7",                  "1"],
        "sejhp_mco": ["4",   None,  "0",     "0",          "0",                  "-1"],
    })
    c = controles_activite_mco(t)
    assert c["lignes"] == 6
    assert c["activite_entierement_vide"] == 1
    assert c["sej0_superieur_a_sejhc"] == 1
    assert c["jou_inferieur_aux_sejours_non_nuls"] == 1   # 5 journées pour 10 séjours d'au moins une nuit
    assert c["journees_sans_sejour"] == 1
    assert c["valeur_negative"] == 1


def test_controles_activite_mco_ligne_correcte_ne_declenche_rien():
    t = pd.DataFrame({"sejhc_mco": ["10"], "sej0_mco": ["2"], "jou_mco": ["30"], "sejhp_mco": ["4"]})
    c = controles_activite_mco(t)
    assert all(v == 0 for k, v in c.items() if k != "lignes")
