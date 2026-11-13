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
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402

COMPOSANTES = ["jou_mco", "sejhc_mco", "sej0_mco", "sejhp_mco", "sea_mco"]
POIDS_CANDIDATS = {"1/3": 1 / 3, "1/2": 1 / 2, "1": 1.0}


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

    print(f"\nTableaux écrits dans {tableaux.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
