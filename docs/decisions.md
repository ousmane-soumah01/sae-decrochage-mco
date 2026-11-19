# Journal des décisions

Chaque choix du projet est noté ici avec sa justification et, le cas échéant, sa preuve.
Les valeurs elles-mêmes sont dans `config.yaml`.

---

## Données

**Encodage des fichiers : Windows-1252 de 2013 à 2024, UTF-8 en 2025**
Ces valeurs viennent de l'exploration des archives faite au départ du projet ; elles sont démontrées par `scripts/01_extraire.py`, avant toute lecture. Pour chacun des 91 fichiers extraits, 7 encodages sont essayés (UTF-8, UTF-16, Windows-1252, Latin-1, ISO-8859-15, CP850, Mac Roman) et seuls sont gardés ceux qui donnent un en-tête correct (colonnes `AN` et `FI`) et un texte plausible (aucun caractère invisible, aucun caractère étranger au français). Résultat (`resultats/01_qualite_donnees/tableaux/encodages.csv`) :
- 2013 à 2024 : Windows-1252 marche pour tous les fichiers de chaque année ; en 2017 et 2020, Latin-1 et ISO-8859-15 marchent aussi (aucun fichier de ces années ne contient les caractères qui les distinguent, comme « ’ » ou « Œ ») ;
- 2015 : `ID_2015r.csv` ne se lit en Windows-1252 qu'à quelques octets près (au plus 10 tolérés) ; les autres fichiers de 2015 se lisent sans aucune erreur ;
- 2025 : seul l'UTF-8 marche.
Lire un fichier UTF-8 en Windows-1252 ne provoque aucune erreur mais abîme tous les accents (« é » devient « Ã© ») : c'est pourquoi la vérification précède toute lecture, et le script s'arrête si l'encodage de `config.yaml` n'est pas parmi les encodages qui marchent.

**Octet illisible : remplacé par « � » et compté, pas d'arrêt**
À la lecture, `src.chargement.octets_invalides` mesure la position exacte de chaque octet qui n'existe pas dans l'encodage du fichier. Sur les 91 fichiers, un seul octet est concerné : `ID_2015r.csv`, position 975 187 (`resultats/01_qualite_donnees/tableaux/extraction.csv`). Il est remplacé par « � » et documenté : une faute de frappe isolée ne justifie pas de bloquer tout le projet.

**Lecture sans interprétation**
Toutes les colonnes sont lues comme du texte (le FINESS « 010000024 » garde son zéro de tête, rien n'est converti en silence) ; seule une case vide est considérée comme manquante (« NA » reste du texte).

**Noms de colonnes en minuscules**
Les noms de colonnes sont mis en minuscules à la lecture (`fi`, `an`, `jou_mco`…), quelle que soit leur casse dans le fichier d'origine : tout le code du projet écrit les colonnes de la même façon. La clé de `config.yaml` s'écrit donc `[fi, an]`.

## Mesure de l'activité

**Activité = `jou_mco` + 0,5 × (`sejhp_mco` + `sej0_mco`), en journées-équivalentes** *(validée le 13/11/2026)*
Pré-analyse (`scripts/04_preanalyse.py`, `resultats/02_preanalyse/tableaux/composantes_nationales.csv`, `sejours_0_jour.csv`, `mesures_comparees.csv`), trois mesures comparées sur le panel 2013-2025 :
- *Séjours* (`sejhc_mco + sejhp_mco`) : un séjour d'un jour compte autant qu'un séjour d'un mois, alors qu'un séjour de complète d'au moins une nuit compte en moyenne 5,6 à 5,8 journées. Elle suit le virage ambulatoire (la partielle passe de 33,3 % des séjours en 2013 à 48,8 % en 2025) plus que le volume de travail ; c'est la mesure la plus éloignée des autres (corrélation de rang 0,901 avec la mesure retenue).
- *Journées de complète seules* (`jou_mco`) : aveugle à la partielle (682 lignes ont 0 journée mais de la partielle) et aux séjours de 0 jour (les 12 lignes dont tous les séjours de complète font 0 jour ont 0 journée), qui représentent 9,4 à 13,5 % des séjours de complète selon l'année.
- *Journées-équivalentes* : les journées de complète, plus une fraction p d'une journée par venue de partielle et par séjour de 0 jour. Une venue dure une journée, mais rester la nuit n'équivaut pas à venir et repartir : p = 0,5. Pour la ligne médiane, passer de p = 1/3 à p = 1 ne change l'activité que de 6,5 % ; pour 1 077 lignes (établissements surtout ambulatoires), elle double ou plus : p = 1/3 et p = 1 sont gardés pour l'analyse de robustesse.

Les séances (`sea_mco` : dialyse, chimiothérapie, radiothérapie ; environ 10 millions par an, sur 15 527 lignes) sont des actes courts et répétés, d'une autre nature : elles restent hors de l'activité, comme variable explicative.

## Périmètre

**France entière, activité MCO seule** *(06/11/2026)*
Le MCO, le SMR, la psychiatrie et l'HAD sont des activités différentes : on ne les mélange pas. La France entière donne assez d'exemples pour apprendre ; la région est une variable, et les résultats seront analysés par région (zoom Occitanie).

**Seuil des petits établissements : 1 000 journées-équivalentes en t** *(validé le 13/11/2026)*
Pour un très petit établissement, quelques journées de plus ou de moins font des évolutions énormes, sans rapport avec un décrochage. Pré-analyse (`seuil_petits_etablissements.csv`, `instabilite_par_taille.csv`), sur les établissements actifs de 2013 à 2025 :

| Seuil | Établissements écartés par an | Part de l'activité nationale écartée (année maximale) |
|--:|--:|--:|
| 365 | 23 à 35 | 0,011 % |
| 1 000 | 56 à 75 | 0,060 % |
| 3 650 | 219 à 257 | 0,822 % |

| Activité en t | Écart interquartile des évolutions d'une année sur l'autre | Part des évolutions de plus de ±50 % |
|---|--:|--:|
| 100 à 365 | 43 points | 21 % |
| 365 à 1 000 | 48 points | 24 % |
| 1 000 à 3 650 | 22 points | 8 % |
| 3 650 et plus | 8,5 points | 1 % |

Entre 365 et 1 000 journées-équivalentes, les établissements sont aussi instables qu'entre 100 et 365 : un seuil à 365 garderait des « décrochages » de bruit. À 1 000, l'instabilité chute nettement, pour 0,06 % de l'activité nationale. Le seuil de 365 est gardé pour l'analyse de robustesse. Les lignes d'activité nulle (1 113) ou inconnue (20) sont écartées quel que soit le seuil.

## Cible

**Référence : l'évolution nationale pondérée par l'activité** *(validée le 13/11/2026)*
Référence d'un passage t → t+1 = somme des activités en t+1 ÷ somme des activités en t − 1, sur les établissements au-dessus du seuil en t et actifs en t+1. C'est l'évolution de l'activité MCO de toute la France : chaque établissement compte selon son activité. Une référence qui change chaque année est indispensable : en 2019→20, l'activité baisse d'environ 10 % partout (Covid), et un établissement qui suit ce mouvement n'a pas décroché.
Pré-analyse (`references_candidates.csv`, figure `references_candidates.png`), sur 1 406 à 1 523 établissements par passage : la médiane, la moyenne simple et l'évolution pondérée racontent la même histoire (légère baisse jusqu'en 2019, environ −10 % en 2019→20, rebond de +2,3 à +2,8 % en 2020→21, petite hausse ensuite) et restent à moins de 1,4 point l'une de l'autre. La moyenne simple est tirée par quelques évolutions extrêmes (jusqu'à +1 590 % en 2019→20) : +1,99 % en 2022→23 contre +1,23 % pour la médiane et +0,60 % pour la pondérée. La pondérée a un sens national clair et ne réagit pas aux pourcentages extrêmes des petits établissements. La médiane est gardée pour l'analyse de robustesse.

**Décrochage : évolution inférieure à la référence − 15 points** *(validé le 13/11/2026)*
L'écart à la référence, en points, est l'évolution de l'établissement moins la référence de l'année ; il y a décrochage si cet écart est strictement inférieur à −15. Pré-analyse (`ecarts_par_passage.csv`, figure `borne_tukey_et_seuils.png`), sur les établissements actifs en t et t+1 :
- les années normales (2013→14 à 2018→19, 2022→23 à 2024→25), la moitié centrale des établissements tient dans une bande de 6,5 à 9,1 points (écart interquartile) : un écart de −10 points reste proche du bruit ordinaire (environ 10 % des établissements chaque année) ;
- sur ces 9 passages, la borne de Tukey (Q1 − 1,5 × écart interquartile) va de −13,8 à −17,9 points (moyenne −15,9) : −15 points se situe au cœur de la zone « anormale » ;
- la borne de Tukey descend à −22,4 et −23,9 points en 2019→20 et 2020→21 : une règle qui la suivrait serait moins sévère précisément pendant la crise (3,2 % de décrochages en 2019→20, contre 5,6 % en 2013→14) ;
- avec −15 points fixe : 5,2 à 6,4 % de décrochages les années normales, 8,1 % et 11,3 % pendant le Covid ; le décrochage garde le même sens chaque année.
Variantes gardées pour l'analyse de robustesse : −10 points et la règle de Tukey.
*Points et pourcentages.* L'évolution d'un établissement s'exprime en % ; l'écart entre deux pourcentages s'exprime en points. « Référence − 15 points » n'est donc ni « −15 % » ni « 15 % de la référence » : le seuil en % dépend de l'année. Il vaut −13,58 % en 2023→24 (référence +1,42 %), −15,42 % en 2018→19 (référence −0,42 %) et −24,47 % en 2019→20 (référence −9,47 %) : pendant le Covid, un établissement à −15 % a suivi le mouvement général et ne décroche pas.

**Sorties : un établissement inactif en t+1 décroche (y = 1)** *(validé le 13/11/2026)*
Pré-analyse (`sorties_par_passage.csv`) : 7 à 30 sorties par passage, 226 en tout, presque toutes des disparitions de la SAE (2 seulement présentes avec une activité nulle) ; ce ne sont pas des établissements minuscules (activité médiane l'année d'avant : 2 670 à 10 873 journées-équivalentes). Disparaître est le décrochage le plus extrême. Exception : 13 sorties réapparaissent plus tard dans la SAE (7 dès l'année suivante) ; leur activité en t+1 est inconnue (trou de déclaration ou fermeture temporaire) : classe « inconnue », retirées des lignes évaluées.

**Restructurations probables : la baisse retrouvée ailleurs, mesurée ou déclarée** *(validé le 13/11/2026)*
Un décrochage ou une sortie est une restructuration probable si (1) au moins 50 % de la perte du site est retrouvée dans les autres sites du même groupe, au-delà de leur croissance normale (un nouveau numéro FINESS dans le groupe compte pour toute son activité), ou (2) si le FINESS du site est cité dans une fusion ou une scission déclarée par un autre établissement (`fifu1-3`, `scfu1-3`), en t ou en t+1. Les restructurations probables sont gardées dans la table, avec un indicateur, et retirées des lignes évaluées ; au test final, les scores sont donnés avec et sans elles.
Pourquoi pas « le groupe ne décroche pas » : un groupe peut absorber la baisse d'un site sans rien lui reprendre (les autres sites croissent normalement). Pré-analyse (`compensation_dans_le_groupe.csv`, `groupes_et_restructurations.csv`, `finess_qui_changent.csv`), sur 1 143 décrochages et 226 sorties :
- la compensation médiane, dans les groupes d'au moins 2 sites, vaut 24 % pour les décrochages et 98 % pour les sorties : quand un site disparaît dans un groupe, son activité réapparaît presque toujours ailleurs dans le groupe ; quand un site baisse, presque jamais ;
- l'ancienne règle aurait classé en restructuration 172 décrochages dont moins de la moitié de la perte se retrouve dans le groupe ; dans les groupes de 6 sites ou plus, la compensation médiane est nulle (−4 %) : le groupe ne baisse pas parce qu'il est grand ;
- la citation dans une fusion ou une scission repère des cas que la compensation ne voit pas (absorption par un établissement d'un autre groupe) : 24 décrochages et 20 sorties sans compensation ;
- au total : 183 décrochages et 118 sorties, contre 429 cas avec l'ancienne règle ; une fois retirées les 13 réapparitions (classe « inconnue »), le code (`src/cible.py`) compte 183 décrochages et 114 sorties restructurations probables, sur 1 143 décrochages et 213 sorties.
`modej` (« modification de l'entité juridique ») n'est pas une preuve de transfert (un rachat ne déplace pas l'activité) : on le garde comme information, avec l'indicateur `changement_de_groupe` (186 passages). Variantes pour l'analyse de robustesse : compensation de 80 %, compensation seule sans les fusions, ancienne règle. Limite : la SAE ne suit pas les patients ; une restructuration reste une présomption.

**Reprise des capacités par un autre site** *(validé le 19/11/2026)*
Un décrochage ou une sortie est aussi une restructuration probable si (3) ses lits et places MCO sont repris en t+1 par un autre site du même département : le site perd au moins 30 lits et places et **toutes ses capacités** (absent en t+1, ou 0 lit et 0 place : il ferme ; un site qui garde des lits décroche) ; un autre site gagne la même capacité (à 2 près ou à 10 % près) ; au plus 6 sites sont dans ce cas en France ; et le repreneur gagne au moins la moitié de l'activité perdue (`config.yaml` › `cible.reprise`, `src/cible.py` › `reprises_de_capacites`). La colonne `reprise_meme_ej` dit si le repreneur est dans la même entité juridique ; elle est une information, pas une variable explicative (elle vient de t+1, comme `reprise_capacites`).
Vocabulaire, selon la SAE et l'observation de terrain : un **transfert** est un déménagement du même établissement ; il change de FINESS géographique (le FINESS porte le département dans ses premiers chiffres : vrai pour 96,8 % des lignes du panel, les écarts sont des codes d'outre-mer) mais garde son entité juridique. Un **regroupement** réunit des établissements ; une **fusion** réunit des entités juridiques, par absorption (l'une garde son FINESS et change de périmètre) ou par création d'une nouvelle entité. Le guide de remplissage (SAE_AR_2024) précise que le transfert d'activité entre établissements d'une même entité n'est pas codé (seulement en commentaire), et qu'un établissement fermé en cours d'année déclare l'activité faite avant la fermeture, ses capacités étant celles du 31 décembre (d'où des journées avec 0 lit).
Pré-analyse (`scripts/04_preanalyse.py`, question 7, cible d'avant cette règle ; perte d'au moins 30 % des capacités, puis vérification que le site disparaît) :
- les mouvements déclarés dans la table ID (`chlej0`, `fipre`, `modej`, `typmd1-3`, `fifu1-3`, `scfu1-3`) ne suffisent pas comme preuve (`mouvements_declares.csv`) : à l'entraînement, au moins un mouvement déclaré pour 6,7 % des lignes stables, 8,9 % des décrochages gardés et 17,0 % des sorties gardées ; `fiaut1-7` et `rsaut1-7` décrivent les autres structures installées dans l'établissement (imagerie, laboratoire), pas une restructuration ;
- chercher la même capacité « partout », sans condition, ne prouve rien : 80 à 96 % des fortes pertes trouvent une correspondance, chez les stables comme dans le placebo (gains de t−1 à t, qui ne peuvent pas venir de la perte) ;
- la règle stricte sépare (`reprise_capacites.csv`, seuil 30, entraînement) : reprise pour 1 stable sur 34 (2,9 %), 4 décrochages gardés sur 42 (9,5 %), 6 sorties gardées sur 23 (26,1 %), placebo à 0 % pour ces trois groupes ; elle retrouve aussi 14 cas déjà repérés par les règles (1) et (2) ;
- seuil de 20 lits et places : les mêmes 14 nouveaux cas, stables à 1,9 % et placebo à 0 % ; le seuil de 30 est retenu ;
- 28 passages y = 1 avec une reprise, dont 14 nouveaux (`reprises_trouvees.csv`) : aucun des 14 n'a son repreneur dans la même entité juridique (9 sur 14 parmi les cas déjà repérés). Aucun n'est donc un transfert : 10 sont le même établissement repris par un autre exploitant (souvent un GCS du même nom, ou « Nouvelle clinique… », parfois déclaré en `fipre`), 4 une activité absorbée par un hôpital d'une autre entité.
- l'ancien site a-t-il vraiment disparu ? (colonnes `capacite_t1` et `annees_dans_la_sae_apres_t`) Pour 12 des 14 : oui. Les 9 sorties ne sont plus jamais dans la SAE ; 3 décrochages (Clinique des Diaconesses en 2015, Clinique chirurgicale du Libournais en 2018, Clinique du Pays de Seine en 2023) déclarent 0 lit et 0 place en t+1, une activité résiduelle (fermeture en cours d'année), puis disparaissent. Les 2 autres gardent des lits et restent dans la SAE jusqu'en 2025 : HIA Desgenettes (2017 : 136 → 79 lits et places, activité qui baisse ensuite chaque année) et Hôpital privé d'Athis-Mons, site Caron (2018 : 64 → 25, activité qui remonte ensuite). Ce ne sont pas des reprises : la règle exige que le site perde toutes ses capacités, et ces 2 cas restent des décrochages (y = 1).
Effet : 12 lignes y = 1 de plus mises à part, 8 à l'entraînement (6 sorties, 2 décrochages), 3 au test, 1 dans les passages Covid. Ces lignes ne sont ni des décrochages ni des stables : elles sont retirées des lignes évaluées (`cible.retirer_restructurations`), le modèle ne les voit pas. Elles ne passent pas à y = 0 : la preuve de la reprise n'existe qu'en t+1, et le modèle apprendrait qu'un site sur le point de fermer est stable. Limites : les seuils ont été choisis en regardant ces données ; les deux sites de Guyane de 2024 passent sous une même nouvelle entité en 2025, à vérifier dans le répertoire FINESS. Variante pour l'analyse de robustesse : cible sans cette règle (`cible.reprise.active: false`).

## Découpage et évaluation

Vocabulaire. Une **ligne évaluée** est un passage t → t+1 dont la cible est connue (y = 0 ou 1) et qui n'est pas une restructuration probable. Un **pli** est un couple (années d'entraînement, année de validation). Pré-analyse : `scripts/04_preanalyse.py`, question 6. Fonctions : `src/decoupage.py`.

**Validation croisée à fenêtre croissante, par année t** *(validé le 14/11/2026)*
On apprend sur les années t passées et on valide sur l'année suivante : apprendre sur 2013, valider sur 2014 ; apprendre sur 2013–2014, valider sur 2015 ; et ainsi de suite. Le modèle n'apprend jamais sur l'avenir. Les plis n'ont pas la même taille, puisque le nombre d'établissements change d'une année à l'autre.
Le découpage se fait sur l'année t de la ligne, pas sur les lignes (`plis_timeseriessplit.csv`). `TimeSeriesSplit` de scikit-learn ne met jamais l'avenir dans l'entraînement, mais il coupe le tableau trié en blocs de lignes de même taille (1 453 lignes ici), sans tenir compte des années : sur les 11 627 lignes d'entraînement, ses 7 plis ont tous une même année des deux côtés (pli 1 : validation sur 64 lignes de 2013 et 1 389 de 2014) et le pli 6 mélange 2018 et 2021. Les plis par année (`plis_par_annee`) n'ont aucun de ces défauts.
Pas de fuite : la cible d'une ligne t dépend de t+1 ; quand on valide sur l'année v, les cibles d'entraînement dépendent au plus de l'année v, connue au moment de prédire pour v.

**Passages Covid retirés de l'entraînement et du test, analysés à part** *(validé le 14/11/2026)*
L'année 2020 intervient dans deux passages : 2019→2020 (la chute) et 2020→2021 (la remontée). Pré-analyse (`lignes_par_passage.csv`, figure `covid_et_test.png`), part de y = 1 parmi les lignes évaluées :

| Passage | Lignes évaluées | y = 1 | Part de y = 1 | Référence nationale |
|---|--:|--:|--:|--:|
| 2013→2014 à 2018→2019 | 1 446 à 1 520 | 64 à 94 | 4,4 % à 6,2 % | −0,4 % à −1,2 % |
| 2019→2020 | 1 435 | 121 | 8,4 % | −9,5 % |
| 2020→2021 | 1 402 | 142 | 10,1 % | +2,8 % |
| 2021→2022 | 1 412 | 93 | 6,6 % | −0,1 % |
| 2022→2023 à 2024→2025 | 1 399 à 1 406 | 70 à 82 | 5,0 % à 5,8 % | +0,6 % à +1,4 % |

La référence nationale absorbe la baisse commune, pas les écarts entre établissements, qui s'élargissent ces deux années-là. Le rattrapage est réel mais partiel (`indice_activite_base_2019.csv`, 1 329 établissements actifs les 13 années, indice 2019 = 100) : médiane 89,5 en 2020 et 95,0 en 2024 ; le quart du bas reste entre 82 et 84 de 2020 à 2025 ; le quart du haut dépasse 104 dès 2024. Ces deux passages (2 837 lignes, 263 y = 1) sont analysés à part, comme test de résistance du modèle. 2018→2019 (5,1 %) et 2021→2022 (6,6 %, proche de 2013→2014 : 6,2 %) sont gardés ; 2021→2022 est surveillé.
Ne pas confondre avec la section Cible (8,1 % et 11,3 % pendant le Covid) : là, ce sont les décrochages seuls, sur tous les passages ; ici, les y = 1 (décrochages et sorties), sur les lignes évaluées.

**Test final : t = 2023 et 2024, utilisé une seule fois** *(validé le 14/11/2026)*
Sans les passages Covid, il reste 10 années, 14 432 lignes évaluées, 796 y = 1 (`proportion_test.csv`) :

| Test final | Lignes | Part | y = 1 au test |
|---|--:|--:|--:|
| 1 an (t = 2024) | 1 406 | 9,7 % | 82 |
| **2 ans (t = 2023, 2024)** | **2 805** | **19,4 %** | **152** |
| 3 ans (t = 2022 à 2024) | 4 206 | 29,1 % | 232 |

Deux ans donnent le partage 80 / 20 visé et une part de y = 1 presque identique des deux côtés (5,5 % à l'entraînement, 5,4 % au test). Un an laisse trop peu de décrochages pour mesurer de façon stable ; trois ans retirent 29 % des lignes et ne laissent qu'un passage d'après le Covid à l'entraînement. Le gain de précision au test avec trois ans est faible : pour un rappel autour de 50 %, la marge à 95 % passe d'environ ±8 points (152 cas) à environ ±6 points (232 cas).
Entraînement et validation croisée : t = 2013 à 2018, 2021 et 2022 (11 627 lignes, 80,6 %, 644 y = 1). Le modèle est choisi en validation croisée seulement ; le test mesure le modèle retenu, une fois, à la fin.
*Mise à jour du 19/11/2026, après la reprise des capacités (section Cible)* : entraînement 11 619 lignes, 636 y = 1 (5,47 % ; « toujours 0 » : 94,53 % d'exactitude) ; test 2 802 lignes, 149 y = 1 (5,32 %) ; passages Covid 2 836 lignes, 262 y = 1 (`resultats/03_exploration/tableaux/table_modelisation_controles.csv`). Les chiffres de cette section et les tableaux de la question 6 gardent la cible telle qu'elle était à ces décisions ; le partage reste à 80 / 20 environ.

**Pas de variable du passé au départ** *(validé le 14/11/2026)*
Les premiers modèles n'utilisent que l'état de l'établissement en t. On testera ensuite l'évolution de t−1 à t ; elle sera vide pour t = 2013 (pas d'année avant) et pour t = 2021 (2020 n'est utilisé nulle part). Elle est gardée seulement si la validation croisée montre qu'elle aide.

**Aucune ligne supprimée, aucune valeur corrigée ; les incohérences deviennent des variables** *(validé le 14/11/2026)*
Les cinq indicateurs `inc_*` entrent dans le modèle : une activité sans capacité déclarée peut signaler un changement administratif (observation de terrain : activité rattachée d'abord à l'entité juridique, puis à un nouveau site), donc peut-être un décrochage à venir. Retirer ces lignes rendrait le modèle aveugle là où il doit voir.

**Cases vides, pour les modèles linéaires seulement** *(validé le 14/11/2026 ; séjours de 0 jour le 19/11/2026)*
La table générale ne change pas ; les modèles à arbres gardent les cases vides. Sur les 14 432 lignes évaluées hors Covid, 710 (4,9 %) ont au moins une case vide, toutes dans les 29 quantités MCO (`cases_vides_modele.csv`) :
- **journées, séjours de complète et venues vides → 0** (`jou_*`, `sejhc_*`, `sejhp_*`) : la capacité correspondante vaut 0 (pour `sejhp_*`, 67 cas sur 68) ; l'établissement n'a pas cette activité ;
- **capacité vide → valeur de remplacement + indicateur « non déclaré »** (`lit_*`, `jli_*`, `pla_*`) : dans 100 % des cas l'activité correspondante est positive (par exemple les 299 `pla_obs` et les 229 `pla_med` vides), puisque la décision 1 du nettoyage a déjà mis à 0 les capacités vides d'activité nulle ; mettre 0 créerait de fausses incohérences (« 0 place, 2 000 venues ») ;
- **séjours de 0 jour (`sej0_*`)** : vide → 0 quand l'établissement n'a pas de lit dans la discipline (37 cases sur 53) ; sinon (16 cases), **valeur de remplacement + indicateur « non déclaré »**. Pré-analyse (`sej0_vides_avec_lits.csv`) : ces 16 absences ne sont pas dues au hasard, 11 tombent en 2024 ; et chacun de ces établissements déclare des séjours de 0 jour les autres années (de 0,3 % à 46,2 % de ses séjours de complète, médiane 7,2 %). 0 serait donc faux. La valeur de remplacement n'utilise que les années passées de l'établissement (2025 pour une ligne de 2024 serait une fuite).
Les valeurs de remplacement sont calculées dans chaque pli, sur l'entraînement seulement. À vérifier avant le test final : `sej0_mco` entre dans l'activité, où une case vide compte pour 0 ; 4 cases `sej0_mco` vides avec des lits sous-estiment un peu l'activité de leur ligne.

**Battre le hasard, pli par pli** *(validé le 14/11/2026)*
À l'entraînement, 5,54 % des lignes ont y = 1 : un modèle qui répond toujours « ne décroche pas » a 94,46 % d'exactitude sans rien prédire. L'exactitude n'est donc pas utilisée. Sur chaque pli, le modèle est comparé à son propre niveau de hasard :

| Score | Niveau du hasard | Ce qu'il mesure |
|---|---|---|
| PR-AUC | part de y = 1 de l'année validée (de 4,4 % en 2015 à 6,6 % en 2021) | trouver les rares décrochages |
| ROC-AUC | 0,5 | classer un décrocheur avant un non-décrocheur |
| Brier | prédiction constante égale à la part de y = 1 | qualité des probabilités |

Une règle naïve simple, à définir avec les modèles, sert d'adversaire plus dur que le hasard.

**Restent ouverts**
- Moyenne pour choisir le modèle : les 7 plis (`decoupage.annees_min_entrainement: 1`), ou les 5 plis qui ont au moins 3 années d'entraînement (validation sur 2016, 2017, 2018, 2021, 2022). Avec une seule année d'entraînement, le modèle gagnant est souvent le plus simple ; compter ces plis tire le choix vers des modèles faits pour peu de données. Les 7 plis sont calculés dans tous les cas (courbe d'apprentissage).
- Valeur de remplacement des cases vides non déclarées : médiane de l'entraînement, ou ratio tiré de l'activité ou des années passées.

## Définitions en phrases simples

- **FINESS** : le numéro d'identification de chaque établissement de santé en France (9 caractères). Un **site** (FINESS géographique, `fi`) est un lieu précis où l'on soigne ; une **entité juridique** (FINESS juridique, `fi_ej`) est la structure qui le possède et le gère, et peut avoir plusieurs sites.
- **Groupe** : dans ce projet, l'ensemble des sites qui ont la même entité juridique une année donnée.
- **Sortie** : un établissement présent et actif en t qui n'apparaît plus, ou n'a plus d'activité, l'année suivante.
- **Réapparition** : un établissement absent une année puis de nouveau présent plus tard ; son activité pendant l'absence est inconnue.
- **Fusion** : deux établissements (ou plus) n'en forment plus qu'un ; l'activité de celui qui est absorbé passe chez l'autre, qui la déclare sous son propre numéro.
- **Scission** : un établissement est coupé en plusieurs ; une partie de son activité continue sous un autre numéro.
- **Changement de numéro FINESS** : le même lieu de soins est déclaré sous un nouveau numéro (souvent après une fusion ou un changement de gestionnaire).
- **Changement d'entité juridique** : le site change de propriétaire ou de gestionnaire (rachat, reprise) ; il continue de soigner au même endroit.
- **Transfert d'activité** : un service ferme sur un site et rouvre sur un autre site du même groupe ; le premier baisse, le second augmente.
- **Compensation** : la part de ce qu'un site a perdu qu'on retrouve en plus dans les autres sites de son groupe, au-delà de leur croissance normale.
- **Restructuration probable** : une baisse ou une disparition qui s'explique très probablement par un transfert, une fusion ou une scission plutôt que par un vrai déclin.
