"""Étape 02 : audit de qualité de toutes les tables, année par année, AVANT l'empilement.

Lancement, depuis la racine du dépôt (après scripts/01_extraire.py) :
    python scripts/02_audit_qualite.py

Rien n'est corrigé ici : on mesure, puis on décide et on documente.
Contrôles :
  1. présence des colonnes selon les années      -> colonnes_par_annee.csv
  2. part de valeurs manquantes                  -> manquants.csv
     (+ figure des quantités d'activité et de capacité de la table MCO)
  3. types : nombres, texte, ou les deux mêlés    -> types.csv
  4. clés : doublons, FINESS mal formés, année ; -> cles.csv
     cohérence : établissements absents de ID     -> coherence_tables.csv
  5. règles de cohérence de l'activité MCO        -> controles_mco.csv
Sorties dans resultats/01_qualite_donnees/ (tableaux/ et figures/).
"""

import sys
from pathlib import Path

# Affichage en UTF-8 : sinon les accents sont abîmés dans le terminal de Git Bash.
sys.stdout.reconfigure(encoding="utf-8")

# La racine du dépôt passe en premier dans le chemin de Python (imports « from src... »).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")                       # figures écrites dans des fichiers, sans fenêtre
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.chargement import lire_table, tables_attendues, trouver_table_extraite  # noqa: E402
from src.config import charger_config, chemin_donnees, encodage_de_l_annee, racine_projet  # noqa: E402
from src.nettoyage import valeurs_non_numeriques  # noqa: E402
from src.qualite import (  # noqa: E402
    absents,
    annees_incoherentes,
    controles_activite_mco,
    doublons_cle,
    finess_invalides,
    presence_colonnes,
    profil_types,
    resume_presence,
    taux_manquants,
)

# Quantités d'activité et de capacité de la table MCO (journées, séjours, séjours de 0 jour,
# venues de partielle, lits, places, journées exploitables, par discipline, et séances).
QUANTITES_MCO = [f"{m}_{d}" for m in ("jou", "sejhc", "sej0", "sejhp", "lit", "pla", "jli")
                 for d in ("med", "chi", "obs", "mco")] + ["sea_mco"]


# Clé de chaque table : un établissement (fi), sauf SSR/SMR (une ligne par type de soins, gde).
CLES = {"SSR": ["fi", "gde"], "SMR": ["fi", "gde"]}
CLE_PAR_DEFAUT = ["fi"]


def nom_stable(table):
    """SSR (2013-2024) et SMR (2025) sont la même table : un seul nom pour l'audit."""
    return "SSR_SMR" if table in ("SSR", "SMR") else table


def figure_manquants(grille, dossier):
    """Carte colonne x année de la part de cases vides (une seule couleur, du clair au foncé)."""
    dossier.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 9))
    image = ax.imshow(100 * grille.values, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(len(grille.columns)), grille.columns, rotation=45)
    ax.set_yticks(range(len(grille.index)), grille.index)
    for i in range(grille.shape[0]):
        for j in range(grille.shape[1]):
            valeur = 100 * grille.values[i, j]
            if valeur >= 0.05:
                ax.text(j, i, f"{valeur:.1f}", ha="center", va="center", fontsize=7,
                        color="white" if valeur > 50 else "#2b2b2a")
    ax.set_title("Table MCO : part de cases vides (%) des quantités d'activité et de capacité",
                 loc="left", fontsize=11)
    fig.colorbar(image, label="part de cases vides (%)")
    fig.tight_layout()
    fig.savefig(dossier / "manquants_quantites_mco.png", dpi=130)
    plt.close(fig)


def main():
    config = charger_config()
    d = config["donnees"]
    extraites = chemin_donnees(config, "dossier_extraites")
    annees = range(d["annee_debut"], d["annee_fin"] + 1)

    colonnes = {}            # {table: {annee: [colonnes]}}
    manquants, types, exemples, cles, coherence, mco = [], [], {}, [], [], []
    for annee in annees:
        encodage = encodage_de_l_annee(config, annee)
        lues = {}
        for table in tables_attendues(d["tables"], annee):
            chemin = trouver_table_extraite(extraites, table, annee)
            lue = lire_table(chemin, encodage, d["separateur_csv"], erreurs="replace")
            lues[table] = lue
            colonnes.setdefault(nom_stable(table), {})[annee] = list(lue.columns)
            for colonne, taux in taux_manquants(lue).items():
                manquants.append({"table": nom_stable(table), "annee": annee,
                                  "colonne": colonne, "taux_manquants": round(taux, 4)})
            for _, ligne in profil_types(lue).iterrows():
                types.append({"table": nom_stable(table), "annee": annee, **ligne.to_dict()})
                if ligne["type"] == "mixte":
                    cle = (nom_stable(table), ligne["colonne"])
                    exemples.setdefault(cle, set()).update(
                        valeurs_non_numeriques(lue[ligne["colonne"]]).index[:5])
            cle_table = CLES.get(table, CLE_PAR_DEFAUT)
            cles.append({"table": nom_stable(table), "annee": annee, "lignes": len(lue),
                         "cle": "+".join(cle_table),
                         "lignes_cle_en_double": len(doublons_cle(lue, cle_table)),
                         "finess_mal_formes": int(finess_invalides(lue["fi"]).sum()),
                         "an_different_de_l_annee": annees_incoherentes(lue, annee)})

        # Règles de l'activité MCO
        mco.append({"annee": annee, **controles_activite_mco(lues["MCO"])})

        # Cohérence : chaque table comparée à ID, la carte d'identité des établissements
        for table, lue in lues.items():
            if table == "ID":
                continue
            hors_id = absents(lue["fi"], lues["ID"]["fi"])
            coherence.append({"annee": annee, "table": nom_stable(table),
                              "finess": lue["fi"].nunique(), "finess_absents_de_ID": len(hors_id),
                              "exemples": " ".join(hors_id[:5])})

    # 1. Présence des colonnes
    presence = pd.concat([resume_presence(presence_colonnes(par_annee)).assign(table=t)
                          for t, par_annee in colonnes.items()])
    presence = presence[["table", "colonne", "nb_annees", "premiere", "derniere",
                         "presente_toutes_annees", "annees_absentes"]]

    tableaux = racine_projet() / "resultats" / "01_qualite_donnees" / "tableaux"
    tableaux.mkdir(parents=True, exist_ok=True)
    sortie = tableaux / "colonnes_par_annee.csv"
    presence.to_csv(sortie, index=False, encoding="utf-8")

    print("1. Présence des colonnes, par table :")
    resume = presence.groupby("table").agg(
        colonnes=("colonne", "size"),
        toutes_les_annees=("presente_toutes_annees", "sum"),
    )
    resume["certaines_annees_seulement"] = resume["colonnes"] - resume["toutes_les_annees"]
    print(resume.to_string())
    print(f"\nDétail colonne par colonne dans {sortie.relative_to(racine_projet())}")

    # 2. Valeurs manquantes
    manquants = pd.DataFrame(manquants)
    manquants.to_csv(tableaux / "manquants.csv", index=False, encoding="utf-8")
    grille = (manquants[(manquants.table == "MCO") & manquants.colonne.isin(QUANTITES_MCO)]
              .pivot(index="colonne", columns="annee", values="taux_manquants")
              .reindex(QUANTITES_MCO))
    figure_manquants(grille, racine_projet() / "resultats" / "01_qualite_donnees" / "figures")

    print("\n2. Part de cases vides (%) des quantités MCO, minimum et maximum sur les 13 années :")
    etendue = (100 * grille).agg(["min", "max"], axis=1).round(1)
    print(etendue.to_string())
    print("Détail dans resultats/01_qualite_donnees/tableaux/manquants.csv "
          "et figures/manquants_quantites_mco.png")

    # 3. Types
    types = pd.DataFrame(types)
    types.to_csv(tableaux / "types.csv", index=False, encoding="utf-8")
    print("\n3. Types des colonnes (nombre de couples table x colonne x année) :")
    print(types.groupby(["table", "type"]).size().unstack(fill_value=0).to_string())
    mixte = types[types.type == "mixte"]
    print("\n   Colonnes « mixtes » (nombres et texte mêlés) : années concernées et exemples de texte :")
    if len(mixte):
        resume = mixte.groupby(["table", "colonne"]).annee.agg(lambda a: " ".join(map(str, sorted(a))))
        for (table, colonne), annees_mixtes in resume.items():
            vus = ", ".join(sorted(exemples.get((table, colonne), set()))[:5])
            print(f"   {table:9s} {colonne:12s} {annees_mixtes}  ->  {vus}")
    else:
        print("   aucune")
    print("Détail dans resultats/01_qualite_donnees/tableaux/types.csv")

    # 4. Clés et cohérence
    cles = pd.DataFrame(cles)
    cles.to_csv(tableaux / "cles.csv", index=False, encoding="utf-8")
    coherence = pd.DataFrame(coherence)
    coherence.to_csv(tableaux / "coherence_tables.csv", index=False, encoding="utf-8")
    print("\n4. Clés (total sur les 13 années, par table) :")
    print(cles.groupby("table")[["lignes", "lignes_cle_en_double", "finess_mal_formes",
                                  "an_different_de_l_annee"]].sum().to_string())
    print("\n   Cohérence : FINESS absents de la table ID (total sur les années, par table) :")
    print(coherence.groupby("table").finess_absents_de_ID.sum().to_string())
    print("Détail dans resultats/01_qualite_donnees/tableaux/cles.csv et coherence_tables.csv")

    # 5. Règles de l'activité MCO
    mco = pd.DataFrame(mco)
    mco.to_csv(tableaux / "controles_mco.csv", index=False, encoding="utf-8")
    noms_courts = {"activite_entierement_vide": "vide", "aucun_sejour": "aucun_sejour",
                   "valeur_negative": "negatif", "sej0_superieur_a_sejhc": "sej0>sejhc",
                   "jou_inferieur_aux_sejours_non_nuls": "jou_trop_bas",
                   "journees_sans_sejour": "jou_sans_sejour"}
    print("\n5. Règles de l'activité MCO (nombre de lignes concernées, par année) :")
    print(mco.rename(columns=noms_courts).to_string(index=False))
    print("Détail dans resultats/01_qualite_donnees/tableaux/controles_mco.csv")


if __name__ == "__main__":
    main()
