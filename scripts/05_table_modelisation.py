"""Étape 05 : construire la table de modélisation, une ligne par passage évalué.

Lancement, depuis la racine du dépôt (après scripts/03_panel.py) :
    python scripts/05_table_modelisation.py

Chaque ligne est un passage t -> t+1 dont la cible est connue et qui n'est pas une
restructuration probable (src.decoupage.lignes_evaluees) : fi, t, y, la classe (stable,
decrochage ou sortie : pour évaluer à part décrochages et sorties ; jamais une variable), la partie
(entrainement, test ou covid, selon config.yaml › decoupage) et les variables connues en t
(src.variables.variables_explicatives). Décisions : docs/decisions.md.
Trois vérifications (le script s'arrête si l'une échoue) :
  - aucune variable interdite (identifiant ou information de t+1) ;
  - chaque passage évalué retrouve sa ligne du panel en t, une seule fois ;
  - le couple (fi, t) n'apparaît jamais deux fois.
Produit :
  - donnees/preparees/modelisation_mco.parquet (non versionné, régénérable) ;
  - resultats/03_exploration/tableaux/table_modelisation_controles.csv : lignes et y = 1
    par partie et par année t ;
  - resultats/03_exploration/tableaux/table_modelisation_variables.csv : chaque variable,
    son type et sa part de cases vides, par partie.
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.activite import calculer_activite  # noqa: E402
from src.chargement import empiler_table  # noqa: E402
from src.cible import classer, construire_passages, restructurations  # noqa: E402
from src.config import charger_config, chemin_donnees, racine_projet  # noqa: E402
from src.decoupage import lignes_evaluees, separer_test  # noqa: E402
from src.variables import CATEGORIELLES, variables_explicatives, verifier_sans_fuite  # noqa: E402

PARTIES = ["entrainement", "test", "covid"]


def main():
    config = charger_config()
    d, decoupage = config["donnees"], config["decoupage"]
    annees = range(d["annee_debut"], d["annee_fin"] + 1)
    panel = pd.read_parquet(chemin_donnees(config, "dossier_preparees") / "panel_mco.parquet")
    panel["activite"] = calculer_activite(panel, config)

    # 1. Passages évalués (cible connue, restructurations probables retirées)
    identite = empiler_table(config, "ID", annees, chemin_donnees(config, "dossier_extraites"))
    classes = restructurations(classer(construire_passages(panel, config), panel, config),
                               panel, identite, config)
    evalues = lignes_evaluees(classes, config)[["fi", "t", "y", "classe"]]

    # 2. Partie de chaque passage, selon l'année t
    entrainement, test, covid = separer_test(evalues, decoupage["annees_test"], decoupage["passages_exclus"])
    evalues = pd.concat([entrainement.assign(partie="entrainement"), test.assign(partie="test"),
                         covid.assign(partie="covid")])

    # 3. Variables connues en t, jointes sur (fi, t)
    variables = variables_explicatives(panel).rename(columns={"an": "t"})
    noms_variables = [c for c in variables.columns if c not in ("fi", "t")]
    verifier_sans_fuite(noms_variables)
    table = evalues.merge(variables, on=["fi", "t"], how="left", validate="one_to_one", indicator=True)
    sans_variables = int((table["_merge"] != "both").sum())
    if sans_variables:
        sys.exit(f"ARRÊT : {sans_variables} passages évalués sans ligne du panel en t.")
    table = table.drop(columns="_merge")
    if table.duplicated(["fi", "t"]).any():
        sys.exit("ARRÊT : un couple (fi, t) apparaît deux fois.")
    table["y"] = table["y"].astype(int)
    table = table.sort_values(["t", "fi"]).reset_index(drop=True)

    sortie = chemin_donnees(config, "dossier_preparees") / "modelisation_mco.parquet"
    table.to_parquet(sortie, index=False)

    # 4. Contrôles
    tableaux = racine_projet() / "resultats" / "03_exploration" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    par_annee = table.groupby(["partie", "t"]).agg(lignes=("y", "size"), y1=("y", "sum"))
    par_partie = table.groupby("partie").agg(lignes=("y", "size"), y1=("y", "sum"))
    par_partie["t"] = "toutes"
    controles = pd.concat([par_annee.reset_index(), par_partie.reset_index()])
    controles["part_y1_pct"] = (100 * controles["y1"] / controles["lignes"]).round(2)
    controles["ordre"] = controles["partie"].map(PARTIES.index)
    controles = controles.sort_values(["ordre", "t"], key=lambda s: s.astype(str)).drop(columns="ordre")
    controles.to_csv(tableaux / "table_modelisation_controles.csv", index=False)

    vides = table.groupby("partie")[noms_variables].apply(lambda g: 100 * g.isna().mean()).T[PARTIES]
    vides.columns = [f"vides_{p}_pct" for p in PARTIES]
    description = pd.DataFrame({"type": ["categorielle" if c in CATEGORIELLES else "nombre"
                                         for c in noms_variables]}, index=noms_variables)
    description = description.join(vides.round(2))
    description.index.name = "variable"
    description.to_csv(tableaux / "table_modelisation_variables.csv")

    print(f"Table de modélisation : {len(table)} passages évalués, {len(noms_variables)} variables "
          f"({sum(c in CATEGORIELLES for c in noms_variables)} catégorielles)")
    print(par_partie[["lignes", "y1"]].assign(part_y1_pct=(100 * par_partie["y1"] / par_partie["lignes"]).round(2))
          .reindex(PARTIES).to_string())
    print("\nVariables avec des cases vides (% des lignes, par partie) :")
    print(description[description.filter(like="vides").sum(axis=1) > 0].to_string())
    print(f"\nÉcrit : {sortie.relative_to(racine_projet())} ; contrôles dans "
          f"{tableaux.relative_to(racine_projet())}")


if __name__ == "__main__":
    main()
