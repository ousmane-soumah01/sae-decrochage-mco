"""Mesure de l'activité MCO, en journées-équivalentes (décision : docs/decisions.md).

    activité = journées de complète + p x (venues de partielle + séjours de 0 jour)

avec p = 0,5 (config.yaml : activite.poids_partielle et activite.poids_sejours_0_jour).
Une venue de partielle dure une journée ; un séjour de complète de 0 jour compte
0 journée dans les journées, il est donc compté comme une venue de partielle.

Exemple : 100 000 journées, 40 000 venues, 8 000 séjours de 0 jour
          -> 100 000 + 0,5 x (40 000 + 8 000) = 124 000 journées-équivalentes.

Un établissement n'entre dans l'étude que si son activité atteint le seuil des
petits établissements (config.yaml : perimetre.seuil_petits_etablissements).
"""

import pandas as pd


def calculer_activite(table, config):
    """Activité MCO en journées-équivalentes, une valeur par ligne.

    Les colonnes doivent déjà être numériques (src.nettoyage.convertir_quantites).
    Une composante vide compte pour 0 si au moins une autre est renseignée ;
    si les trois sont vides, l'activité est inconnue (NaN).
    """
    a = config["activite"]
    journees, venues, sejours_0 = (pd.to_numeric(table[a[c]], errors="coerce")
                                   for c in ("colonne_journees_complete", "colonne_venues_partielle",
                                             "colonne_sejours_0_jour"))
    activite = (journees.fillna(0)
                + a["poids_partielle"] * venues.fillna(0)
                + a["poids_sejours_0_jour"] * sejours_0.fillna(0))
    toutes_vides = pd.concat([journees, venues, sejours_0], axis=1).isna().all(axis=1)
    return activite.mask(toutes_vides)

def est_eligible(activite, config):
    """Vrai si l'activité atteint le seuil des petits établissements ; faux si elle est inconnue."""
    return activite >= config["perimetre"]["seuil_petits_etablissements"]
