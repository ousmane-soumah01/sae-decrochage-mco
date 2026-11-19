"""Construction du panel : une ligne par établissement (fi) et par année (an) de la table MCO.

Étapes (chacune comptée dans le tableau des contrôles) :
  1. empilement des 13 années de la table MCO, quantités utiles seulement ;
  2. conversion des quantités en nombres (décision 3) ;
  3. capacités vides mises à 0 quand l'activité correspondante est nulle (décision 1) ;
  4. incohérences repérées par des indicateurs 0/1, jamais corrigées (décision 2) ;
  5. identité de l'établissement (table ID), jointe sur (fi, an) sans perdre ni dupliquer
     de ligne, avec la région actuelle retrouvée à partir du département (décision 4) ;
  6. indicateurs 0/1 tirés des autres tables (pédiatrie, gériatrie, unité neurovasculaire,
     urgences, SMR) : 1 si l'établissement y a la ligne demandée, 0 sinon (décision 5).
Décisions : docs/nettoyage_donnees.md.

Puis les variables explicatives de la table de modélisation (variables_explicatives) :
seulement ce qui est connu en t, jamais ce qui vient de t+1 (VARIABLES_INTERDITES).
"""

import numpy as np
import pandas as pd

from src.chargement import empiler_table
from src.nettoyage import (
    capacite_vide_a_zero,
    convertir_quantites,
    correspondance_region,
    indicateurs_incoherences,
    joindre_gauche,
    valeurs_non_numeriques,
    vers_nombre,
)

CLE = ["fi", "an"]
DISCIPLINES = ["med", "chi", "obs", "mco"]

# Quantités de la table MCO gardées dans le panel (converties en nombres) : lits, journées
# exploitables, journées, séjours, séjours de 0 jour, places, venues, par discipline, et séances.
QUANTITES_MCO = [f"{mesure}_{d}" for mesure in ("lit", "jli", "jou", "sejhc", "sej0", "pla", "sejhp")
                 for d in DISCIPLINES] + ["sea_mco"]

# Colonnes d'identité prises dans la table ID (reg sert seulement à retrouver la région actuelle).
COLONNES_ID = ["fi", "an", "rs", "fi_ej", "stjr", "catr", "dep", "reg"]

# Réforme territoriale : la table ID code les nouvelles régions à partir de 2016.
ANNEE_NOUVELLES_REGIONS = 2016

# Indicateurs 0/1 tirés des autres tables (décision 5) : nom -> (table, condition sur la ligne).
# Libellés DREES (« Liste variables SAE 2024 ») : sped = service ou unité pédiatrique,
# uger = service ou unité de médecine gériatrique, unv = unité neurovasculaire,
# autsu = structure d'urgences autorisée sur le site, gde = type d'activité SSR (SSR_TOT : total),
# sejhc = séjours en hospitalisation complète.
INDICATEURS = {
    "a_pediatrie": ("MCOPED", lambda t: t["sped"] == "1"),
    "a_geriatrie": ("MCOGER", lambda t: t["uger"] == "1"),
    "a_unv": ("MCOAVC", lambda t: t["unv"] == "1"),
    "a_urgences": ("URGENCES", lambda t: t["autsu"] == "1"),
    "a_smr": ("SSR_SMR", lambda t: (t["gde"] == "SSR_TOT") & (vers_nombre(t["sejhc"]) > 0)),
}

# Capacité -> activité correspondante, pour la décision 1.
CAPACITES = {f"{c}_{d}": f"{a}_{d}" for d in DISCIPLINES
             for c, a in (("lit", "jou"), ("jli", "jou"), ("pla", "sejhp"))}


def indicateur(table, condition, nom):
    """Table (fi, an, nom = 1) des lignes qui vérifient la condition, sans doublon."""
    lignes = table.loc[condition, CLE].drop_duplicates()
    return lignes.assign(**{nom: 1})


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

    # 5. Identité et région actuelle (décision 4)
    identite = empiler_table(config, "ID", annees, dossier_extraites)[COLONNES_ID]
    identite["an"] = identite["an"].astype(int)
    region = correspondance_region(identite[identite["an"] >= ANNEE_NOUVELLES_REGIONS])
    identite["reg_actuelle"] = identite["dep"].map(region)
    sans_region = sorted(identite.loc[identite["reg_actuelle"].isna(), "dep"].unique())
    if sans_region:
        raise ValueError(f"Départements sans région actuelle : {sans_region}")
    noter("identite", "départements", len(region))
    noter("identite", "régions actuelles", len(set(region.values())))
    mco, sans_id = joindre_gauche(mco, identite.drop(columns="reg"), CLE, "MCO <- ID")
    noter("jointures", "lignes MCO absentes de ID", sans_id)

    # 6. Indicateurs tirés des autres tables (décision 5) : absent de la table -> 0
    for nom, (table, condition) in INDICATEURS.items():
        source = empiler_table(config, table, annees, dossier_extraites)
        source["an"] = source["an"].astype(int)
        mco, _ = joindre_gauche(mco, indicateur(source, condition(source), nom), CLE, f"MCO <- {table}")
        mco[nom] = mco[nom].fillna(0).astype(int)
        noter("indicateurs", f"{nom} = 1", int(mco[nom].sum()))
        if nom == "a_smr":
            sans_sejour = source[(source["gde"] == "SSR_TOT") & ~(vers_nombre(source["sejhc"]) > 0)]
            noter("indicateurs", "lignes SSR_TOT sans séjour en complète (non comptées)", len(sans_sejour))

    mco = mco.sort_values(CLE).reset_index(drop=True)
    noter("panel", "lignes", len(mco))
    noter("panel", "colonnes", mco.shape[1])
    return mco, controles


# --- Variables explicatives de la table de modélisation ---------------------------------

# Colonnes qui ne doivent jamais servir à prédire : identifiants, et tout ce qui vient de t+1
# (src/cible.py) ou qui sert à construire la cible.
VARIABLES_INTERDITES = [
    "fi", "fi_ej", "rs", "an", "t", "t1", "y", "classe", "activite_t", "activite_t1", "fi_ej_t1",
    "actif_t1", "evolution", "reference", "ecart_points", "decrochage", "reapparu_plus_tard",
    "fermeture_en_cours",
    "compensation", "cite_fusion_scission", "reprise_capacites", "reprise_meme_ej",
    "restructuration_probable", "changement_de_groupe",
]

# Variables catégorielles : gardées en texte dans la table, encodées en 0/1 dans chaque modèle.
CATEGORIELLES = ["stjr", "catr", "reg_actuelle"]

# Modalités rares (moins de 100 lignes à l'entraînement, scripts/07_exploration.py), regroupées pour
# qu'aucune ne reçoive son propre coefficient. Chaque catégorie rare n'a qu'un statut juridique :
# on les regroupe par statut.
REGROUPEMENT_CATR = {
    "PUB3": "PUB_autres", "PUB10": "PUB_autres",
    "PLU5": "PLU_autres", "PLU7": "PLU_autres", "PLU8": "PLU_autres", "PLU10": "PLU_autres",
    "PNL3": "PNL_autres", "PNL7": "PNL_autres", "PNL8": "PNL_autres",
}
# Régions d'outre-mer (Guadeloupe, Martinique, Guyane, La Réunion, Mayotte) : une seule modalité.
REGIONS_OUTRE_MER = ["01", "02", "03", "04", "06"]

# Taux d'occupation au-delà duquel la déclaration est impossible (journées, lits ou journées
# exploitables mal déclarés) : indicateur inc_occupation_superieure_a_1_5.
OCCUPATION_IMPOSSIBLE = 1.5


def ratio(numerateur, denominateur):
    """numerateur / denominateur, vide quand le dénominateur est nul ou vide."""
    denominateur = denominateur.where(denominateur > 0)
    return numerateur / denominateur


def variables_explicatives(panel):
    """Variables connues en t, une ligne par (fi, an) du panel.

    panel : sortie de construire_panel avec la colonne activite (src.activite.calculer_activite).
    Renvoie fi, an et : les 29 quantités, l'activité et son logarithme, les ratios, la place du
    site dans son entité juridique (sites actifs en t), l'identité (texte) et les indicateurs.
    Un ratio dont le dénominateur est nul ou vide reste vide. Taux d'occupation > 1,5 :
    inc_occupation_superieure_a_1_5. Modalités rares regroupées : REGROUPEMENT_CATR (catr) et
    REGIONS_OUTRE_MER (reg_actuelle = « outre_mer »).
    """
    v = panel[CLE + QUANTITES_MCO + ["activite"]].copy()
    v["log_activite"] = np.log1p(v["activite"])
    v["taux_occupation_mco"] = ratio(panel["jou_mco"], panel["jli_mco"])
    v["inc_occupation_superieure_a_1_5"] = (v["taux_occupation_mco"] > OCCUPATION_IMPOSSIBLE).astype(int)
    v["part_partielle_mco"] = ratio(panel["sejhp_mco"], panel["sejhc_mco"] + panel["sejhp_mco"])
    v["duree_moyenne_sejour_mco"] = ratio(panel["jou_mco"], panel["sejhc_mco"] - panel["sej0_mco"])
    for d in DISCIPLINES[:3]:
        v[f"part_journees_{d}"] = ratio(panel[f"jou_{d}"], panel["jou_mco"])

    actifs = panel[panel["activite"] > 0]
    entite = actifs.groupby(["fi_ej", "an"]).agg(sites_entite=("fi", "size"),
                                                 activite_entite=("activite", "sum")).reset_index()
    groupe = panel[CLE + ["fi_ej"]].merge(entite, on=["fi_ej", "an"], how="left")
    v["sites_entite"] = groupe["sites_entite"].fillna(0).astype(int).to_numpy()
    v["part_site_dans_entite"] = ratio(panel["activite"], pd.Series(groupe["activite_entite"].to_numpy(),
                                                                     index=panel.index))

    autres = CATEGORIELLES + list(INDICATEURS) + [c for c in panel.columns if c.startswith("inc_")]
    v = pd.concat([v, panel[autres]], axis=1)
    v["catr"] = v["catr"].replace(REGROUPEMENT_CATR)
    v["reg_actuelle"] = v["reg_actuelle"].where(~v["reg_actuelle"].isin(REGIONS_OUTRE_MER), "outre_mer")
    return v


def verifier_sans_fuite(colonnes):
    """Arrête le programme si une colonne interdite (identifiant ou t+1) est parmi les variables."""
    interdites = sorted(set(colonnes) & set(VARIABLES_INTERDITES))
    if interdites:
        raise ValueError(f"Variables interdites parmi les variables explicatives : {interdites}")
