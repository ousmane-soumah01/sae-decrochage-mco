"""La cible : décrochage d'activité à un an (règles : docs/decisions.md).

Pour chaque établissement au-dessus du seuil en t et son passage t -> t+1 :
  1. référence = évolution nationale pondérée (somme des activités t+1 / somme en t - 1),
     sur les établissements actifs en t+1 ;
  2. décrochage : évolution de l'établissement < référence - 15 points ;
  3. sortie : établissement absent ou sans activité en t+1 ; une sortie compte comme
     un décrochage (y = 1), sauf s'il réapparaît plus tard (activité en t+1 inconnue) ;
  4. restructuration probable : y = 1, et (au moins 50 % de la perte retrouvée dans les
     autres sites du groupe au-delà de la référence, ou site cité dans une fusion ou une
     scission déclarée par un autre établissement).

Exemple (passage 2023 -> 2024, activités en journées-équivalentes, seuil 1 000) :
    A  124 000 -> 129 500      B  22 500 -> 16 900      C  6 700 -> 6 140
    D    9 300 -> absent       E     325 -> 325 (sous le seuil : hors étude)
    référence = (129 500 + 16 900 + 6 140) / (124 000 + 22 500 + 6 700) - 1
              = 152 540 / 153 200 - 1 = -0,43 %   (D, absent en 2024, n'y entre pas)
    B : 16 900 / 22 500 - 1 = -24,89 %, écart -24,46 points -> décrochage
    C :  6 140 /  6 700 - 1 =  -8,36 %, écart  -7,93 points -> stable
    D : absent en 2024 -> sortie
"""

import numpy as np
import pandas as pd

from src.activite import est_eligible

# Colonnes de la table ID qui citent les établissements concernés par une fusion ou une scission.
COLONNES_FUSION_SCISSION = ["fifu1", "fifu2", "fifu3", "scfu1", "scfu2", "scfu3"]


def construire_passages(panel, config):
    """Une ligne par établissement au-dessus du seuil en t et par passage t -> t+1.

    panel : colonnes fi, an, fi_ej, activite (une ligne par établissement et par année).
    Seules les années t dont l'année t+1 existe dans le panel sont gardées.
    Colonnes ajoutées : activite_t, activite_t1 (vide si absent en t+1), fi_ej_t1,
    actif_t1 (vrai si l'activité en t+1 est strictement positive).
    """
    derniere = panel["an"].max()
    t = panel[est_eligible(panel["activite"], config) & (panel["an"] < derniere)]
    t = t[["fi", "an", "fi_ej", "activite"]].rename(columns={"activite": "activite_t"})

    suivante = panel[["fi", "an", "fi_ej", "activite"]].copy()
    suivante["an"] = suivante["an"] - 1                 # l'année t+1 est rattachée à t
    suivante = suivante.rename(columns={"activite": "activite_t1", "fi_ej": "fi_ej_t1"})

    passages = t.merge(suivante, on=["fi", "an"], how="left", validate="one_to_one")
    passages = passages.rename(columns={"an": "t"})
    passages["t1"] = passages["t"] + 1
    passages["actif_t1"] = passages["activite_t1"] > 0
    return passages


def reference_ponderee(passages):
    """Référence de chaque passage : évolution de la somme des activités.

    Seuls les établissements actifs en t+1 y entrent. Chaque établissement y pèse
    selon son activité. Renvoie une série indexée par t.
    """
    actifs = passages[passages["actif_t1"]]
    sommes = actifs.groupby("t")[["activite_t", "activite_t1"]].sum()
    return sommes["activite_t1"] / sommes["activite_t"] - 1


def ecarts_et_decrochages(passages, config):
    """Ajoute evolution, reference, ecart_points et decrochage aux passages.

    evolution et ecart_points n'ont de sens que pour un établissement actif en t+1 :
    ils sont vides sinon, et decrochage vaut alors faux (les établissements inactifs
    en t+1 sont traités par classer()).
    decrochage : ecart_points < -cible.ecart_points (inégalité stricte).
    """
    p = passages.copy()
    p["evolution"] = (p["activite_t1"] / p["activite_t"] - 1).where(p["actif_t1"])
    p["reference"] = p["t"].map(reference_ponderee(p))
    p["ecart_points"] = 100 * (p["evolution"] - p["reference"])
    p["decrochage"] = p["ecart_points"] < -config["cible"]["ecart_points"]
    return p


def classer(passages, panel, config):
    """Classe chaque passage : stable, decrochage, sortie ou inconnue ; et calcule y.

    sortie   : inactif en t+1 (absent ou activité nulle), et jamais réapparu ensuite ;
    inconnue : absent en t+1 mais réapparu plus tard (trou de déclaration ou fermeture
               temporaire : on ne connaît pas son activité en t+1) ;
    y = 1 pour un décrochage ou une sortie (cible.sortie_est_un_decrochage), 0 pour
    stable, vide pour inconnue.
    """
    p = ecarts_et_decrochages(passages, config)
    annees = panel.groupby("fi")["an"].apply(set).to_dict()
    p["reapparu_plus_tard"] = [not actif and any(a > t1 for a in annees.get(fi, ()))
                               for fi, t1, actif in zip(p["fi"], p["t1"], p["actif_t1"])]
    p["classe"] = "stable"
    p.loc[p["decrochage"], "classe"] = "decrochage"
    p.loc[~p["actif_t1"], "classe"] = "sortie"
    p.loc[p["reapparu_plus_tard"], "classe"] = "inconnue"
    sortie_y = 1 if config["cible"]["sortie_est_un_decrochage"] else 0
    p["y"] = p["classe"].map({"stable": 0, "decrochage": 1, "sortie": sortie_y, "inconnue": np.nan})
    return p


def compensation_dans_le_groupe(classes, panel):
    """Part de la perte des sites à y = 1 retrouvée dans les autres sites du même groupe.

    Pour chaque groupe (fi_ej en t) et chaque passage :
      perte = somme, sur les sites à y = 1, de (activité en t - activité en t+1) ;
      gain  = somme, sur les autres sites actifs du groupe en t+1, de leur activité en t+1
              moins leur activité en t multipliée par (1 + référence) : ce qu'ils ont gagné
              au-delà de la croissance normale ; un site nouveau dans le groupe compte pour
              toute son activité ;
      compensation = gain / perte.
    Renvoie une table (fi_ej, t, compensation).
    """
    reference = classes.groupby("t")["reference"].first()
    actifs = panel[panel["activite"] > 0][["fi", "an", "fi_ej", "activite"]]
    cas = classes[classes["y"] == 1]
    cles_cas = set(zip(cas["fi"], cas["t"]))
    lignes = []
    for (ej, t), cas_groupe in cas.groupby(["fi_ej", "t"]):
        sites_t = actifs[(actifs["fi_ej"] == ej) & (actifs["an"] == t)].set_index("fi")["activite"]
        sites_t1 = actifs[(actifs["fi_ej"] == ej) & (actifs["an"] == t + 1)].set_index("fi")["activite"]
        perte = float((cas_groupe["activite_t"] - cas_groupe["activite_t1"].fillna(0).clip(lower=0)).sum())
        gain = 0.0
        for fi, activite_t1 in sites_t1.items():
            if (fi, t) in cles_cas:
                continue
            gain += activite_t1 - sites_t[fi] * (1 + reference[t]) if fi in sites_t.index else activite_t1
        lignes.append({"fi_ej": ej, "t": t, "compensation": gain / perte if perte > 0 else np.nan})
    return pd.DataFrame(lignes, columns=["fi_ej", "t", "compensation"])


def citations_fusion_scission(identite):
    """Ensemble des (fi, an) cités dans une fusion ou une scission déclarée par un AUTRE établissement.

    identite : table ID empilée (colonnes fi, an et celles de COLONNES_FUSION_SCISSION).
    """
    citations = set()
    for colonne in [c for c in COLONNES_FUSION_SCISSION if c in identite]:
        lignes = identite[identite[colonne].notna() & (identite[colonne] != identite["fi"])]
        citations |= set(zip(lignes[colonne], lignes["an"].astype(int)))
    return citations


def restructurations(classes, panel, identite, config):
    """Ajoute compensation, cite_fusion_scission, restructuration_probable et changement_de_groupe.

    restructuration_probable : y = 1 et (compensation >= cible.compensation_min, ou site
    cité dans une fusion ou une scission en t ou en t+1).
    changement_de_groupe : actif en t+1 dans un autre groupe (fi_ej différent) ; information seule.
    """
    c = classes.merge(compensation_dans_le_groupe(classes, panel), on=["fi_ej", "t"], how="left")
    citations = citations_fusion_scission(identite)
    c["cite_fusion_scission"] = [(fi, t) in citations or (fi, t + 1) in citations
                                 for fi, t in zip(c["fi"], c["t"])]
    compense = c["compensation"] >= config["cible"]["compensation_min"]
    c["restructuration_probable"] = ((c["y"] == 1) & (compense | c["cite_fusion_scission"])).astype(int)
    c["changement_de_groupe"] = (c["actif_t1"] & c["fi_ej_t1"].notna()
                                 & (c["fi_ej_t1"] != c["fi_ej"])).astype(int)
    return c
