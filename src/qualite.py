"""Contrôles de qualité des fichiers de la SAE.

Ces fonctions MESURENT, elles ne corrigent rien.
  - Encodage de chaque fichier, à vérifier avant toute lecture (un fichier lu dans
    le mauvais encodage ne provoque aucune erreur, mais abîme les accents en silence).
  - Audit des tables lues (scripts/02_audit_qualite.py) : structure, puis les autres
    contrôles au fur et à mesure.
"""

import pandas as pd

from src.nettoyage import vers_nombre

# Numéro FINESS : 9 caractères ; pour la Corse, le département s'écrit 2A ou 2B.
MOTIF_FINESS = r"(\d{9}|2[AB]\d{7})"

# Encodages candidats : ceux qu'un fichier français produit sous Windows, Mac ou DOS
# peut raisonnablement utiliser.
CANDIDATS_ENCODAGE = ["utf-8", "utf-16", "cp1252", "latin-1", "iso8859_15", "cp850", "mac_roman"]

# Caractères non ASCII acceptables dans un texte français : lettres accentuées
# et signes typographiques. Tout autre caractère non ASCII trahit un mauvais encodage.
CARACTERES_FRANCAIS = set("ÀÂÄÆÇÉÈÊËÎÏÔÖŒÙÛÜŸàâäæçéèêëîïôöœùûüÿ°’‘–—“”«»…€¨·\xa0")


def evaluer_encodage(contenu, encodage):
    """Lit des octets dans un encodage et juge le résultat, sur trois critères.

      1. octets illisibles : combien d'octets n'existent pas dans cet encodage ;
      2. en-tête correct : la première ligne contient les colonnes AN et FI ;
      3. texte plausible : aucun caractère de contrôle invisible, et tous les
         caractères non ASCII sont des lettres ou signes français.
    """
    texte = contenu.decode(encodage, errors="replace").lstrip("﻿")
    illisibles = texte.count("�")
    premiere_ligne = texte.split("\n", 1)[0]
    colonnes = [c.strip().upper() for c in premiere_ligne.split(";")]
    controle = sum(1 for ch in texte
                   if (ord(ch) < 32 and ch not in "\n\r\t") or 0x7F <= ord(ch) <= 0x9F)
    etrangers = [ch for ch in texte
                 if ord(ch) > 127 and ch != "�" and ch not in CARACTERES_FRANCAIS]
    return {
        "encodage": encodage,
        "octets_illisibles": illisibles,
        "entete_correcte": "AN" in colonnes and "FI" in colonnes,
        "caracteres_controle": controle,
        "caracteres_non_francais": len(etrangers),
        "exemples": "".join(dict.fromkeys(etrangers))[:10],
    }


def encodages_valides(chemin, candidats=CANDIDATS_ENCODAGE, octets_illisibles_toleres=0):
    """Essaie tous les encodages candidats sur un fichier et renvoie ceux qui marchent.

    Un encodage « marche » si l'en-tête est correct, le texte est plausible, et il
    n'y a pas plus de `octets_illisibles_toleres` octets illisibles. Quand on tolère
    des octets illisibles, on ne garde que les encodages qui en ont le MOINS : sur un
    fichier Windows avec une faute de frappe, Windows-1252 bute sur 1 octet, l'UTF-8
    sur chaque accent.
    Un fichier sans accent marche avec presque tous les candidats : c'est normal,
    il se lit à l'identique.
    """
    with open(chemin, "rb") as fichier:
        contenu = fichier.read()
    retenus = {}
    for encodage in candidats:
        e = evaluer_encodage(contenu, encodage)
        if (e["entete_correcte"] and e["caracteres_controle"] == 0
                and e["caracteres_non_francais"] == 0
                and e["octets_illisibles"] <= octets_illisibles_toleres):
            retenus[encodage] = e["octets_illisibles"]
    if not retenus:
        return []
    minimum = min(retenus.values())
    return [encodage for encodage, illisibles in retenus.items() if illisibles == minimum]


# --- Structure : présence des colonnes selon les années ----------------------

def presence_colonnes(colonnes_par_annee):
    """Tableau colonne x année : True si la colonne existe cette année-là.

    colonnes_par_annee : {annee: liste des noms de colonnes}.
    """
    toutes = sorted({c for colonnes in colonnes_par_annee.values() for c in colonnes})
    annees = sorted(colonnes_par_annee)
    return pd.DataFrame({a: [c in set(colonnes_par_annee[a]) for c in toutes] for a in annees},
                        index=pd.Index(toutes, name="colonne"))


def resume_presence(presence):
    """Pour chaque colonne : nombre d'années, première et dernière année, années absentes."""
    annees = list(presence.columns)
    lignes = []
    for colonne, presente in presence.iterrows():
        vues = [a for a in annees if presente[a]]
        absentes = [a for a in annees if not presente[a]]
        lignes.append({"colonne": colonne, "nb_annees": len(vues),
                       "premiere": min(vues), "derniere": max(vues),
                       "presente_toutes_annees": not absentes,
                       "annees_absentes": " ".join(map(str, absentes))})
    return pd.DataFrame(lignes)


# --- Valeurs manquantes ----------------------------------------------------------

def taux_manquants(table):
    """Part de cases vides de chaque colonne (entre 0 et 1)."""
    return table.isna().mean()


# --- Types : une colonne contient-elle des nombres, du texte, ou les deux ? --------

def profil_types(table, seuil=0.99):
    """Pour chaque colonne : cases non vides, part convertible en nombre, type.

    type : « vide » (aucune valeur), « numerique » (au moins `seuil` des valeurs
    sont des nombres), « texte » (aucune), « mixte » (entre les deux : à examiner).
    """
    lignes = []
    for colonne in table.columns:
        valeurs = table[colonne].dropna()
        if valeurs.empty:
            lignes.append({"colonne": colonne, "non_vides": 0, "part_numerique": None, "type": "vide"})
            continue
        part = vers_nombre(valeurs).notna().mean()
        nature = "numerique" if part >= seuil else ("texte" if part == 0 else "mixte")
        lignes.append({"colonne": colonne, "non_vides": len(valeurs),
                       "part_numerique": round(part, 4), "type": nature})
    return pd.DataFrame(lignes)


# --- Clés et cohérence entre tables ---------------------------------------------

def doublons_cle(table, cle):
    """Lignes dont la clé (par exemple ["fi"] ou ["fi", "gde"]) apparaît plusieurs fois."""
    return table[table.duplicated(cle, keep=False)]


def finess_invalides(serie):
    """Masque des numéros FINESS mal formés (vides compris)."""
    return ~serie.fillna("").str.fullmatch(MOTIF_FINESS)


def annees_incoherentes(table, annee):
    """Nombre de lignes dont la colonne an ne vaut pas l'année du fichier."""
    return int((table["an"] != str(annee)).sum())


def absents(fi_a, fi_b):
    """FINESS présents dans fi_a mais absents de fi_b (liste triée, sans doublon)."""
    return sorted(set(fi_a.dropna()) - set(fi_b.dropna()))


# --- Règles de cohérence de l'activité MCO --------------------------------------

def controles_activite_mco(table):
    """Compte les lignes de la table MCO qui enfreignent une règle de cohérence.

    Renvoie un dictionnaire {règle: nombre de lignes}. Rien n'est corrigé.
    Une case vide compte comme 0 dans les comparaisons.
    """
    n = {c: vers_nombre(table[c]) for c in ("sejhc_mco", "sej0_mco", "jou_mco", "sejhp_mco")}
    hc, hc0 = n["sejhc_mco"].fillna(0), n["sej0_mco"].fillna(0)
    jou, hp = n["jou_mco"].fillna(0), n["sejhp_mco"].fillna(0)
    toutes_vides = pd.concat(list(n.values()), axis=1).isna().all(axis=1)
    return {
        "lignes": len(table),
        "activite_entierement_vide": int(toutes_vides.sum()),
        "aucun_sejour": int(((hc + hp) == 0).sum()),
        "valeur_negative": int(pd.concat([s < 0 for s in n.values()], axis=1).any(axis=1).sum()),
        # Les séjours de 0 jour font partie des séjours d'hospitalisation complète
        "sej0_superieur_a_sejhc": int((hc0 > hc).sum()),
        # Un séjour d'au moins une nuit compte au moins une journée : jou >= sejhc - sej0
        "jou_inferieur_aux_sejours_non_nuls": int((jou < hc - hc0).sum()),
        "journees_sans_sejour": int(((jou > 0) & (hc == 0)).sum()),
    }
