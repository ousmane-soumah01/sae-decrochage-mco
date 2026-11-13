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
