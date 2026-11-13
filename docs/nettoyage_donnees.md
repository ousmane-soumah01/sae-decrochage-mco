# Journal du nettoyage des données

Ce que l'audit de qualité a mesuré, et les décisions prises à partir de ces mesures.
L'audit ne corrige rien (`scripts/02_audit_qualite.py`) ; les décisions sont appliquées
plus loin, au moment de construire le panel. Tous les chiffres viennent des tableaux de
`resultats/01_qualite_donnees/tableaux/`.

---

## 1. Ce que l'audit a mesuré (13 années, 2013 à 2025)

**Structure (`colonnes_par_annee.csv`).** Les colonnes changent selon les années. Dans la table MCO, 40 colonnes sur 63 sont présentes les 13 années, dont toutes les quantités d'activité et de capacité (journées, séjours, séjours de 0 jour, venues de partielle, lits, places, journées exploitables, séances). Les 23 autres sont des colonnes de personnel (présentes jusqu'en 2022, certaines seulement de 2013 à 2015), d'activité technique ou clinique (2016 à 2022) et la raison sociale `rs` (à partir de 2020). Dans la table ID, des colonnes changent de nom (`com` en 2013-2014 puis `cominsee`, `arm` puis `armt`).

**Valeurs manquantes (`manquants.csv`, figure `manquants_quantites_mco.png`).** Dans la table MCO :
- quantités d'activité : moins de 1 % de cases vides chaque année (`jou_mco`, `sejhc_mco`, `sej0_mco` : au plus 0,3 % ; `sejhp_mco` : 0,6 % ; `sea_mco` : 0,5 %) ; seule exception, `sejhp_med` en 2013 (7,4 %) ;
- capacités, total MCO : `lit_mco` et `jli_mco` 3 à 12 %, `pla_mco` 14 à 26 % ;
- capacités par discipline : jusqu'à 70 % (places d'obstétrique).

**Types (`types.csv`).** Les tables d'activité (MCO, MCOAVC, MCOGER, MCOPED, SSR/SMR, URGENCES) n'ont aucune colonne mêlant nombres et texte. Dans la table ID, 21 colonnes sont « mixtes » : des codes qui ressemblent à des nombres sans en être (départements `2A`, `2B`, `9A`… ; communes `2A004` ; FINESS secondaires `2A0000436`) et des champs d'adresse ou de nom (`numvoi` « 10B », `bp` « BP 10 »…).

**Clés et cohérence (`cles.csv`, `coherence_tables.csv`).** Aucune clé en double (un établissement par table et par année ; pour SSR/SMR, un par type de soins), aucun FINESS mal formé, la colonne `an` vaut toujours l'année du fichier. Aucun établissement des tables d'activité n'est absent de la table ID.

**Règles de l'activité MCO (`controles_mco.csv`).** Aucune valeur négative, aucune ligne avec des journées sans aucun séjour. Deux lignes ont plus de séjours de 0 jour que de séjours de complète (2017, 2020) ; sept ont moins de journées que de séjours d'au moins une nuit (2013, 2015, 2024, 2025). Les lignes sans aucun séjour (complète + partielle) sont nombreuses jusqu'en 2022 (138) puis presque absentes (49 en 2023, 2 en 2024) : la baisse du nombre de lignes MCO à partir de 2023 (1 637 en 2022, 1 528 en 2023, 1 483 en 2024) vient de ces lignes sans activité ; le nombre de lignes avec des séjours reste stable (1 499, 1 479, 1 481).

**Capacités vides et activité.** Sur les 12 colonnes de capacité (lits, journées exploitables, places × médecine, chirurgie, obstétrique, total MCO) et les 13 années, 83 461 cases sont vides : 82 092 (98,4 %) correspondent à une activité nulle, 1 369 à une activité positive. Pour le total MCO : `lit_mco` vide avec des journées sur 39 lignes, `jli_mco` sur 26, `pla_mco` vide avec des venues sur 90 (au plus 16 lignes par an).

---

## 2. Décisions (validées le 13/11/2026)

**Décision 1 — Capacité vide : 0 si l'activité correspondante est nulle.**
Une case de capacité vide (lits, journées exploitables, places) est mise à 0 quand l'activité correspondante (journées pour les lits et journées exploitables, venues pour les places) est nulle ou vide : dans 98,4 % des cas, une capacité vide signifie « pas de capacité ». Quand l'activité est positive, la case reste vide (valeur réellement inconnue) et un indicateur le signale. Le nombre de cases mises à 0 et laissées vides est compté au moment de l'appliquer.

**Décision 2 — Incohérences repérées, jamais corrigées.**
Les lignes qui enfreignent une règle de cohérence (journées trop basses, séjours de 0 jour en trop, capacité vide avec activité…) sont gardées telles quelles et repérées par un indicateur 0/1. On ne sait pas quelle valeur est fausse : on ne la change pas, mais on peut suivre ces lignes et mesurer leur effet.

**Décision 3 — Ce qui n'entre dans aucun calcul reste du texte.**
Identifiants (`fi`, `fi_ej`), codes (`dep`, `com`, `cominsee`, `reg`…), noms et adresses restent du texte : convertis en nombres, ils perdraient « 2A », « 9B » ou leurs zéros de tête. Seules les quantités qui servent aux calculs (lits, journées exploitables, journées, séjours, séjours de 0 jour, places, venues, séances) sont converties en nombres, ainsi que l'année `an`.

**Décision 4 — Région actuelle retrouvée à partir du département, pour toutes les années.**
Mesure sur la table ID : la colonne `reg` code 27 régions de 2013 à 2015 (anciennes régions), puis 18 à partir de 2016 (nouvelles régions de la réforme territoriale), 19 en 2025. De 2016 à 2025, chaque département correspond à une seule région, et tous les départements présents avant 2016 existent après. Règle : `reg_actuelle` = la région que la correspondance département → région des années 2016 à 2025 donne au département, appliquée aux 13 années ; le code s'arrête si un département a deux régions ou n'en a aucune. Ainsi un établissement garde le même code région d'une année à l'autre, et l'Occitanie (`76`) existe dès 2013. La colonne `reg` d'origine, qui change de sens en 2016, n'entre pas dans le panel. La région `05` n'apparaît qu'en 2025, pour un seul établissement (département `9E`) : elle est gardée telle quelle.

---

## 3. Application dans le panel (`scripts/03_panel.py`)

Le panel compte une ligne par établissement et par année de la table MCO : **20 974 lignes** (la somme des 13 fichiers), aucune en double sur `(fi, an)`, 42 colonnes (`donnees/preparees/panel_mco.parquet`, non versionné). Chaque étape est comptée dans `resultats/01_qualite_donnees/tableaux/panel_controles.csv`.

- **Quantités gardées** : les 29 quantités MCO (lits, journées exploitables, journées, séjours, séjours de 0 jour, places, venues, par discipline et pour le total MCO, et séances). Les colonnes de personnel et d'activité technique, absentes certaines années, ne sont pas gardées.
- **Conversion en nombres (décision 3)** : aucune valeur non numérique sur les 29 quantités.
- **Capacités vides (décision 1)** : 82 092 cases mises à 0, 1 369 laissées vides.
- **Incohérences repérées (décision 2)** : `inc_lits_vides_avec_journees` 39 lignes, `inc_places_vides_avec_venues` 90, `inc_sej0_superieur_a_sejhc` 2, `inc_jou_trop_bas` 7, `inc_lits_zero_avec_journees` 116. Ce dernier indicateur (0 lit déclaré alors qu'il y a des journées) n'avait pas été mesuré par l'audit : il est mesuré ici.
- **Identité (table ID)** : `rs`, `fi_ej`, `stjr`, `catr`, `dep` et `reg_actuelle` (décision 4), joints sur `(fi, an)` par une jointure contrôlée (clé unique dans ID, nombre de lignes inchangé). Aucune ligne MCO sans correspondance dans ID ; 102 départements, 19 régions actuelles.
