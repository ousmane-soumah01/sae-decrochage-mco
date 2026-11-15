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
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.activite import calculer_activite, est_eligible  # noqa: E402
from src.cible import construire_passages, ecarts_et_decrochages, reference_ponderee  # noqa: E402
from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402

COMPOSANTES = ["jou_mco", "sejhc_mco", "sej0_mco", "sejhp_mco", "sea_mco"]
POIDS_CANDIDATS = {"1/3": 1 / 3, "1/2": 1 / 2, "1": 1.0}
SEUILS_CANDIDATS = [0, 365, 1000, 3650]
TRANCHES = [0, 100, 365, 1000, 3650, float("inf")]


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

    print(f"\nTableaux écrits dans {tableaux.relative_to(racine_projet())}, figures dans "
          f"{figures.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
