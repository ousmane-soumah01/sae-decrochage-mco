"""Découpage dans le temps : lignes évaluées, test final et plis de validation par année.

Une ligne est un passage t -> t+1 (src/cible.py). Tout se découpe sur l'année t de la ligne :
le modèle apprend sur les années passées et il est validé sur l'année suivante.
"""

import numpy as np


def lignes_evaluees(classes, config):
    """Passages dont la cible est connue (y = 0 ou 1), sans les restructurations probables
    si cible.retirer_restructurations est vrai, et sans les sites qui ne déclarent ni lit ni
    place MCO en t si perimetre.capacite_mco_requise est vrai (règle connue en t)."""
    garde = classes["y"].notna()
    if config["cible"]["retirer_restructurations"]:
        garde &= classes["restructuration_probable"] == 0
    if config["perimetre"]["capacite_mco_requise"] and "sans_capacite_mco_t" in classes:
        garde &= classes["sans_capacite_mco_t"] == 0
    return classes[garde]


def separer_test(lignes, annees_test, passages_exclus, colonne="t"):
    """Sépare les lignes en (entrainement, test, exclues), selon l'année t.

    annees_test     : années t du test final ;
    passages_exclus : années t mises à part, ni à l'entraînement ni au test.
    """
    annees_test, passages_exclus = set(annees_test), set(passages_exclus)
    if annees_test & passages_exclus:
        raise ValueError(f"Années à la fois au test et exclues : {sorted(annees_test & passages_exclus)}")
    exclue = lignes[colonne].isin(passages_exclus)
    test = lignes[colonne].isin(annees_test)
    return lignes[~exclue & ~test], lignes[test], lignes[exclue]


def plis_par_annee(annees, annees_min_entrainement=1):
    """Plis de validation croisée à fenêtre croissante, une année de validation par pli.

    annees : année t de chaque ligne, dans l'ordre des lignes (pas besoin de trier).
    Pour chaque année v (sauf les premières) : entraînement sur toutes les lignes des années < v,
    validation sur les lignes de l'année v. Le premier pli a au moins annees_min_entrainement
    années d'entraînement (années présentes dans les lignes).
    Renvoie une liste de couples (indices d'entraînement, indices de validation), utilisable
    comme cv= dans scikit-learn.
    """
    if annees_min_entrainement < 1:
        raise ValueError("annees_min_entrainement doit valoir au moins 1")
    annees = np.asarray(annees)
    distinctes = np.unique(annees)
    plis = []
    for rang, v in enumerate(distinctes):
        if rang >= annees_min_entrainement:
            plis.append((np.flatnonzero(annees < v), np.flatnonzero(annees == v)))
    return plis
