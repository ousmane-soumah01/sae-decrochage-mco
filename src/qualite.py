"""Contrôles de qualité des fichiers de la SAE.

Ces fonctions MESURENT, elles ne corrigent rien.
  - Encodage de chaque fichier, à vérifier avant toute lecture (un fichier lu dans
    le mauvais encodage ne provoque aucune erreur, mais abîme les accents en silence).
  - Audit des tables lues (scripts/02_audit_qualite.py) : structure, puis les autres
    contrôles au fur et à mesure.
"""

import pandas as pd

from src.nettoyage import vers_nombre

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
