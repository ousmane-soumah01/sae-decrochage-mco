"""Dictionnaire des colonnes du panel : la seule source de leurs définitions.

Chaque colonne du panel (scripts/03_panel.py) a une entrée : groupe, définition, unité,
source et règle. Les libellés entre guillemets sont ceux de la DREES (« Liste variables
SAE 2024.xlsx », archive SAE 2024, dossier Documentation). scripts/06_dictionnaire.py
écrit docs/dictionnaire.md à partir de ce dictionnaire.
"""

import pandas as pd

GROUPES = ["clé", "quantité MCO", "incohérence repérée", "identité", "indicateur d'une autre table"]


def _e(groupe, definition, unite, source, regle):
    return {"groupe": groupe, "definition": definition, "unite": unite, "source": source, "regle": regle}


DICTIONNAIRE = {
    "fi": _e("clé", "« N° Finess » du site géographique (l'établissement)", "code", "SAE, table MCO", "texte : garde le zéro de tête et le « 2A » / « 2B » de la Corse (décision 3)"),
    "an": _e("clé", "Année de la SAE", "année", "SAE, table MCO", "nombre entier"),
    "lit_med": _e("quantité MCO", "« Lits de médecine installés en hospitalisation complète au 31/12 »", "lits", "SAE, table MCO", "nombre ; vide mis à 0 si jou_med est nul (décision 1)"),
    "lit_chi": _e("quantité MCO", "« Lits de chirurgie installés en hospitalisation complète au 31/12 »", "lits", "SAE, table MCO", "nombre ; vide mis à 0 si jou_chi est nul (décision 1)"),
    "lit_obs": _e("quantité MCO", "« Lits de gynécologie-obstétrique installés en hospitalisation complète au 31/12 »", "lits", "SAE, table MCO", "nombre ; vide mis à 0 si jou_obs est nul (décision 1)"),
    "lit_mco": _e("quantité MCO", "« Lits de MCO installés en hospitalisation complète au 31/12 »", "lits", "SAE, table MCO", "nombre ; vide mis à 0 si jou_mco est nul (décision 1)"),
    "jli_med": _e("quantité MCO", "« Journées exploitables de médecine en hospitalisation complète »", "journées", "SAE, table MCO", "nombre ; vide mis à 0 si jou_med est nul (décision 1)"),
    "jli_chi": _e("quantité MCO", "« Journées exploitables de chirurgie en hospitalisation complète »", "journées", "SAE, table MCO", "nombre ; vide mis à 0 si jou_chi est nul (décision 1)"),
    "jli_obs": _e("quantité MCO", "« Journées exploitables de gynécologie-obstétrique en hospitalisation complète »", "journées", "SAE, table MCO", "nombre ; vide mis à 0 si jou_obs est nul (décision 1)"),
    "jli_mco": _e("quantité MCO", "« Journées exploitables de MCO en hospitalisation complète »", "journées", "SAE, table MCO", "nombre ; vide mis à 0 si jou_mco est nul (décision 1)"),
    "jou_med": _e("quantité MCO", "« Journées de médecine en hospitalisation complète »", "journées", "SAE, table MCO", "nombre (décision 3)"),
    "jou_chi": _e("quantité MCO", "« Journées de chirurgie en hospitalisation complète »", "journées", "SAE, table MCO", "nombre (décision 3)"),
    "jou_obs": _e("quantité MCO", "« Journées de gynécologie-obstétrique en hospitalisation complète »", "journées", "SAE, table MCO", "nombre (décision 3)"),
    "jou_mco": _e("quantité MCO", "« Journées de MCO en hospitalisation complète »", "journées", "SAE, table MCO", "nombre (décision 3)"),
    "sejhc_med": _e("quantité MCO", "« Séjours de médecine en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sejhc_chi": _e("quantité MCO", "« Séjours de chirurgie en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sejhc_obs": _e("quantité MCO", "« Séjours de gynécologie-obstétrique en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sejhc_mco": _e("quantité MCO", "« Séjours de MCO en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sej0_med": _e("quantité MCO", "« dont : Séjours de 0 jour de médecine en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sej0_chi": _e("quantité MCO", "« dont séjours de 0 jour de chirurgie en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sej0_obs": _e("quantité MCO", "« dont séjours de 0 jour de gynécologie-obstétrique en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "sej0_mco": _e("quantité MCO", "« dont séjours de 0 jour de MCO en hospitalisation complète »", "séjours", "SAE, table MCO", "nombre (décision 3)"),
    "pla_med": _e("quantité MCO", "« Places de médecine en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 »", "places", "SAE, table MCO", "nombre ; vide mis à 0 si sejhp_med est nul (décision 1)"),
    "pla_chi": _e("quantité MCO", "« Places de chirurgie en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 »", "places", "SAE, table MCO", "nombre ; vide mis à 0 si sejhp_chi est nul (décision 1)"),
    "pla_obs": _e("quantité MCO", "« Places de gynécologie-obstétrique en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 »", "places", "SAE, table MCO", "nombre ; vide mis à 0 si sejhp_obs est nul (décision 1)"),
    "pla_mco": _e("quantité MCO", "« Places de MCO en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 »", "places", "SAE, table MCO", "nombre ; vide mis à 0 si sejhp_mco est nul (décision 1)"),
    "sejhp_med": _e("quantité MCO", "« Séjours de médecine en hospitalisation partielle ou ambulatoire »", "venues (une venue = une journée)", "SAE, table MCO", "nombre (décision 3)"),
    "sejhp_chi": _e("quantité MCO", "« Séjours de chirurgie en hospitalisation partielle ou ambulatoire »", "venues (une venue = une journée)", "SAE, table MCO", "nombre (décision 3)"),
    "sejhp_obs": _e("quantité MCO", "« Séjours de gynécologie-obstétrique en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire »", "venues (une venue = une journée)", "SAE, table MCO", "nombre (décision 3)"),
    "sejhp_mco": _e("quantité MCO", "« Séjours de MCO en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire »", "venues (une venue = une journée)", "SAE, table MCO", "nombre (décision 3)"),
    "sea_mco": _e("quantité MCO", "« Nombre de séances de MCO (CM 28) » : dialyse, chimiothérapie, radiothérapie", "séances", "SAE, table MCO", "nombre (décision 3) ; hors de l'activité"),

    # Incohérences repérées, jamais corrigées (décision 2)
    "inc_lits_vides_avec_journees": _e("incohérence repérée", "Lits non renseignés alors qu'il y a des journées",
                                       "0/1", "calculée", "lit_mco vide et jou_mco > 0"),
    "inc_places_vides_avec_venues": _e("incohérence repérée", "Places non renseignées alors qu'il y a des venues",
                                       "0/1", "calculée", "pla_mco vide et sejhp_mco > 0"),
    "inc_sej0_superieur_a_sejhc": _e("incohérence repérée", "Plus de séjours de 0 jour que de séjours de complète",
                                     "0/1", "calculée", "sej0_mco > sejhc_mco"),
    "inc_jou_trop_bas": _e("incohérence repérée", "Moins de journées que de séjours d'au moins une nuit",
                           "0/1", "calculée", "jou_mco < sejhc_mco − sej0_mco"),
    "inc_lits_zero_avec_journees": _e("incohérence repérée", "Zéro lit déclaré alors qu'il y a des journées",
                                      "0/1", "calculée", "lit_mco = 0 et jou_mco > 0"),

    # Identité (table ID)
    "rs": _e("identité", "« Raison sociale de l'entité interrogée »", "texte", "SAE, table ID", "jointure sur (fi, an)"),
    "fi_ej": _e("identité", "« N° FINESS de l'entité juridique » : le groupe auquel appartient le site", "code",
                "SAE, table ID", "jointure sur (fi, an)"),
    "stjr": _e("identité", "« Statut juridique regroupé (1 : Public, 2 : Privé lucratif, 3 : Privé non lucratif) »", "code", "SAE, table ID", "jointure sur (fi, an)"),
    "catr": _e("identité", "« Catégorie d'établissement regroupée » : statut (PUB, PNL, PLU) et type, ex. PUB1 = CHR/CHU, "
               "PUB2 = centres hospitaliers, PLU4 = privé lucratif de courte durée ou pluridisciplinaire "
               "(libellés : Nomenclatures_2024.xls)", "code", "SAE, table ID", "jointure sur (fi, an)"),
    "dep": _e("identité", "« Département »", "code", "SAE, table ID", "jointure sur (fi, an) ; texte (2A, 2B, 9A…)"),
    "reg_actuelle": _e("identité", "Région actuelle (découpage de 2016), y compris avant 2016", "code",
                       "calculée à partir de dep",
                       "correspondance département -> région des tables ID 2016 à 2025 (décision 4)"),

    # Indicateurs tirés des autres tables (décision 5) : absent de la table -> 0
    "a_pediatrie": _e("indicateur d'une autre table", "« Existe t-il un (ou plusieurs) service(s) ou une unité pédiatrique dans l'établissement (avec une UM typée dans le PMSI-MCO) ? »", "0/1", "SAE, table MCOPED",
                      "1 si sped = 1, sinon 0"),
    "a_geriatrie": _e("indicateur d'une autre table", "« Existe t-il un (ou plusieurs) service(s) ou une unité de médecine gériatrique dans l'établissement (avec une UM typée dans le PMSI-MCO)? »", "0/1",
                      "SAE, table MCOGER", "1 si uger = 1, sinon 0"),
    "a_unv": _e("indicateur d'une autre table", "« Existe-t-il une unité neurovasculaire (UNV) dans l'établissement (avec une UM typée dans le PMSI-MCO)? »", "0/1", "SAE, table MCOAVC",
                "1 si unv = 1, sinon 0"),
    "a_urgences": _e("indicateur d'une autre table", "« Sur le site géographique, disposez-vous d'une implantation d'une structure d'urgences autorisée ? »", "0/1", "SAE, table URGENCES",
                     "1 si autsu = 1, sinon 0"),
    "a_smr": _e("indicateur d'une autre table", "Activité de soins médicaux et de réadaptation en hospitalisation "
                "complète dans l'année", "0/1", "SAE, table SSR (SMR en 2025)",
                "1 si la ligne SSR_TOT (« Type d'activité autorisée de SSR » : total) compte au moins un séjour (sejhc > 0)"),
}


def table_dictionnaire(panel):
    """Le dictionnaire sous forme de table, dans l'ordre des colonnes du panel, avec la part de cases vides."""
    lignes = []
    for colonne in panel.columns:
        e = DICTIONNAIRE[colonne]
        lignes.append({"colonne": colonne, **e,
                       "vides_pct": round(100 * panel[colonne].isna().mean(), 2)})
    return pd.DataFrame(lignes)


def colonnes_sans_definition(panel):
    """Colonnes du panel absentes du dictionnaire, et définitions sans colonne dans le panel."""
    return sorted(set(panel.columns) - set(DICTIONNAIRE)), sorted(set(DICTIONNAIRE) - set(panel.columns))


def vers_markdown(dico, lignes_panel):
    """Texte de docs/dictionnaire.md."""
    texte = ["# Dictionnaire des colonnes du panel", "",
             f"Panel : `donnees/preparees/panel_mco.parquet` (non versionné, régénéré par `scripts/03_panel.py`) : "
             f"une ligne par établissement et par année, {lignes_panel} lignes, {len(dico)} colonnes.", "",
             "Ce fichier est écrit par `scripts/06_dictionnaire.py` : ne pas le modifier à la main. Les définitions "
             "sont dans `src/dictionnaire.py` ; les libellés entre guillemets sont ceux de la DREES (« Liste variables "
             "SAE 2024 »). Les décisions citées sont dans `docs/nettoyage_donnees.md`. Cases vides : part mesurée "
             "sur le panel.", ""]
    for groupe in GROUPES:
        bloc = dico[dico["groupe"] == groupe]
        if bloc.empty:
            continue
        texte += [f"## {groupe[0].upper() + groupe[1:]}", "",
                  "| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |",
                  "|---|---|---|---|---|--:|"]
        for _, r in bloc.iterrows():
            cellules = [f"`{r['colonne']}`", r["definition"], r["unite"], r["source"], r["regle"],
                        f"{r['vides_pct']:.2f}"]
            texte.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cellules) + " |")
        texte.append("")
    return "\n".join(texte)
