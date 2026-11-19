"""La cible : décrochage d'activité à un an (règles : docs/decisions.md).

Pour chaque établissement au-dessus du seuil en t et son passage t -> t+1 :
  1. référence = évolution nationale pondérée (somme des activités t+1 / somme en t - 1),
     sur les établissements actifs en t+1 ;
  2. décrochage : évolution de l'établissement < référence - 15 points ;
  3. sortie : établissement absent ou sans activité en t+1, ou qui ferme en cours d'année
     (0 lit et 0 place MCO en t+1 et plus aucune activité ensuite) ; une sortie compte comme
     un décrochage (y = 1), sauf s'il réapparaît plus tard (activité en t+1 inconnue) ;
  4. restructuration probable : y = 1, et (au moins 50 % de la perte retrouvée dans les
     autres sites du groupe au-delà de la référence, ou site cité dans une fusion ou une
     scission déclarée par un autre établissement, ou lits et places repris par un autre site
     du même département en t+1).

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

# Capacités MCO : fermeture en cours d'année, et reprise par un autre site.
CAPACITES_MCO = ["lit_mco", "pla_mco"]


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


def fermetures_en_cours(passages, panel, config):
    """Vrai si le site, actif en t+1, déclare 0 lit et 0 place MCO en t+1 alors qu'il en avait en t,
    et n'a plus aucune activité après t+1 : il a fermé pendant l'année t+1 (la SAE déclare l'activité
    faite avant la fermeture et les capacités au 31 décembre).

    Faux si t+1 est la dernière année du panel (la suite n'est pas connue), si la règle est
    désactivée (cible.fermeture_en_cours_est_une_sortie) ou si le panel n'a pas les capacités.
    """
    faux = pd.Series(False, index=passages.index)
    if not config["cible"]["fermeture_en_cours_est_une_sortie"] or not set(CAPACITES_MCO) <= set(panel.columns):
        return faux
    capacite = dict(zip(zip(panel["fi"], panel["an"]), panel[CAPACITES_MCO].fillna(0).sum(axis=1)))
    capacite_t = np.array([capacite.get(k, np.nan) for k in zip(passages["fi"], passages["t"])])
    capacite_t1 = np.array([capacite.get(k, np.nan) for k in zip(passages["fi"], passages["t1"])])
    derniere_active = passages["fi"].map(panel[panel["activite"] > 0].groupby("fi")["an"].max()).to_numpy()
    t1 = passages["t1"].to_numpy()
    return pd.Series(passages["actif_t1"].to_numpy() & (capacite_t1 == 0) & (capacite_t > 0)
                     & (derniere_active == t1) & (t1 < panel["an"].max()), index=passages.index)


def classer(passages, panel, config):
    """Classe chaque passage : stable, decrochage, sortie ou inconnue ; et calcule y.

    sortie   : inactif en t+1 (absent ou activité nulle), et jamais réapparu ensuite ;
               ou décrochage d'un site qui ferme en cours d'année t+1 (fermetures_en_cours) ;
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
    p["fermeture_en_cours"] = fermetures_en_cours(p, panel, config).astype(int)
    p.loc[(p["fermeture_en_cours"] == 1) & (p["classe"] == "decrochage"), "classe"] = "sortie"
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


def reprises_de_capacites(classes, panel, config):
    """Reprise plausible des lits et places d'un site à y = 1 par un autre site, en t+1.

    Capacité = lits + places MCO (vide : 0 ; absent : 0). Règles de config.yaml › cible.reprise :
      - le site perd au moins perte_min et au moins part_perte_min de ses capacités ;
      - un autre site gagne la même capacité entre t et t+1, à tolerance_absolue ou
        tolerance_relative près, et au plus candidats_max sites sont dans ce cas en France ;
      - l'un d'eux est dans le même département et gagne au moins part_activite_min de
        l'activité perdue.
    reprise_meme_ej : ce repreneur est dans la même entité juridique (en t ou en t+1) ;
    information seule (regroupement interne ou transfert, sinon reprise par une autre entité).
    Renvoie (fi, t, reprise_capacites, reprise_meme_ej) pour les sites à y = 1 ; aucune ligne
    si la règle est désactivée ou si le panel n'a pas les capacités et le département.
    """
    r = config["cible"]["reprise"]
    lignes = []
    if r["active"] and set(CAPACITES_MCO + ["dep"]) <= set(panel.columns):
        cap = panel[["fi", "an", "fi_ej", "dep"]].copy()
        cap["cap"] = panel[CAPACITES_MCO].fillna(0).sum(axis=1)
        cap["activite"] = panel["activite"].fillna(0)
        for t, cas in classes[classes["y"] == 1].groupby("t"):
            avant = cap[cap["an"] == t].set_index("fi")
            apres = cap[cap["an"] == t + 1].set_index("fi")
            gains = apres.join(avant[["fi_ej", "cap", "activite"]], rsuffix="_avant")
            gains["gain"] = gains["cap"] - gains["cap_avant"].fillna(0)
            gains["gain_activite"] = gains["activite"] - gains["activite_avant"].fillna(0)
            for fi in cas["fi"]:
                if fi not in avant.index:
                    continue
                site = avant.loc[fi]
                perte = site["cap"] - (apres.at[fi, "cap"] if fi in apres.index else 0.0)
                perte_activite = site["activite"] - (apres.at[fi, "activite"] if fi in apres.index else 0.0)
                reprise = meme_ej = False
                if perte >= r["perte_min"] and perte >= r["part_perte_min"] * site["cap"] and perte_activite > 0:
                    tolerance = max(r["tolerance_absolue"], r["tolerance_relative"] * perte)
                    candidats = gains[(gains.index != fi) & ((gains["gain"] - perte).abs() <= tolerance)]
                    repreneurs = candidats[(candidats["dep"] == site["dep"])
                                           & (candidats["gain_activite"] >= r["part_activite_min"] * perte_activite)]
                    if len(candidats) <= r["candidats_max"] and len(repreneurs):
                        reprise = True
                        meme_ej = bool(((repreneurs["fi_ej"] == site["fi_ej"])
                                        | (repreneurs["fi_ej_avant"] == site["fi_ej"])).any())
                lignes.append({"fi": fi, "t": t, "reprise_capacites": int(reprise), "reprise_meme_ej": int(meme_ej)})
    vide = {"fi": pd.Series(dtype=object), "t": pd.Series(dtype="int64"),
            "reprise_capacites": pd.Series(dtype="int64"), "reprise_meme_ej": pd.Series(dtype="int64")}
    return pd.DataFrame(lignes).astype({"t": "int64"}) if lignes else pd.DataFrame(vide)


def restructurations(classes, panel, identite, config):
    """Ajoute compensation, cite_fusion_scission, reprise_capacites, reprise_meme_ej,
    restructuration_probable et changement_de_groupe.

    restructuration_probable : y = 1 et (compensation >= cible.compensation_min, ou site
    cité dans une fusion ou une scission en t ou en t+1, ou capacités reprises par un autre
    site en t+1 : reprises_de_capacites).
    changement_de_groupe : actif en t+1 dans un autre groupe (fi_ej différent) ; information seule.
    """
    c = classes.merge(compensation_dans_le_groupe(classes, panel), on=["fi_ej", "t"], how="left")
    citations = citations_fusion_scission(identite)
    c["cite_fusion_scission"] = [(fi, t) in citations or (fi, t + 1) in citations
                                 for fi, t in zip(c["fi"], c["t"])]
    c = c.merge(reprises_de_capacites(classes, panel, config), on=["fi", "t"], how="left")
    for colonne in ("reprise_capacites", "reprise_meme_ej"):
        c[colonne] = c[colonne].fillna(0).astype(int)
    compense = c["compensation"] >= config["cible"]["compensation_min"]
    c["restructuration_probable"] = ((c["y"] == 1) & (compense | c["cite_fusion_scission"]
                                                      | (c["reprise_capacites"] == 1))).astype(int)
    c["changement_de_groupe"] = (c["actif_t1"] & c["fi_ej_t1"].notna()
                                 & (c["fi_ej_t1"] != c["fi_ej"])).astype(int)
    return c
