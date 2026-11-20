"""Étape 04 : pré-analyse des règles de la cible, AVANT de les fixer.

Lancement, depuis la racine du dépôt (après scripts/03_panel.py) :
    python scripts/04_preanalyse.py

Question 1 : comment mesurer l'activité MCO d'un établissement ?
Mesures candidates comparées (rien n'est fixé dans config.yaml à ce stade) :
  M1  séjours                     sejhc_mco + sejhp_mco
  M2  journées de complète seules jou_mco
  M3  journées-équivalentes       jou_mco + p x (sejhp_mco + sej0_mco), p = 1/3, 1/2 ou 1
Tableaux dans resultats/02_preanalyse/tableaux/ :
  - composantes_nationales.csv : totaux nationaux de chaque composante, par année ;
  - sejours_0_jour.csv         : les séjours de 0 jour comptent-ils dans les journées ?
  - mesures_comparees.csv      : ce que chaque mesure ignore, et sa sensibilité au poids p.

Question 2 : à partir de quelle activité un établissement entre-t-il dans l'étude ?
Activité = mesure retenue à la question 1 (src.activite.calculer_activite). Seuils
candidats comparés (rien n'est fixé dans config.yaml à ce stade) : 0, 365, 1 000, 3 650.
  - seuil_petits_etablissements.csv : établissements écartés et part de l'activité
    nationale qu'ils représentent, par seuil et par année ;
  - instabilite_par_taille.csv : dispersion des évolutions d'une année sur l'autre,
    par tranche d'activité.

Question 3 : quelle référence pour l'évolution « normale » d'une année sur l'autre ?
Établissements au-dessus du seuil en t, présents et actifs en t et t+1. Candidates :
  R1 médiane des évolutions ; R2 moyenne simple ; R3 évolution nationale pondérée
  (somme des activités en t+1 / somme en t - 1).
  - references_candidates.csv et figure references_candidates.png (resultats/02_preanalyse/).

Question 4 : à partir de quel écart à la référence parle-t-on de décrochage ?
Écart = 100 x (évolution de l'établissement - référence pondérée), en points, pour les
établissements au-dessus du seuil en t et actifs en t+1. Seuils candidats : -10, -15,
-20 points (fixes) et la borne de Tukey de l'année (Q1 - 1,5 x écart interquartile).
  - ecarts_par_passage.csv et figure borne_tukey_et_seuils.png.

Question 5 : que faire des établissements inactifs en t+1 (sorties) et des baisses dues à
un transfert d'activité au sein du même groupe (fi_ej : entité juridique) ?
  - sorties_par_passage.csv : établissements inactifs en t+1 (absents ou activité nulle) ;
  - groupes_et_restructurations.csv : pour les décrochages et les sorties, ce que fait le
    groupe entre t et t+1, et le nombre de « restructurations probables » selon la définition ;
  - compensation_dans_le_groupe.csv : part de la perte des sites qui décrochent ou sortent,
    retrouvée dans les autres sites du groupe au-delà de leur croissance normale ;
  - finess_qui_changent.csv : sorties suivies d'un nouveau numéro dans le même groupe,
    établissements réapparus après une absence, sites qui changent de groupe.

Question 6 : comment découper les années pour apprendre, valider et tester ?
(lignes évaluées : y connu, restructurations probables retirées)
  - lignes_par_passage.csv : lignes évaluées, y = 1 et référence nationale par passage ;
  - indice_activite_base_2019.csv : activité des établissements actifs les 13 années,
    quantiles d'un indice 2019 = 100 (creux de 2020 et rattrapage) ;
  - proportion_test.csv : part des lignes et des y = 1 au test selon 1, 2 ou 3 années de test ;
  - plis_timeseriessplit.csv : plis de TimeSeriesSplit comparés aux plis par année ;
  - cases_vides_modele.csv : chaque case vide des lignes évaluées, comparée à la capacité
    ou à l'activité correspondante ;
  - sej0_vides_avec_lits.csv : séjours de 0 jour non renseignés alors que l'établissement a
    des lits dans la discipline (mécanisme d'absence) ;
  - figure covid_et_test.png.

Les questions 6 à 8 utilisent la cible telle qu'elle était à ces décisions : sans la reprise des
capacités (cible.reprise, décidée après la question 7) pour les questions 6 et 7, et sans la
fermeture en cours d'année (cible.fermeture_en_cours_est_une_sortie, décidée après la question 8).

Question 7 : les sorties et les décrochages restants cachent-ils des mouvements de structure ?
(passages dont la cible est connue ; « déjà repéré » = restructuration probable de la question 5)
  - mouvements_declares.csv : part des lignes qui portent chaque mouvement déclaré dans la
    table ID (changement d'entité juridique, modification de l'entité, fusion, scission,
    création, citations) ou observé (fi_ej qui change), comparée aux lignes stables (y = 0) ;
  - reprise_capacites.csv : sites qui perdent au moins SEUIL lits et places MCO (et au moins
    30 % de leurs capacités) ; part dont un autre site du même département gagne la même
    capacité en t+1, avec une hausse d'activité, et au plus 6 sites candidats en France ;
    même test avec les gains de t-1 -> t (placebo : ils ne peuvent pas venir de cette perte) ;
  - reprises_trouvees.csv : chaque passage y = 1 avec une reprise, son repreneur, et si le
    repreneur est dans la même entité juridique (transfert ou regroupement interne) ou non ;
    capacité de l'ancien site en t+1 et années où il est encore dans la SAE après t (un site
    qui garde des lits n'a pas disparu : la règle retenue exige qu'il perde toutes ses capacités).

Question 8 : un site qui déclare 0 lit et 0 place MCO en t+1, mais encore de l'activité, a-t-il
fermé en cours d'année (décrochage ou sortie) ?
  - fermeture_en_cours_bilan.csv : ces passages (capacité > 0 en t), par groupe (stable,
    décrochage gardé ou déjà repéré), selon ce que devient le site : plus jamais actif après
    t+1, actif à nouveau plus tard, ou suite inconnue (t+1 = dernière année) ; activité de t+1
    en % de celle de t ;
  - fermeture_en_cours_par_partie.csv : décrochages et sorties des lignes évaluées, par partie,
    et ce qu'ils deviendraient si les fermetures définitives en cours d'année étaient des sorties ;
  - fermeture_en_cours_cas.csv : chaque passage concerné.

Question 9 : que faire d'un site sans lits ni places MCO en t (fermeture déjà faite pendant l'année t,
ou capacité non saisie) ? Règle examinée, connue en t : n'entrent dans l'étude que les sites qui
déclarent des lits ou des places MCO en t.
  - champ_lignes_zero_capacite.csv : lignes évaluées à 0 lit et 0 place MCO en t, avec leur capacité
    l'année d'avant et d'après, et ce qu'elles sont (passage qui suit une fermeture en cours d'année,
    fermeture pendant l'année t, capacité non saisie) : description, la règle n'utilise pas la suite ;
  - champ_par_partie.csv : lignes hors champ (sorties, décrochages, stables) et lignes restantes, par partie ;
  - classes_y1_rapport.csv : y = 1 réparti en décrochage, fermeture et arrêt du MCO (pour le rapport) ;
  - champ_controle_indicateur.csv : ce qu'annonce inc_lits_zero_avec_journees, toutes lignes et dans le champ.
"""

import copy
import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.model_selection import TimeSeriesSplit  # noqa: E402

from src.activite import calculer_activite, est_eligible  # noqa: E402
from src.chargement import empiler_table  # noqa: E402
from src.cible import (  # noqa: E402
    COLONNES_FUSION_SCISSION,
    classer,
    construire_passages,
    ecarts_et_decrochages,
    reference_ponderee,
    restructurations,
)
from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.decoupage import lignes_evaluees, plis_par_annee, separer_test  # noqa: E402
from src.nettoyage import vers_nombre  # noqa: E402

COMPOSANTES = ["jou_mco", "sejhc_mco", "sej0_mco", "sejhp_mco", "sea_mco"]
POIDS_CANDIDATS = {"1/3": 1 / 3, "1/2": 1 / 2, "1": 1.0}
SEUILS_CANDIDATS = [0, 365, 1000, 3650]
TRANCHES = [0, 100, 365, 1000, 3650, float("inf")]
# Question 6 : candidats examinés (les choix retenus iront dans config.yaml)
ANNEE_BASE_INDICE = 2019                      # dernière année avant le Covid
PASSAGES_COVID = [2019, 2020]                 # années t des passages 2019->2020 et 2020->2021
ANNEES_DE_TEST_CANDIDATES = [1, 2, 3]         # nombre de dernières années t gardées pour le test
DISCIPLINES = ["med", "chi", "obs", "mco"]
CAPACITE_ET_ACTIVITE = [("lit", "jou"), ("jli", "jou"), ("pla", "sejhp")]   # capacité vide -> activité ?
ACTIVITE_ET_CAPACITE = [("jou", "lit"), ("sejhc", "lit"), ("sej0", "lit"), ("sejhp", "pla")]  # et l'inverse
# Question 7 : candidats examinés (les choix retenus iront dans config.yaml)
SEUILS_REPRISE_CANDIDATS = [20, 30]           # perte minimale de lits + places MCO
PART_PERTE_MIN = 0.3                          # et au moins 30 % des capacités du site
TOLERANCE_REPRISE = (2, 0.10)                 # gain égal à la perte, à 2 près ou à 10 % près
CANDIDATS_MAX = 6                             # au-delà, la correspondance peut être le hasard
PART_ACTIVITE_REPRISE = 0.5                   # le repreneur gagne au moins la moitié de l'activité perdue


def evolutions(panel):
    """Évolution de l'activité entre t et t+1 pour les établissements présents et actifs les deux années.

    Renvoie (fi, an = t, activite_t, evolution). Les disparitions ne sont pas des évolutions.
    """
    t = panel.loc[panel["activite"] > 0, ["fi", "an", "activite"]]
    t1 = t.assign(an=t["an"] - 1).rename(columns={"activite": "activite_t1"})
    e = t.merge(t1, on=["fi", "an"], how="inner")
    e["evolution"] = e["activite_t1"] / e["activite"] - 1
    return e.rename(columns={"activite": "activite_t"})


def mesures(panel):
    """Les mesures candidates, une colonne chacune (une case vide compte comme 0)."""
    v = panel[COMPOSANTES].fillna(0)
    m = pd.DataFrame({"M1_sejours": v.sejhc_mco + v.sejhp_mco, "M2_journees": v.jou_mco}, index=panel.index)
    for nom, p in POIDS_CANDIDATS.items():
        m[f"M3_p{nom}"] = v.jou_mco + p * (v.sejhp_mco + v.sej0_mco)
    return m


def main():
    config = charger_config()
    panel = pd.read_parquet(chemin_donnees(config, "dossier_preparees") / "panel_mco.parquet")
    tableaux = racine_projet() / "resultats" / "02_preanalyse" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    # 1. Poids de chaque composante à l'échelle nationale
    nat = panel.groupby("an")[COMPOSANTES].sum()
    nat["part_partielle_dans_sejours_pct"] = 100 * nat.sejhp_mco / (nat.sejhc_mco + nat.sejhp_mco)
    nat["part_sej0_dans_sejhc_pct"] = 100 * nat.sej0_mco / nat.sejhc_mco
    nat["jou_par_sejour_hc_non_nul"] = nat.jou_mco / (nat.sejhc_mco - nat.sej0_mco)
    nat.round(3).to_csv(tableaux / "composantes_nationales.csv")
    print("1. Totaux nationaux (millions) et parts, par année :")
    affichage = (nat[COMPOSANTES] / 1e6).round(2)
    affichage["partielle_%_sejours"] = nat.part_partielle_dans_sejours_pct.round(1)
    affichage["sej0_%_sejhc"] = nat.part_sej0_dans_sejhc_pct.round(1)
    affichage["jou_par_sejour_hc>0j"] = nat.jou_par_sejour_hc_non_nul.round(2)
    print(affichage.to_string())

    # 2. Les séjours de 0 jour comptent-ils dans les journées ?
    v = panel[COMPOSANTES].fillna(0)
    tout_0_jour = (v.sejhc_mco > 0) & (v.sej0_mco == v.sejhc_mco)
    sej0 = pd.DataFrame({
        "lignes_tous_sejours_hc_de_0_jour": [int(tout_0_jour.sum())],
        "dont_journees_nulles": [int((tout_0_jour & (v.jou_mco == 0)).sum())],
        "journees_max_parmi_elles": [float(v.loc[tout_0_jour, "jou_mco"].max()) if tout_0_jour.any() else 0.0],
    })
    sej0.to_csv(tableaux / "sejours_0_jour.csv", index=False)
    print("\n2. Lignes dont TOUS les séjours de complète font 0 jour :")
    print(sej0.to_string(index=False))

    # 3. et 4. Ce que chaque mesure ignore, et sensibilité au poids p
    m = mesures(panel)
    actives = m["M1_sejours"] > 0
    comparaison = pd.DataFrame({
        "lignes_avec_sejours": [int(actives.sum())],
        "M2_nulle_alors_que_partielle": [int((actives & (v.jou_mco == 0) & (v.sejhp_mco > 0)).sum())],
        "part_partielle_dans_M3_p1/2_mediane_pct":
            [round(100 * ((0.5 * (v.sejhp_mco + v.sej0_mco)) / m["M3_p1/2"])[m["M3_p1/2"] > 0].median(), 1)],
        "rapport_M3_p1_sur_M3_p1/3_mediane":
            [round((m["M3_p1"] / m["M3_p1/3"])[m["M3_p1/3"] > 0].median(), 3)],
        "lignes_ou_p1_double_ou_plus_M3_p1/3": [int(((m["M3_p1"] >= 2 * m["M3_p1/3"]) & (m["M3_p1/3"] > 0)).sum())],
        "spearman_M1_M3_p1/2": [round(m.loc[actives, "M1_sejours"].corr(m.loc[actives, "M3_p1/2"], method="spearman"), 3)],
        "spearman_M2_M3_p1/2": [round(m.loc[actives, "M2_journees"].corr(m.loc[actives, "M3_p1/2"], method="spearman"), 3)],
        "lignes_avec_seances": [int((v.sea_mco > 0).sum())],
    })
    comparaison.T.rename(columns={0: "valeur"}).to_csv(tableaux / "mesures_comparees.csv")
    print("\n3-4. Ce que chaque mesure ignore, et sensibilité au poids p (toutes années) :")
    print(comparaison.T.rename(columns={0: "valeur"}).to_string())

    # --- Question 2 : seuil des petits établissements ---------------------------
    panel["activite"] = calculer_activite(panel, config)
    actifs = panel[panel["activite"] > 0]
    total = actifs.groupby("an")["activite"].sum()
    lignes = []
    for seuil in SEUILS_CANDIDATS:
        sous = actifs[actifs["activite"] < seuil]
        for an in sorted(actifs["an"].unique()):
            s_an = sous[sous["an"] == an]
            lignes.append({"seuil": seuil, "an": an, "etablissements_actifs": int((actifs["an"] == an).sum()),
                           "ecartes": len(s_an),
                           "part_activite_ecartee_pct": 100 * s_an["activite"].sum() / total[an]})
    seuils = pd.DataFrame(lignes)
    seuils.round(4).to_csv(tableaux / "seuil_petits_etablissements.csv", index=False)
    print("\n5. Seuil des petits établissements (activité > 0 seulement), par seuil candidat :")
    resume = seuils.groupby("seuil").agg(ecartes_min=("ecartes", "min"), ecartes_max=("ecartes", "max"),
                                         part_activite_max_pct=("part_activite_ecartee_pct", "max"))
    print(resume.round(4).to_string())
    print(f"   (activité nulle : {int((panel['activite'] == 0).sum())} lignes, "
          f"inconnue : {int(panel['activite'].isna().sum())} lignes, écartées quel que soit le seuil)")

    e = evolutions(panel)
    e["tranche"] = pd.cut(e["activite_t"], TRANCHES, right=False)
    instab = e.groupby("tranche", observed=True)["evolution"].agg(
        lignes="size",
        q1=lambda x: x.quantile(0.25), mediane="median", q3=lambda x: x.quantile(0.75),
        part_plus_de_50pct=lambda x: 100 * (x.abs() > 0.5).mean())
    instab["ecart_interquartile_points"] = 100 * (instab["q3"] - instab["q1"])
    instab = instab[["lignes", "ecart_interquartile_points", "part_plus_de_50pct"]]
    instab.round(2).to_csv(tableaux / "instabilite_par_taille.csv")
    print("\n6. Instabilité des évolutions d'une année sur l'autre, par tranche d'activité en t :")
    print(instab.round(1).to_string())

    # --- Question 3 : référence nationale -----------------------------------------
    e = e[est_eligible(e["activite_t"], config)]
    refs = e.groupby("an").apply(lambda g: pd.Series({
        "etablissements": len(g),
        "R1_mediane_pct": 100 * g["evolution"].median(),
        "R2_moyenne_simple_pct": 100 * g["evolution"].mean(),
        "R3_ponderee_pct": 100 * (g["activite_t1"].sum() / g["activite_t"].sum() - 1),
        "part_hausses_plus_de_100pct": 100 * (g["evolution"] > 1).mean(),
        "evolution_max_pct": 100 * g["evolution"].max(),
    }), include_groups=False)
    refs.index = [f"{t}->{t + 1}" for t in refs.index]
    refs.index.name = "passage"
    refs.round(3).to_csv(tableaux / "references_candidates.csv")
    print("\n7. Références candidates par passage (établissements au-dessus du seuil, présents et actifs) :")
    print(refs.round(2).to_string())

    figures = racine_projet() / "resultats" / "02_preanalyse" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for colonne, couleur, nom in (("R1_mediane_pct", "#2a78d6", "R1 médiane"),
                                  ("R2_moyenne_simple_pct", "#eb6834", "R2 moyenne simple"),
                                  ("R3_ponderee_pct", "#1baf7a", "R3 pondérée (évolution nationale)")):
        ax.plot(refs.index, refs[colonne], marker="o", markersize=4, linewidth=2, color=couleur, label=nom)
    ax.axhline(0, color="#6b6a64", linewidth=0.8)
    ax.set_ylabel("évolution de l'activité (%)", color="#6b6a64")
    ax.set_title("Références candidates, par passage t -> t+1", loc="left", fontsize=11)
    ax.grid(axis="y", color="#e6e5e0")
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(figures / "references_candidates.png", dpi=130)
    plt.close(fig)

    # --- Question 4 : écart à la référence et seuil de décrochage ------------------
    passages = construire_passages(panel, config)
    reference = reference_ponderee(passages)
    actifs_t1 = passages[passages["actif_t1"]].copy()
    actifs_t1["ecart_points"] = 100 * (actifs_t1["activite_t1"] / actifs_t1["activite_t"] - 1
                                       - actifs_t1["t"].map(reference))
    lignes = []
    for t, g in actifs_t1.groupby("t"):
        q1, q3 = g["ecart_points"].quantile(0.25), g["ecart_points"].quantile(0.75)
        tukey = q1 - 1.5 * (q3 - q1)
        ligne = {"passage": f"{t}->{t + 1}", "etablissements": len(g),
                 "q1_points": q1, "q3_points": q3, "ecart_interquartile_points": q3 - q1,
                 "borne_tukey_points": tukey}
        for seuil in (10, 15, 20):
            ligne[f"part_sous_moins_{seuil}_pct"] = 100 * (g["ecart_points"] < -seuil).mean()
        ligne["part_sous_tukey_pct"] = 100 * (g["ecart_points"] < tukey).mean()
        lignes.append(ligne)
    ecarts = pd.DataFrame(lignes).set_index("passage")
    ecarts.round(3).to_csv(tableaux / "ecarts_par_passage.csv")
    print("\n8. Écart à la référence (points) et part des établissements sous chaque seuil (%) :")
    print(ecarts.round(1).to_string())

    fig, ax = plt.subplots(figsize=(9, 4.5))
    covid = [i for i, nom in enumerate(ecarts.index) if nom in ("2019->2020", "2020->2021")]
    ax.axvspan(min(covid) - 0.5, max(covid) + 0.5, color="#f1f0ec", zorder=0)
    ax.set_ylim(min(-26, ecarts["borne_tukey_points"].min() - 2), -8)
    ax.text((min(covid) + max(covid)) / 2, -9, "Covid", ha="center", va="top", color="#6b6a64", fontsize=9)
    ax.plot(range(len(ecarts)), ecarts["borne_tukey_points"], marker="o", markersize=4, linewidth=2,
            color="#2a78d6", label="borne de Tukey de l'année (Q1 - 1,5 x EI)")
    for seuil, style in ((10, ":"), (15, "--"), (20, "-.")):
        ax.axhline(-seuil, color="#eb6834", linewidth=1.2, linestyle=style, label=f"seuil fixe -{seuil} points")
    ax.set_xticks(range(len(ecarts)), ecarts.index, rotation=45)
    ax.set_ylabel("écart à la référence (points)", color="#6b6a64")
    ax.set_title("Borne de Tukey de chaque année et seuils fixes candidats", loc="left", fontsize=11)
    ax.grid(axis="y", color="#e6e5e0")
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout()
    fig.savefig(figures / "borne_tukey_et_seuils.png", dpi=130)
    plt.close(fig)

    # --- Question 5 : sorties et restructurations -----------------------------------
    p = ecarts_et_decrochages(passages, config)
    presents_t1 = set(zip(panel["fi"], panel["an"]))
    p["absent_t1"] = [(fi, t1) not in presents_t1 for fi, t1 in zip(p["fi"], p["t1"])]
    sorties = p[~p["actif_t1"]]
    par_passage = p.groupby("t").agg(etablissements=("fi", "size"),
                                     decrochages=("decrochage", "sum"),
                                     inactifs_t1=("actif_t1", lambda x: int((~x).sum())))
    par_passage["dont_absents_t1"] = sorties.groupby("t")["absent_t1"].sum()
    par_passage["dont_presents_activite_nulle"] = par_passage["inactifs_t1"] - par_passage["dont_absents_t1"]
    par_passage["activite_t_mediane_des_inactifs"] = sorties.groupby("t")["activite_t"].median()
    par_passage = par_passage.fillna(0)
    par_passage.index = [f"{t}->{t + 1}" for t in par_passage.index]
    par_passage.round(1).to_csv(tableaux / "sorties_par_passage.csv")
    print("\n9. Établissements inactifs en t+1 (au-dessus du seuil en t), par passage :")
    print(par_passage.round(0).astype(int).to_string())

    # Groupes (fi_ej) : activité des sites actifs, en t et en t+1 (même code fi_ej)
    actifs_panel = panel[panel["activite"] > 0]
    groupes = actifs_panel.groupby(["fi_ej", "an"]).agg(activite_ej=("activite", "sum"),
                                                         sites_ej=("fi", "nunique")).reset_index()
    g_t = groupes.rename(columns={"an": "t", "activite_ej": "activite_ej_t"})
    g_t1 = groupes.assign(t=groupes["an"] - 1)[["fi_ej", "t", "activite_ej"]].rename(
        columns={"activite_ej": "activite_ej_t1"})
    g = g_t.merge(g_t1, on=["fi_ej", "t"], how="left")
    g["groupe_actif_t1"] = g["activite_ej_t1"] > 0
    ref_groupes = (g[g["groupe_actif_t1"]].groupby("t")[["activite_ej_t", "activite_ej_t1"]].sum()
                   .pipe(lambda x: x["activite_ej_t1"] / x["activite_ej_t"] - 1))
    g["ecart_groupe_points"] = 100 * (g["activite_ej_t1"] / g["activite_ej_t"] - 1 - g["t"].map(ref_groupes))
    g["groupe_decroche"] = ~g["groupe_actif_t1"] | (g["ecart_groupe_points"] < -config["cible"]["ecart_points"])

    cas = p[p["decrochage"] | ~p["actif_t1"]].merge(
        g[["fi_ej", "t", "sites_ej", "groupe_decroche"]], on=["fi_ej", "t"], how="left")
    cas["groupe_decroche"] = cas["groupe_decroche"].fillna(True).astype(bool)
    cas["nature"] = cas["decrochage"].map({True: "decrochage", False: "sortie"})
    nouveaux_fi = {(ej, t) for ej, t, fi in zip(panel["fi_ej"], panel["an"], panel["fi"])}
    fi_par_ej_an = panel.groupby(["fi_ej", "an"])["fi"].apply(set).to_dict()
    cas["nouveau_site_dans_le_groupe_t1"] = [
        bool(fi_par_ej_an.get((ej, t + 1), set()) - fi_par_ej_an.get((ej, t), set()))
        for ej, t in zip(cas["fi_ej"], cas["t"])]
    definitions = {
        "groupe_ne_decroche_pas": ~cas["groupe_decroche"],
        "groupe_ne_decroche_pas_et_2_sites_ou_plus": ~cas["groupe_decroche"] & (cas["sites_ej"] >= 2),
        "groupe_ne_decroche_pas_et_(2_sites_ou_plus_ou_sortie)":
            ~cas["groupe_decroche"] & ((cas["sites_ej"] >= 2) | (cas["nature"] == "sortie")),
    }
    lignes = []
    for nature, sous in cas.groupby("nature"):
        ligne = {"nature": nature, "cas": len(sous),
                 "dans_un_groupe_de_2_sites_ou_plus": int((sous["sites_ej"] >= 2).sum()),
                 "nouveau_site_dans_le_groupe_en_t1": int(sous["nouveau_site_dans_le_groupe_t1"].sum())}
        for nom, masque in definitions.items():
            ligne[nom] = int(masque[sous.index].sum())
        lignes.append(ligne)
    restr = pd.DataFrame(lignes).set_index("nature")
    restr.to_csv(tableaux / "groupes_et_restructurations.csv")
    print("\n10. Décrochages et sorties (toutes années) : ce que fait le groupe (fi_ej) entre t et t+1 :")
    print(restr.T.to_string())

    # --- 5b. Compensation dans le groupe ----------------------------------------------
    # Pour chaque groupe et chaque passage : perte totale des sites qui décrochent ou sortent,
    # et gain des autres sites du groupe AU-DELÀ de la référence nationale (croissance normale) ;
    # un site nouveau dans le groupe en t+1 compte pour toute son activité.
    ref = reference_ponderee(passages)
    vus = panel[panel["activite"] > 0][["fi", "an", "fi_ej", "activite"]]
    lignes = []
    cles_cas = set(zip(cas["fi"], cas["t"]))
    for (ej, t), cas_groupe in cas.groupby(["fi_ej", "t"]):
        sites_t = vus[(vus["fi_ej"] == ej) & (vus["an"] == t)].set_index("fi")["activite"]
        sites_t1 = vus[(vus["fi_ej"] == ej) & (vus["an"] == t + 1)].set_index("fi")["activite"]
        perte = float((cas_groupe["activite_t"] - cas_groupe["activite_t1"].fillna(0).clip(lower=0)).sum())
        gain = 0.0
        for fi, a1 in sites_t1.items():
            if (fi, t) in cles_cas:
                continue
            gain += a1 - sites_t.get(fi, 0.0) * (1 + ref[t]) if fi in sites_t.index else a1
        lignes.append({"fi_ej": ej, "t": t, "cas": len(cas_groupe), "sites_t": len(sites_t),
                       "perte": perte, "gain_hors_croissance_normale": gain,
                       "compensation": gain / perte if perte > 0 else float("nan")})
    comp = pd.DataFrame(lignes)
    comp.round(3).to_csv(tableaux / "compensation_dans_le_groupe.csv", index=False)
    cas = cas.merge(comp[["fi_ej", "t", "compensation"]], on=["fi_ej", "t"], how="left")
    print("\n11. Compensation dans le groupe (gain des autres sites au-delà de la référence / perte) :")
    seuils_comp = (0.5, 0.8)
    tableau = []
    for nature, sous in cas.groupby("nature"):
        ligne = {"nature": nature, "cas": len(sous),
                 "groupe_de_2_sites_ou_plus": int((sous["sites_ej"] >= 2).sum()),
                 "compensation_mediane_(2_sites_ou_plus)": round(sous.loc[sous["sites_ej"] >= 2, "compensation"].median(), 2)}
        for seuil in seuils_comp:
            ligne[f"compensation_au_moins_{int(100 * seuil)}pct"] = int((sous["compensation"] >= seuil).sum())
        ligne["groupe_ne_decroche_pas"] = int((~sous["groupe_decroche"]).sum())
        ligne["groupe_ne_decroche_pas_mais_compensation_<50pct"] = int(
            (~sous["groupe_decroche"] & ~(sous["compensation"] >= 0.5)).sum())
        tableau.append(ligne)
    print(pd.DataFrame(tableau).set_index("nature").T.to_string())
    taille = cas[~cas["groupe_decroche"]].assign(
        taille=pd.cut(cas["sites_ej"], [0, 1, 2, 5, 1000], labels=["1 site", "2 sites", "3-5 sites", "6 sites et +"]))
    print("\n    Parmi les cas où le groupe ne décroche pas : taille du groupe et compensation médiane")
    print(taille.groupby("taille", observed=True)["compensation"].agg(["size", "median"]).round(2).to_string())

    # --- 5c. Les FINESS qui changent ---------------------------------------------------
    presence = panel.groupby("fi")["an"].apply(set).to_dict()
    sorties_cas = cas[cas["nature"] == "sortie"].copy()
    sorties_cas["reapparu_plus_tard"] = [any(a > t1 for a in presence[fi]) for fi, t1 in
                                         zip(sorties_cas["fi"], sorties_cas["t1"])]
    sorties_cas["presente_en_t+2"] = [(t1 + 1) in presence[fi] for fi, t1 in zip(sorties_cas["fi"], sorties_cas["t1"])]
    # Nouveau numéro dans le même groupe en t+1, d'activité comparable (entre la moitié et le double)
    successeurs = []
    for _, sortie in sorties_cas.iterrows():
        nouveaux = vus[(vus["fi_ej"] == sortie["fi_ej"]) & (vus["an"] == sortie["t1"])]
        nouveaux = nouveaux.loc[nouveaux["fi"].map(lambda f: sortie["t"] not in presence[f]).astype(bool)]
        comparables = nouveaux[(nouveaux["activite"] >= 0.5 * sortie["activite_t"])
                               & (nouveaux["activite"] <= 2 * sortie["activite_t"])]
        successeurs.append(len(comparables) > 0)
    sorties_cas["successeur_comparable_meme_groupe"] = successeurs
    # Sites qui changent de groupe (fi_ej différent entre t et t+1)
    change_groupe = p[p["actif_t1"] & p["fi_ej_t1"].notna() & (p["fi_ej"] != p["fi_ej_t1"])]
    finess = pd.DataFrame({
        "sorties": [len(sorties_cas)],
        "dont_reapparues_plus_tard": [int(sorties_cas["reapparu_plus_tard"].sum())],
        "dont_presentes_en_t+2": [int(sorties_cas["presente_en_t+2"].sum())],
        "dont_successeur_comparable_dans_le_groupe": [int(sorties_cas["successeur_comparable_meme_groupe"].sum())],
        "passages_avec_changement_de_groupe": [len(change_groupe)],
        "dont_decrochage": [int(change_groupe["decrochage"].sum())],
    }).T.rename(columns={0: "valeur"})
    finess.to_csv(tableaux / "finess_qui_changent.csv")
    print("\n12. Les FINESS qui changent (toutes années) :")
    print(finess.to_string())

    # --- Question 6 : découpage des années ------------------------------------------
    question_6(panel, config, tableaux, figures)

    # --- Question 7 : mouvements de structure ----------------------------------------
    question_7(panel, config, tableaux)

    # --- Question 8 : fermeture en cours d'année ---------------------------------------
    question_8(panel, config, tableaux)

    # --- Question 9 : sites sans capacité MCO en t (règle de champ) ----------------------
    question_9(panel, config, tableaux)

    print(f"\nTableaux écrits dans {tableaux.relative_to(racine_projet())}, figures dans "
          f"{figures.relative_to(racine_projet())}")


def sans_regles_posterieures(config, reprise=True, fermeture=True):
    """Copie de la configuration sans les règles de la cible décidées après une question : la reprise
    des capacités (après la question 7) et la fermeture en cours d'année (après la question 8)."""
    copie = copy.deepcopy(config)
    if reprise:
        copie["cible"]["reprise"]["active"] = False
    if fermeture:
        copie["cible"]["fermeture_en_cours_est_une_sortie"] = False
    return copie


def question_6(panel, config, tableaux, figures):
    """Question 6 : passages Covid, années de test, plis de validation et cases vides."""
    config = sans_regles_posterieures(config)
    annees = range(config["donnees"]["annee_debut"], config["donnees"]["annee_fin"] + 1)
    identite = empiler_table(config, "ID", annees, chemin_donnees(config, "dossier_extraites"))
    classes = restructurations(classer(construire_passages(panel, config), panel, config),
                               panel, identite, config)
    ev = lignes_evaluees(classes, config)

    # 13. Lignes évaluées par passage
    par_t = ev.groupby("t").agg(lignes=("y", "size"), y1=("y", "sum"))
    par_t["part_y1_pct"] = 100 * par_t["y1"] / par_t["lignes"]
    par_t["reference_pct"] = 100 * classes.groupby("t")["reference"].first()
    ecarts = classes[classes["actif_t1"]].groupby("t")["ecart_points"]
    par_t["ecart_q10"], par_t["ecart_mediane"], par_t["ecart_q90"] = (
        ecarts.quantile(0.10), ecarts.median(), ecarts.quantile(0.90))
    par_t.index = [f"{t}->{t + 1}" for t in par_t.index]
    par_t.round(2).to_csv(tableaux / "lignes_par_passage.csv")
    print("\n13. Lignes évaluées par passage (y connu, restructurations probables retirées) :")
    print(par_t.round(1).to_string())

    # 14. Creux de 2020 et rattrapage : établissements actifs les 13 années, indice base 2019 = 100
    actifs = panel[panel["activite"] > 0]
    nb_annees = actifs.groupby("fi")["an"].nunique()
    toujours = nb_annees[nb_annees == len(annees)].index
    indice = actifs[actifs["fi"].isin(toujours)].pivot(index="fi", columns="an", values="activite")
    indice = 100 * indice.div(indice[ANNEE_BASE_INDICE], axis=0)
    quantiles = indice.quantile([0.10, 0.25, 0.50, 0.75, 0.90]).T
    quantiles.columns = ["q10", "q25", "mediane", "q75", "q90"]
    quantiles.round(2).to_csv(tableaux / "indice_activite_base_2019.csv")
    print(f"\n14. Indice d'activité ({ANNEE_BASE_INDICE} = 100), {len(indice)} établissements actifs "
          f"les {len(annees)} années :")
    print(quantiles.round(1).to_string())

    # 15. Part du test selon le nombre de dernières années, passages Covid retirés
    hors_covid = ev[~ev["t"].isin(PASSAGES_COVID)]
    annees_t = sorted(hors_covid["t"].unique())
    lignes = []
    for k in ANNEES_DE_TEST_CANDIDATES:
        entrainement, test, _ = separer_test(hors_covid, annees_t[-k:], PASSAGES_COVID)
        lignes.append({"annees_de_test": k, "annees_t_test": "-".join(map(str, annees_t[-k:])),
                       "lignes_test": len(test), "part_test_pct": 100 * len(test) / len(hors_covid),
                       "y1_test": int(test["y"].sum()), "part_y1_test_pct": 100 * test["y"].mean(),
                       "lignes_entrainement": len(entrainement), "y1_entrainement": int(entrainement["y"].sum()),
                       "part_y1_entrainement_pct": 100 * entrainement["y"].mean()})
    proportion = pd.DataFrame(lignes).set_index("annees_de_test")
    proportion.round(2).to_csv(tableaux / "proportion_test.csv")
    covid = ev[ev["t"].isin(PASSAGES_COVID)]
    print(f"\n15. Sans les passages Covid ({len(covid)} lignes, {int(covid['y'].sum())} y = 1) : "
          f"{len(annees_t)} années, {len(hors_covid)} lignes, {int(hors_covid['y'].sum())} y = 1. Part du test :")
    print(proportion.round(1).to_string())

    # 16. TimeSeriesSplit (blocs de lignes) contre plis par année, sur l'entraînement à 2 années de test
    entrainement, _, _ = separer_test(hors_covid, annees_t[-2:], PASSAGES_COVID)
    a = entrainement.sort_values("t")["t"].to_numpy()
    lignes = []
    decoupages = {"TimeSeriesSplit": TimeSeriesSplit(n_splits=len(np.unique(a)) - 1).split(a),
                  "plis_par_annee": plis_par_annee(a)}
    for methode, plis in decoupages.items():
        for numero, (tr, te) in enumerate(plis, 1):
            validation = pd.Series(a[te]).value_counts().sort_index()
            lignes.append({"methode": methode, "pli": numero,
                           "entrainement": f"{a[tr].min()}-{a[tr].max()}", "lignes_entrainement": len(tr),
                           "validation": " + ".join(f"{n} de {an}" for an, n in validation.items()),
                           "meme_annee_des_deux_cotes": bool(set(a[tr]) & set(a[te])),
                           "avenir_dans_l_entrainement": bool(a[tr].max() > a[te].min())})
    plis_tss = pd.DataFrame(lignes)
    plis_tss.to_csv(tableaux / "plis_timeseriessplit.csv", index=False)
    print(f"\n16. Plis sur l'entraînement ({len(a)} lignes) : TimeSeriesSplit contre plis par année :")
    print(plis_tss.to_string(index=False))

    # 17. Cases vides des lignes évaluées hors Covid (test compris)
    modele = hors_covid[["fi", "t"]].merge(panel, left_on=["fi", "t"], right_on=["fi", "an"])
    lignes = []
    for d in DISCIPLINES:
        for vide, autre in CAPACITE_ET_ACTIVITE + ACTIVITE_ET_CAPACITE:
            colonne, reference = f"{vide}_{d}", f"{autre}_{d}"
            v = modele[colonne].isna()
            if v.any():
                r = modele.loc[v, reference]
                lignes.append({"colonne": colonne, "cases_vides": int(v.sum()),
                               "pct_lignes": 100 * v.mean(), "comparee_a": reference,
                               "comparee_positive": int((r > 0).sum()), "comparee_nulle": int((r == 0).sum()),
                               "comparee_vide": int(r.isna().sum())})
    vides = pd.DataFrame(lignes).sort_values(["comparee_a", "colonne"])
    vides.round(2).to_csv(tableaux / "cases_vides_modele.csv", index=False)
    quantites = [c for c in panel.columns if c.split("_")[0] in
                 {"lit", "jli", "jou", "sejhc", "sej0", "pla", "sejhp", "sea"}]
    print(f"\n17. Cases vides des {len(modele)} lignes évaluées hors Covid "
          f"({int(modele[quantites].isna().any(axis=1).sum())} lignes avec au moins une case vide) :")
    print(vides.round(2).to_string(index=False))

    # 18. Séjours de 0 jour non renseignés alors que l'établissement a des lits
    lignes = []
    for d in DISCIPLINES[:3]:
        cas = modele[modele[f"sej0_{d}"].isna() & (modele[f"lit_{d}"] > 0)]
        for _, c in cas.iterrows():
            historique = panel[(panel["fi"] == c["fi"]) & (panel["an"] != c["an"])]
            renseigne = historique[historique[f"sej0_{d}"].notna() & (historique[f"sejhc_{d}"] > 0)]
            lignes.append({"fi": c["fi"], "t": c["an"], "discipline": d, "stjr": c["stjr"], "catr": c["catr"],
                           "lit": c[f"lit_{d}"], "sejhc": c[f"sejhc_{d}"], "activite": round(c["activite"]),
                           "autres_annees_sej0_vide": int(historique[f"sej0_{d}"].isna().sum()),
                           "autres_annees_sej0_renseigne": len(renseigne),
                           "part_sej0_dans_sejhc_autres_annees_pct":
                               round(100 * renseigne[f"sej0_{d}"].sum() / renseigne[f"sejhc_{d}"].sum(), 1)
                               if len(renseigne) else float("nan")})
    sej0 = pd.DataFrame(lignes)
    sej0.to_csv(tableaux / "sej0_vides_avec_lits.csv", index=False)
    print(f"\n18. Séjours de 0 jour non renseignés alors que l'établissement a des lits ({len(sej0)} cases) :")
    print(sej0.to_string(index=False))

    # Figure : activité nationale, indice des établissements, part de y = 1 par passage
    nat = panel.groupby("an")[["activite", "jou_mco", "sejhp_mco"]].sum() / 1e6
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
    for colonne, nom in [("activite", "activité (journées-équivalentes)"), ("jou_mco", "journées de complète"),
                         ("sejhp_mco", "venues de partielle")]:
        ax[0].plot(nat.index, nat[colonne], marker="o", label=nom)
    ax[0].set_title("France : activité MCO (millions)")
    ax[1].fill_between(quantiles.index, quantiles["q10"], quantiles["q90"], alpha=.2, label="10 %–90 %")
    ax[1].fill_between(quantiles.index, quantiles["q25"], quantiles["q75"], alpha=.35, label="25 %–75 %")
    ax[1].plot(quantiles.index, quantiles["mediane"], marker="o", label="médiane")
    ax[1].axhline(100, color="grey", lw=.8)
    ax[1].set_title(f"Établissements actifs les {len(annees)} années (n = {len(indice)}) : "
                    f"indice {ANNEE_BASE_INDICE} = 100")
    covid_labels = {f"{t}->{t + 1}" for t in PASSAGES_COVID}
    ax[2].bar(range(len(par_t)), par_t["part_y1_pct"],
              color=["tab:red" if s in covid_labels else "tab:blue" for s in par_t.index])
    ax[2].set_xticks(range(len(par_t)))
    ax[2].set_xticklabels(par_t.index, rotation=60, fontsize=8)
    ax[2].set_title("Part de y = 1 par passage (%), passages Covid en rouge")
    for x in ax[:2]:
        x.axvspan(2019.5, 2020.5, color="red", alpha=.08)
        x.legend(fontsize=8)
    for x in ax:
        x.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(figures / "covid_et_test.png", dpi=130)
    plt.close(fig)


def groupe_de_ligne(c):
    """stable (y = 0), décrochage ou sortie, gardé ou déjà repéré (restructuration probable)."""
    return np.where(c["y"] == 0, "stable (y=0)",
                    c["classe"] + np.where(c["restructuration_probable"] == 1, " déjà repéré", " gardé"))


def mouvements_declares(c, identite):
    """Mouvements déclarés dans la table ID pour chaque passage (fi, t), en t ou en t+1."""
    ident = identite.copy()
    ident["an"] = ident["an"].astype(int)
    for col in ["fi", "fi_ej", "fipre"] + COLONNES_FUSION_SCISSION:
        ident[col] = ident[col].str.strip().str.zfill(9)
    for col in ["chlej0", "modej", "typmd1", "typmd2", "typmd3"]:
        ident[col] = pd.to_numeric(ident[col], errors="coerce").fillna(0).astype(int)
    site = ident.drop_duplicates(["fi", "an"]).set_index(["fi", "an"])
    cle_t = list(zip(c["fi"], c["t"]))
    cle_t1 = list(zip(c["fi"], c["t"] + 1))

    def declare(col, cles):
        valeurs = site[col]
        return np.array([valeurs.get(k, 0) == 1 for k in cles])

    m = pd.DataFrame(index=c.index)
    m["entite_changee_declaree"] = declare("chlej0", cle_t1)
    for col, nom in [("modej", "modification_entite"), ("typmd2", "fusion"), ("typmd3", "scission"),
                     ("typmd1", "creation")]:
        m[nom] = declare(col, cle_t) | declare(col, cle_t1)
    cites = set()
    for col in COLONNES_FUSION_SCISSION:
        x = ident[ident[col].notna()]
        cites |= set(zip(x[col], x["an"], x["fi"]))
    par_soi = {(f, a) for f, a, d in cites if f == d}
    cites_finess = {(f, a) for f, a, _ in cites}
    m["se_cite_lui_meme"] = [(f, t) in par_soi or (f, t + 1) in par_soi for f, t in cle_t]
    m["cite_par_un_autre"] = c["cite_fusion_scission"].astype(bool).to_numpy()
    m["entite_citee"] = [(e, t) in cites_finess or (e, t + 1) in cites_finess for e, t in zip(c["fi_ej"], c["t"])]
    avec_fipre = ident[ident["fipre"].notna()]
    fipre = set(zip(avec_fipre["fipre"], avec_fipre["an"]))
    m["entite_precedente_d_un_site_en_t1"] = [(e, t + 1) in fipre for e, t in zip(c["fi_ej"], c["t"])]
    avec_modej = ident[ident["modej"] == 1]
    modej = set(zip(avec_modej["fi_ej"], avec_modej["an"]))
    m["modification_dans_l_entite"] = [(e, t) in modej or (e, t + 1) in modej for e, t in zip(c["fi_ej"], c["t"])]
    m["entite_changee_observee"] = c["changement_de_groupe"].astype(bool).to_numpy()
    m["au_moins_un"] = m.any(axis=1)
    return m


def gains_de_capacite(capacites, a0, a1):
    """Sites qui gagnent au moins 5 lits et places MCO entre a0 et a1 (absents en a0 : 0)."""
    avant = capacites[capacites["an"] == a0][["fi", "fi_ej", "cap", "activite"]]
    x = capacites[capacites["an"] == a1].merge(avant, on="fi", how="left", suffixes=("", "_avant"))
    x["gain"] = x["cap"] - x["cap_avant"].fillna(0)
    x["gain_activite"] = x["activite"] - x["activite_avant"].fillna(0)
    x["nouveau_finess"] = x["cap_avant"].isna()
    return x[x["gain"] >= 5]


def reprises(c, capacites, seuil):
    """Pour chaque passage à forte perte de capacité : reprise stricte en t+1, et placebo (gains de t-1 -> t)."""
    cap = capacites.set_index(["fi", "an"])
    gains = {a: gains_de_capacite(capacites, a - 1, a) for a in sorted(capacites["an"].unique())[1:]}
    absolue, relative = TOLERANCE_REPRISE
    resultats = []
    for r in c.itertuples():
        t = int(r.t)
        if (r.fi, t) not in cap.index:
            continue
        a = cap.loc[(r.fi, t)]
        cap1 = cap["cap"].get((r.fi, t + 1), 0.0)
        act1 = cap["activite"].get((r.fi, t + 1), 0.0)
        perte = a["cap"] - (0.0 if pd.isna(cap1) else cap1)
        perte_activite = max(a["activite"] - (0.0 if pd.isna(act1) else act1), 0.0)
        if perte < seuil or perte < PART_PERTE_MIN * a["cap"]:
            continue
        ligne = {"fi": r.fi, "t": t, "perte": perte, "fi_ej": a["fi_ej"],
                 "capacite_t1": 0.0 if pd.isna(cap1) else cap1}
        for nom, annee in [("reprise", t + 1), ("placebo", t)]:
            g = gains.get(annee)
            if g is None:
                ligne[nom] = np.nan
                continue
            m = g[(g["fi"] != r.fi) & ((g["gain"] - perte).abs() <= max(absolue, relative * perte))]
            k = m[(m["dep"] == a["dep"]) & (m["gain_activite"] >= PART_ACTIVITE_REPRISE * perte_activite)]
            ligne[nom] = bool(len(m) <= CANDIDATS_MAX and perte_activite > 0 and len(k) > 0)
            if nom == "reprise":
                ligne["candidats_en_france"] = len(m)
                ligne["repreneurs"] = k if ligne[nom] else k.iloc[0:0]
        resultats.append(ligne)
    return resultats


def question_7(panel, config, tableaux):
    """Question 7 : mouvements déclarés dans la table ID et reprise des capacités par un autre site."""
    config = sans_regles_posterieures(config)
    annees = range(config["donnees"]["annee_debut"], config["donnees"]["annee_fin"] + 1)
    identite = empiler_table(config, "ID", annees, chemin_donnees(config, "dossier_extraites"))
    c = restructurations(classer(construire_passages(panel, config), panel, config), panel, identite, config)
    c = c[c["y"].notna()].reset_index(drop=True)
    decoupage = config["decoupage"]
    c["partie"] = np.where(c["t"].isin(decoupage["passages_exclus"]), "covid",
                           np.where(c["t"].isin(decoupage["annees_test"]), "test", "entrainement"))
    c["groupe"] = groupe_de_ligne(c)

    # 19. Mouvements déclarés
    m = mouvements_declares(c, identite)
    lignes = []
    for perimetre, masque in [("entrainement", c["partie"] == "entrainement"), ("toutes", c["partie"].notna())]:
        g = (100 * m[masque].groupby(c.loc[masque, "groupe"]).mean()).round(2)
        g.insert(0, "lignes", c[masque].groupby("groupe").size())
        lignes.append(g.assign(perimetre=perimetre).reset_index())
    declares = pd.concat(lignes).set_index(["perimetre", "groupe"])
    declares.to_csv(tableaux / "mouvements_declares.csv")
    print("\n19. Mouvements déclarés dans la table ID (% des lignes de chaque groupe, en t ou t+1) :")
    print(declares.T.to_string())

    # 20. Reprise des capacités par un autre site, selon le seuil de perte
    capacites = panel[["fi", "an", "fi_ej", "dep", "activite"]].copy()
    capacites["cap"] = panel["lit_mco"].fillna(0) + panel["pla_mco"].fillna(0)
    lignes, trouvees = [], {}
    for seuil in SEUILS_REPRISE_CANDIDATS:
        r = pd.DataFrame(reprises(c, capacites, seuil))
        r = r.merge(c[["fi", "t", "partie", "groupe", "classe", "restructuration_probable"]], on=["fi", "t"])
        trouvees[seuil] = r[r["reprise"] == True]  # noqa: E712
        for perimetre, x in [("entrainement", r[r["partie"] == "entrainement"]), ("toutes", r)]:
            for groupe, g in x.groupby("groupe"):
                lignes.append({"seuil": seuil, "perimetre": perimetre, "groupe": groupe, "fortes_pertes": len(g),
                               "reprises": int(g["reprise"].sum()), "reprises_pct": 100 * g["reprise"].mean(),
                               "placebo_pct": 100 * g["placebo"].astype(float).mean()})
    reprise = pd.DataFrame(lignes)
    reprise.round(2).to_csv(tableaux / "reprise_capacites.csv", index=False)
    print("\n20. Reprise stricte des capacités perdues (même département, hausse d'activité, "
          f"au plus {CANDIDATS_MAX} candidats) et placebo t-1 -> t :")
    print(reprise.round(1).to_string(index=False))

    # 21. Reprises trouvées (y = 1), au plus grand seuil
    ident = identite.assign(an=identite["an"].astype(int)).drop_duplicates(["fi", "an"]).set_index(["fi", "an"])
    seuil = max(SEUILS_REPRISE_CANDIDATS)
    presence = ident.reset_index().groupby("fi")["an"].apply(sorted).to_dict()
    lignes = []
    for r in trouvees[seuil][trouvees[seuil]["classe"] != "stable"].itertuples():
        for x in r.repreneurs.itertuples():
            lignes.append({"fi": r.fi, "t": r.t, "partie": r.partie, "classe": r.classe,
                           "deja_repere": r.restructuration_probable, "perte": r.perte,
                           "capacite_t1": r.capacite_t1,
                           "annees_dans_la_sae_apres_t": ",".join(str(a) for a in presence.get(r.fi, []) if a > r.t),
                           "repreneur": x.fi,
                           "gain": x.gain, "nouveau_finess": x.nouveau_finess,
                           "meme_entite_juridique": x.fi_ej == r.fi_ej or x.fi_ej_avant == r.fi_ej,
                           "fipre_repreneur": ident["fipre"].get((x.fi, r.t + 1)),
                           "rs": ident["rs"].get((r.fi, r.t)), "rs_repreneur": ident["rs"].get((x.fi, r.t + 1))})
    trouvees_y1 = pd.DataFrame(lignes)
    trouvees_y1.to_csv(tableaux / "reprises_trouvees.csv", index=False)
    u = trouvees_y1.drop_duplicates(["fi", "t"])
    nouveaux, deja = u[u["deja_repere"] == 0], u[u["deja_repere"] == 1]
    print(f"\n21. Passages y = 1 avec une reprise (seuil {seuil}) : {len(u)}, dont {len(nouveaux)} pas encore "
          f"repérés. Repreneur dans la même entité juridique : {int(nouveaux['meme_entite_juridique'].sum())} "
          f"sur {len(nouveaux)} nouveaux, {int(deja['meme_entite_juridique'].sum())} sur {len(deja)} déjà repérés")
    print(f"    Anciens sites qui gardent des lits ou des places en t+1 : "
          f"{int((nouveaux['capacite_t1'] > 0).sum())} sur {len(nouveaux)} nouveaux")
    print(trouvees_y1.to_string(index=False))


def question_8(panel, config, tableaux):
    """Question 8 : 0 lit et 0 place MCO en t+1 avec encore de l'activité : fermeture en cours d'année ?"""
    config = sans_regles_posterieures(config, reprise=False)
    annees = range(config["donnees"]["annee_debut"], config["donnees"]["annee_fin"] + 1)
    identite = empiler_table(config, "ID", annees, chemin_donnees(config, "dossier_extraites"))
    c = restructurations(classer(construire_passages(panel, config), panel, config), panel, identite, config)
    c = c[c["y"].notna()].reset_index(drop=True)
    decoupage = config["decoupage"]
    c["partie"] = np.where(c["t"].isin(decoupage["passages_exclus"]), "covid",
                           np.where(c["t"].isin(decoupage["annees_test"]), "test", "entrainement"))
    c["groupe"] = groupe_de_ligne(c)
    capacite = dict(zip(zip(panel["fi"], panel["an"]), panel["lit_mco"].fillna(0) + panel["pla_mco"].fillna(0)))
    derniere_active = panel[panel["activite"] > 0].groupby("fi")["an"].max()
    c["capacite_t"] = [capacite.get((f, t), np.nan) for f, t in zip(c["fi"], c["t"])]
    c["capacite_t1"] = [capacite.get((f, t + 1), np.nan) for f, t in zip(c["fi"], c["t"])]
    c["derniere_annee_active"] = c["fi"].map(derniere_active)
    cas = c[c["actif_t1"] & (c["capacite_t1"] == 0) & (c["capacite_t"] > 0)].copy()
    cas["devenir"] = np.select([cas["t"] + 2 > config["donnees"]["annee_fin"],
                                cas["derniere_annee_active"] == cas["t"] + 1],
                               ["suite inconnue (t+1 = dernière année)", "plus jamais actif après t+1"],
                               "actif à nouveau plus tard")
    cas["activite_t1_pct_de_t"] = (100 * cas["activite_t1"] / cas["activite_t"]).round(1)

    # 22. Ce que deviennent les sites à 0 capacité en t+1
    bilan = pd.crosstab(cas["groupe"], cas["devenir"], margins=True, margins_name="total")
    bilan["activite_t1_pct_de_t_mediane"] = cas.groupby("groupe")["activite_t1_pct_de_t"].median()
    bilan.round(1).to_csv(tableaux / "fermeture_en_cours_bilan.csv")
    print(f"\n22. Passages actifs en t+1 avec 0 lit et 0 place MCO en t+1 (capacité > 0 en t) : {len(cas)}")
    print(bilan.round(1).to_string())

    # 23. Décrochages et sorties des lignes évaluées, avant et après reclassement
    ev = c[c["restructuration_probable"] == 0]
    definitives = cas[(cas["restructuration_probable"] == 0) & (cas["classe"] == "decrochage")
                      & (cas["devenir"] == "plus jamais actif après t+1")]
    par_partie = pd.DataFrame({
        "decrochages": ev[ev["classe"] == "decrochage"].groupby("partie").size(),
        "sorties": ev[ev["classe"] == "sortie"].groupby("partie").size(),
        "fermetures_definitives_parmi_les_decrochages": definitives.groupby("partie").size(),
    }).fillna(0).astype(int).reindex(["entrainement", "test", "covid"])
    par_partie["decrochages_apres"] = par_partie["decrochages"] - par_partie["fermetures_definitives_parmi_les_decrochages"]
    par_partie["sorties_apres"] = par_partie["sorties"] + par_partie["fermetures_definitives_parmi_les_decrochages"]
    par_partie.to_csv(tableaux / "fermeture_en_cours_par_partie.csv")
    print("\n23. Lignes évaluées : décrochages et sorties, si les fermetures définitives en cours d'année "
          "devenaient des sorties :")
    print(par_partie.to_string())

    colonnes = ["fi", "t", "partie", "classe", "y", "restructuration_probable", "activite_t", "activite_t1",
                "activite_t1_pct_de_t", "capacite_t", "derniere_annee_active", "devenir"]
    cas[colonnes].sort_values(["devenir", "classe", "t", "fi"]).to_csv(tableaux / "fermeture_en_cours_cas.csv",
                                                                       index=False)


def question_9(panel, config, tableaux):
    """Question 9 : sites sans lits ni places MCO en t (fermeture déjà faite ou capacité non saisie),
    règle de champ (lits + places MCO > 0 en t, connue en t) et classes de y = 1."""
    annees = range(config["donnees"]["annee_debut"], config["donnees"]["annee_fin"] + 1)
    identite = empiler_table(config, "ID", annees, chemin_donnees(config, "dossier_extraites"))
    c = restructurations(classer(construire_passages(panel, config), panel, config), panel, identite, config)
    ev = lignes_evaluees(c, config).reset_index(drop=True)
    decoupage = config["decoupage"]
    ev["partie"] = np.where(ev["t"].isin(decoupage["passages_exclus"]), "covid",
                            np.where(ev["t"].isin(decoupage["annees_test"]), "test", "entrainement"))
    capacite = dict(zip(zip(panel["fi"], panel["an"]), panel["lit_mco"].fillna(0) + panel["pla_mco"].fillna(0)))
    derniere_active = panel[panel["activite"] > 0].groupby("fi")["an"].max()
    ev["capacite_t"] = [capacite.get((f, t), np.nan) for f, t in zip(ev["fi"], ev["t"])]
    ev["capacite_t_moins_1"] = [capacite.get((f, t - 1), np.nan) for f, t in zip(ev["fi"], ev["t"])]
    ev["capacite_t_plus_1"] = [capacite.get((f, t + 1), np.nan) for f, t in zip(ev["fi"], ev["t"])]
    ev["derniere_annee_mco"] = ev["fi"].map(derniere_active)
    ev["deja_ferme_en_t"] = (ev["capacite_t"] == 0) & (ev["derniere_annee_mco"] == ev["t"])   # description seulement
    ev["hors_champ"] = ev["capacite_t"] == 0                                                   # règle : connue en t
    # passage d'avant (toutes les lignes de la cible, restructurations comprises) : fermeture en cours d'année ?
    fermetures = set(zip(c.loc[c["fermeture_en_cours"] == 1, "fi"], c.loc[c["fermeture_en_cours"] == 1, "t"] + 1))
    ev["suit_une_fermeture_en_cours"] = [(f, t) in fermetures for f, t in zip(ev["fi"], ev["t"])]

    # 24. Lignes évaluées à 0 lit et 0 place MCO en t
    zero = ev[ev["capacite_t"] == 0].copy()
    zero["capacite_avant_et_apres"] = (zero["capacite_t_moins_1"] > 0) & (zero["capacite_t_plus_1"] > 0)
    zero["explication"] = np.select(
        [zero["suit_une_fermeture_en_cours"], zero["deja_ferme_en_t"] & (zero["t"] == min(annees)),
         zero["deja_ferme_en_t"], zero["capacite_avant_et_apres"]],
        ["passage qui suit une fermeture en cours d'année", "fermeture pendant la première année (pas de passage avant)",
         "fermeture pendant l'année t", "capacité non saisie (lits avant et après)"], "autre")
    colonnes = ["fi", "t", "partie", "classe", "y", "activite_t", "capacite_t_moins_1", "capacite_t_plus_1",
                "derniere_annee_mco", "deja_ferme_en_t", "explication"]
    zero[colonnes].sort_values(["explication", "t", "fi"]).to_csv(tableaux / "champ_lignes_zero_capacite.csv", index=False)
    print(f"\n24. Lignes évaluées à 0 lit et 0 place MCO en t : {len(zero)}")
    print(pd.crosstab(zero["explication"], zero["classe"], margins=True, margins_name="total").to_string())

    # 25. Règle de champ : lignes sans lits ni places MCO en t retirées, par partie
    lignes = []
    for partie in ["entrainement", "test", "covid"]:
        p = ev[ev["partie"] == partie]
        hors = p[p["hors_champ"]]
        apres = p[~p["hors_champ"]]
        lignes.append({"partie": partie, "lignes": len(p), "y1": int(p["y"].sum()),
                       "hors_champ": len(hors), "hors_champ_sorties": int((hors["classe"] == "sortie").sum()),
                       "hors_champ_decrochages": int((hors["classe"] == "decrochage").sum()),
                       "hors_champ_stables": int((hors["classe"] == "stable").sum()),
                       "lignes_apres": len(apres), "y1_apres": int(apres["y"].sum()),
                       "part_y1_apres_pct": round(100 * apres["y"].mean(), 2),
                       "decrochages_apres": int((apres["classe"] == "decrochage").sum()),
                       "sorties_apres": int((apres["classe"] == "sortie").sum())})
    par_partie = pd.DataFrame(lignes).set_index("partie")
    par_partie.to_csv(tableaux / "champ_par_partie.csv")
    print("\n25. Règle de champ (lits + places MCO > 0 en t) : lignes hors champ et lignes évaluées restantes :")
    print(par_partie.to_string())

    # 26. Classes de y = 1, pour le rapport : décrochage, fermeture, arrêt du MCO
    smr = empiler_table(config, "SSR_SMR", annees, chemin_donnees(config, "dossier_extraites"))
    smr = smr[smr["gde"] == "SSR_TOT"]
    jours = vers_nombre(smr["jouhc"]).fillna(0) + vers_nombre(smr["jouhp"]).fillna(0)
    avec_smr = set(zip(smr.loc[jours > 0, "fi"], smr.loc[jours > 0, "an"].astype(int)))
    dans_sae = set(zip(identite["fi"], identite["an"].astype(int)))
    garde = ev[~ev["hors_champ"] & (ev["y"] == 1)].copy()
    fin = config["donnees"]["annee_fin"]
    apres_mco = [range(int(m) + 1, fin + 1) for m in garde["derniere_annee_mco"]]
    garde["classe_rapport"] = np.select(
        [garde["classe"] == "decrochage",
         [any((f, a) in avec_smr for a in r) for f, r in zip(garde["fi"], apres_mco)],
         [any((f, a) in dans_sae for a in r) for f, r in zip(garde["fi"], apres_mco)]],
        ["décrochage", "arrêt du MCO (activité SMR ensuite)", "fermeture ou arrêt du MCO (dans la SAE, sans SMR)"],
        "fermeture (absent de la SAE)")
    classes = pd.crosstab(garde["classe_rapport"], garde["partie"], margins=True, margins_name="total")
    classes.to_csv(tableaux / "classes_y1_rapport.csv")
    print("\n26. Classes de y = 1 pour le rapport (lignes évaluées dans le champ) :")
    print(classes.to_string())

    # 27. Contrôle : ce qu'annonce inc_lits_zero_avec_journees à l'entraînement, avant et après le retrait
    indicateur = panel.set_index(["fi", "an"])["inc_lits_zero_avec_journees"]
    ev["inc_lits_zero_avec_journees"] = [indicateur.get((f, t), 0) for f, t in zip(ev["fi"], ev["t"])]
    lignes = []
    for nom, p in [("toutes les lignes évaluées", ev), ("dans le champ", ev[~ev["hors_champ"]])]:
        p = p[p["partie"] == "entrainement"]
        un = p[p["inc_lits_zero_avec_journees"] == 1]
        lignes.append({"lignes": nom, "indicateur_a_1": len(un), "stables": int((un["classe"] == "stable").sum()),
                       "decrochages": int((un["classe"] == "decrochage").sum()),
                       "sorties": int((un["classe"] == "sortie").sum()),
                       "y1_pct_si_1": round(100 * un["y"].mean(), 1) if len(un) else np.nan,
                       "y1_pct_si_0": round(100 * p.loc[p["inc_lits_zero_avec_journees"] != 1, "y"].mean(), 1)})
    controle = pd.DataFrame(lignes).set_index("lignes")
    controle.to_csv(tableaux / "champ_controle_indicateur.csv")
    print("\n27. Contrôle à l'entraînement : inc_lits_zero_avec_journees, toutes lignes et dans le champ :")
    print(controle.to_string())


if __name__ == "__main__":
    main()
