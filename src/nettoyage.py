"""Conversions appliquées aux données de la SAE.

Chaque fonction fait une seule chose, et ne modifie jamais les données en
silence : ce qu'elle change doit pouvoir être compté et documenté.
"""

import pandas as pd


def vers_nombre(serie):
    """Convertit une colonne lue en texte en nombres.

    - La virgule décimale française est acceptée (« 12,5 » -> 12.5).
    - Les espaces sont retirés (« 1 234 » -> 1234).
    - Une case vide reste manquante (NaN).
    - Une valeur qui n'est pas un nombre devient manquante (NaN) :
      utiliser valeurs_non_numeriques() pour savoir lesquelles.
    """
    texte = serie.astype("string").str.replace(r"\s", "", regex=True).str.replace(",", ".", regex=False)
    return pd.to_numeric(texte, errors="coerce").astype("float64")


def valeurs_non_numeriques(serie):
    """Valeurs non vides qui ne se convertissent pas en nombre (avec leur nombre d'apparitions)."""
    non_vides = serie.dropna()
    echecs = non_vides[vers_nombre(non_vides).isna()]
    return echecs.value_counts()


def convertir_quantites(table, colonnes):
    """Copie de la table où les colonnes de quantités sont converties en nombres.

    Les colonnes de codes (fi, dep...) ne sont pas touchées (décision 3).
    """
    copie = table.copy()
    for colonne in colonnes:
        if colonne in copie:
            copie[colonne] = vers_nombre(copie[colonne])
    return copie


def capacite_vide_a_zero(table, capacite, activite):
    """Décision 1 : une capacité vide vaut 0 quand l'activité correspondante est nulle.

    Exemple : lit_mco vide et jou_mco nul -> lit_mco = 0 (pas de lit).
    Si l'activité est positive, la capacité reste vide (valeur inconnue).
    Renvoie (table, nombre de cases mises à 0, nombre de cases laissées vides).
    """
    vide = table[capacite].isna()
    active = pd.to_numeric(table[activite], errors="coerce").fillna(0) > 0
    a_zero, laissees_vides = vide & ~active, vide & active
    copie = table.copy()
    copie.loc[a_zero, capacite] = 0.0
    return copie, int(a_zero.sum()), int(laissees_vides.sum())


def indicateurs_incoherences(table):
    """Décision 2 : indicateurs (0/1) des incohérences de l'activité MCO, sans rien corriger.

    Les colonnes de quantités doivent déjà être numériques ; une case vide compte comme 0.
    """
    hc, hc0 = table["sejhc_mco"].fillna(0), table["sej0_mco"].fillna(0)
    jou = table["jou_mco"].fillna(0)
    return pd.DataFrame({
        # Les séjours de 0 jour font partie des séjours d'hospitalisation complète
        "inc_sej0_superieur_a_sejhc": (hc0 > hc).astype(int),
        # Un séjour d'au moins une nuit compte au moins une journée
        "inc_jou_trop_bas": (jou < hc - hc0).astype(int),
        "inc_lits_zero_avec_journees": ((table["lit_mco"] == 0) & (jou > 0)).astype(int),
    }, index=table.index)
