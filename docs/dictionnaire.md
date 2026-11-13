# Dictionnaire des colonnes du panel

Panel : `donnees/preparees/panel_mco.parquet` (non versionné, régénéré par `scripts/03_panel.py`) : une ligne par établissement et par année, 20974 lignes, 47 colonnes.

Ce fichier est écrit par `scripts/06_dictionnaire.py` : ne pas le modifier à la main. Les définitions sont dans `src/dictionnaire.py` ; les libellés entre guillemets sont ceux de la DREES (« Liste variables SAE 2024 »). Les décisions citées sont dans `docs/nettoyage_donnees.md`. Cases vides : part mesurée sur le panel.

## Clé

| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |
|---|---|---|---|---|--:|
| `fi` | « N° Finess » du site géographique (l'établissement) | code | SAE, table MCO | texte : garde le zéro de tête et le « 2A » / « 2B » de la Corse (décision 3) | 0.00 |
| `an` | Année de la SAE | année | SAE, table MCO | nombre entier | 0.00 |

## Quantité MCO

| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |
|---|---|---|---|---|--:|
| `lit_med` | « Lits de médecine installés en hospitalisation complète au 31/12 » | lits | SAE, table MCO | nombre ; vide mis à 0 si jou_med est nul (décision 1) | 0.40 |
| `lit_chi` | « Lits de chirurgie installés en hospitalisation complète au 31/12 » | lits | SAE, table MCO | nombre ; vide mis à 0 si jou_chi est nul (décision 1) | 0.22 |
| `lit_obs` | « Lits de gynécologie-obstétrique installés en hospitalisation complète au 31/12 » | lits | SAE, table MCO | nombre ; vide mis à 0 si jou_obs est nul (décision 1) | 0.32 |
| `lit_mco` | « Lits de MCO installés en hospitalisation complète au 31/12 » | lits | SAE, table MCO | nombre ; vide mis à 0 si jou_mco est nul (décision 1) | 0.19 |
| `jli_med` | « Journées exploitables de médecine en hospitalisation complète » | journées | SAE, table MCO | nombre ; vide mis à 0 si jou_med est nul (décision 1) | 0.64 |
| `jli_chi` | « Journées exploitables de chirurgie en hospitalisation complète » | journées | SAE, table MCO | nombre ; vide mis à 0 si jou_chi est nul (décision 1) | 0.27 |
| `jli_obs` | « Journées exploitables de gynécologie-obstétrique en hospitalisation complète » | journées | SAE, table MCO | nombre ; vide mis à 0 si jou_obs est nul (décision 1) | 0.51 |
| `jli_mco` | « Journées exploitables de MCO en hospitalisation complète » | journées | SAE, table MCO | nombre ; vide mis à 0 si jou_mco est nul (décision 1) | 0.12 |
| `jou_med` | « Journées de médecine en hospitalisation complète » | journées | SAE, table MCO | nombre (décision 3) | 0.17 |
| `jou_chi` | « Journées de chirurgie en hospitalisation complète » | journées | SAE, table MCO | nombre (décision 3) | 0.21 |
| `jou_obs` | « Journées de gynécologie-obstétrique en hospitalisation complète » | journées | SAE, table MCO | nombre (décision 3) | 0.26 |
| `jou_mco` | « Journées de MCO en hospitalisation complète » | journées | SAE, table MCO | nombre (décision 3) | 0.11 |
| `sejhc_med` | « Séjours de médecine en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.17 |
| `sejhc_chi` | « Séjours de chirurgie en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.21 |
| `sejhc_obs` | « Séjours de gynécologie-obstétrique en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.26 |
| `sejhc_mco` | « Séjours de MCO en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.11 |
| `sej0_med` | « dont : Séjours de 0 jour de médecine en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.24 |
| `sej0_chi` | « dont séjours de 0 jour de chirurgie en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.26 |
| `sej0_obs` | « dont séjours de 0 jour de gynécologie-obstétrique en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.26 |
| `sej0_mco` | « dont séjours de 0 jour de MCO en hospitalisation complète » | séjours | SAE, table MCO | nombre (décision 3) | 0.15 |
| `pla_med` | « Places de médecine en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 » | places | SAE, table MCO | nombre ; vide mis à 0 si sejhp_med est nul (décision 1) | 1.56 |
| `pla_chi` | « Places de chirurgie en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 » | places | SAE, table MCO | nombre ; vide mis à 0 si sejhp_chi est nul (décision 1) | 0.19 |
| `pla_obs` | « Places de gynécologie-obstétrique en hospitalisation partielle ou ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 » | places | SAE, table MCO | nombre ; vide mis à 0 si sejhp_obs est nul (décision 1) | 1.67 |
| `pla_mco` | « Places de MCO en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire (hors postes de dialyse et de chimiothérapie) au 31/12 » | places | SAE, table MCO | nombre ; vide mis à 0 si sejhp_mco est nul (décision 1) | 0.43 |
| `sejhp_med` | « Séjours de médecine en hospitalisation partielle ou ambulatoire » | venues (une venue = une journée) | SAE, table MCO | nombre (décision 3) | 0.88 |
| `sejhp_chi` | « Séjours de chirurgie en hospitalisation partielle ou ambulatoire » | venues (une venue = une journée) | SAE, table MCO | nombre (décision 3) | 0.23 |
| `sejhp_obs` | « Séjours de gynécologie-obstétrique en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire » | venues (une venue = une journée) | SAE, table MCO | nombre (décision 3) | 0.29 |
| `sejhp_mco` | « Séjours de MCO en hospitalisation partielle ou ambulatoire ou chirurgie ambulatoire » | venues (une venue = une journée) | SAE, table MCO | nombre (décision 3) | 0.15 |
| `sea_mco` | « Nombre de séances de MCO (CM 28) » : dialyse, chimiothérapie, radiothérapie | séances | SAE, table MCO | nombre (décision 3) ; hors de l'activité | 0.17 |

## Incohérence repérée

| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |
|---|---|---|---|---|--:|
| `inc_lits_vides_avec_journees` | Lits non renseignés alors qu'il y a des journées | 0/1 | calculée | lit_mco vide et jou_mco > 0 | 0.00 |
| `inc_places_vides_avec_venues` | Places non renseignées alors qu'il y a des venues | 0/1 | calculée | pla_mco vide et sejhp_mco > 0 | 0.00 |
| `inc_sej0_superieur_a_sejhc` | Plus de séjours de 0 jour que de séjours de complète | 0/1 | calculée | sej0_mco > sejhc_mco | 0.00 |
| `inc_jou_trop_bas` | Moins de journées que de séjours d'au moins une nuit | 0/1 | calculée | jou_mco < sejhc_mco − sej0_mco | 0.00 |
| `inc_lits_zero_avec_journees` | Zéro lit déclaré alors qu'il y a des journées | 0/1 | calculée | lit_mco = 0 et jou_mco > 0 | 0.00 |

## Identité

| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |
|---|---|---|---|---|--:|
| `rs` | « Raison sociale de l'entité interrogée » | texte | SAE, table ID | jointure sur (fi, an) | 0.00 |
| `fi_ej` | « N° FINESS de l'entité juridique » : le groupe auquel appartient le site | code | SAE, table ID | jointure sur (fi, an) | 0.00 |
| `stjr` | « Statut juridique regroupé (1 : Public, 2 : Privé lucratif, 3 : Privé non lucratif) » | code | SAE, table ID | jointure sur (fi, an) | 0.00 |
| `catr` | « Catégorie d'établissement regroupée » : statut (PUB, PNL, PLU) et type, ex. PUB1 = CHR/CHU, PUB2 = centres hospitaliers, PLU4 = privé lucratif de courte durée ou pluridisciplinaire (libellés : Nomenclatures_2024.xls) | code | SAE, table ID | jointure sur (fi, an) | 0.00 |
| `dep` | « Département » | code | SAE, table ID | jointure sur (fi, an) ; texte (2A, 2B, 9A…) | 0.00 |
| `reg_actuelle` | Région actuelle (découpage de 2016), y compris avant 2016 | code | calculée à partir de dep | correspondance département -> région des tables ID 2016 à 2025 (décision 4) | 0.00 |

## Indicateur d'une autre table

| Colonne | Définition | Unité | Source | Règle | Cases vides (%) |
|---|---|---|---|---|--:|
| `a_pediatrie` | « Existe t-il un (ou plusieurs) service(s) ou une unité pédiatrique dans l'établissement (avec une UM typée dans le PMSI-MCO) ? » | 0/1 | SAE, table MCOPED | 1 si sped = 1, sinon 0 | 0.00 |
| `a_geriatrie` | « Existe t-il un (ou plusieurs) service(s) ou une unité de médecine gériatrique dans l'établissement (avec une UM typée dans le PMSI-MCO)? » | 0/1 | SAE, table MCOGER | 1 si uger = 1, sinon 0 | 0.00 |
| `a_unv` | « Existe-t-il une unité neurovasculaire (UNV) dans l'établissement (avec une UM typée dans le PMSI-MCO)? » | 0/1 | SAE, table MCOAVC | 1 si unv = 1, sinon 0 | 0.00 |
| `a_urgences` | « Sur le site géographique, disposez-vous d'une implantation d'une structure d'urgences autorisée ? » | 0/1 | SAE, table URGENCES | 1 si autsu = 1, sinon 0 | 0.00 |
| `a_smr` | Activité de soins médicaux et de réadaptation en hospitalisation complète dans l'année | 0/1 | SAE, table SSR (SMR en 2025) | 1 si la ligne SSR_TOT (« Type d'activité autorisée de SSR » : total) compte au moins un séjour (sejhc > 0) | 0.00 |
