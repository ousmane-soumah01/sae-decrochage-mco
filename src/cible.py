"""La cible : décrochage d'activité à un an (règles : docs/decisions.md).

Pour l'instant : les passages t -> t+1, la référence nationale, et le décrochage :
évolution de l'établissement < référence - 15 points (config.yaml : cible.ecart_points).

Exemple (passage 2023 -> 2024, activités en journées-équivalentes, seuil 1 000) :
    A  124 000 -> 129 500      B  22 500 -> 16 900      C  6 700 -> 6 140
    D    9 300 -> absent       E     325 -> 325 (sous le seuil : hors étude)
    référence = (129 500 + 16 900 + 6 140) / (124 000 + 22 500 + 6 700) - 1
              = 152 540 / 153 200 - 1 = -0,43 %   (D, absent en 2024, n'y entre pas)
    B : 16 900 / 22 500 - 1 = -24,89 %, écart -24,46 points -> décrochage
    C :  6 140 /  6 700 - 1 =  -8,36 %, écart  -7,93 points -> pas de décrochage
"""

from src.activite import est_eligible


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
    ils sont vides sinon, et decrochage vaut alors faux (le cas des établissements
    inactifs en t+1 est traité à part).
    decrochage : ecart_points < -cible.ecart_points (inégalité stricte).
    """
    p = passages.copy()
    p["evolution"] = (p["activite_t1"] / p["activite_t"] - 1).where(p["actif_t1"])
    p["reference"] = p["t"].map(reference_ponderee(p))
    p["ecart_points"] = 100 * (p["evolution"] - p["reference"])
    p["decrochage"] = p["ecart_points"] < -config["cible"]["ecart_points"]
    return p
