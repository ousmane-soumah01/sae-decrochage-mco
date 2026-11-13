"""Construction du panel : une ligne par établissement (fi) et par année (an) de la table MCO.

Étapes (chacune comptée dans le tableau des contrôles) :
  1. empilement des 13 années de la table MCO, quantités utiles seulement ;
  2. conversion des quantités en nombres (décision 3) ;
  3. capacités vides mises à 0 quand l'activité correspondante est nulle (décision 1) ;
  4. incohérences repérées par des indicateurs 0/1, jamais corrigées (décision 2).
Décisions : docs/nettoyage_donnees.md.
"""

from src.chargement import empiler_table
from src.nettoyage import (
    capacite_vide_a_zero,
    convertir_quantites,
    indicateurs_incoherences,
    valeurs_non_numeriques,
)

CLE = ["fi", "an"]
DISCIPLINES = ["med", "chi", "obs", "mco"]

# Quantités de la table MCO gardées dans le panel (converties en nombres) : lits, journées
# exploitables, journées, séjours, séjours de 0 jour, places, venues, par discipline, et séances.
QUANTITES_MCO = [f"{mesure}_{d}" for mesure in ("lit", "jli", "jou", "sejhc", "sej0", "pla", "sejhp")
                 for d in DISCIPLINES] + ["sea_mco"]

# Capacité -> activité correspondante, pour la décision 1.
CAPACITES = {f"{c}_{d}": f"{a}_{d}" for d in DISCIPLINES
             for c, a in (("lit", "jou"), ("jli", "jou"), ("pla", "sejhp"))}


def construire_panel(config, dossier_extraites, annees):
    """Construit le panel MCO et renvoie (panel, controles).

    controles : liste de dictionnaires {etape, mesure, valeur} qui documente chaque
    transformation (valeurs non numériques, cases mises à 0, lignes repérées...).
    """
    controles = []

    def noter(etape, mesure, valeur):
        controles.append({"etape": etape, "mesure": mesure, "valeur": valeur})

    # 1. Empilement, quantités utiles seulement
    mco = empiler_table(config, "MCO", annees, dossier_extraites)
    mco = mco[CLE + QUANTITES_MCO]
    noter("mco", "lignes", len(mco))

    # 2. Conversion en nombres (décision 3), en comptant ce qui ne serait pas un nombre
    for colonne in QUANTITES_MCO:
        noter("conversion", f"{colonne} : valeurs non numériques", int(valeurs_non_numeriques(mco[colonne]).sum()))
    mco = convertir_quantites(mco, QUANTITES_MCO)
    mco["an"] = mco["an"].astype(int)

    # 3. Capacités vides (décision 1)
    for capacite, activite in CAPACITES.items():
        mco, mises_a_zero, laissees_vides = capacite_vide_a_zero(mco, capacite, activite)
        noter("capacites", f"{capacite} vide mis à 0", mises_a_zero)
        noter("capacites", f"{capacite} vide laissé vide ({activite} > 0)", laissees_vides)

    # 4. Incohérences (décision 2) : repérées, jamais corrigées
    mco["inc_lits_vides_avec_journees"] = (mco["lit_mco"].isna() & (mco["jou_mco"] > 0)).astype(int)
    mco["inc_places_vides_avec_venues"] = (mco["pla_mco"].isna() & (mco["sejhp_mco"] > 0)).astype(int)
    incoherences = indicateurs_incoherences(mco)
    for colonne in incoherences:
        mco[colonne] = incoherences[colonne]
    for colonne in [c for c in mco.columns if c.startswith("inc_")]:
        noter("incoherences", colonne, int(mco[colonne].sum()))

    mco = mco.sort_values(CLE).reset_index(drop=True)
    noter("panel", "lignes", len(mco))
    noter("panel", "colonnes", mco.shape[1])
    return mco, controles
