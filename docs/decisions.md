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

**Sites avec des lits ou des places MCO en t (règle de champ)** *(validé le 20/11/2026)*
Un passage t → t+1 n'entre dans l'étude que si le site déclare des lits ou des places MCO en t (lits + places > 0, cases vides comptées 0 ; `config.yaml` › `perimetre.capacite_mco_requise`, `src/cible.py` › `sans_capacite_mco`, appliquée par `src/decoupage.py` › `lignes_evaluees`). Sans capacité MCO au 31 décembre de t, le site n'est plus un établissement MCO à cette date ; en production, il sera signalé « capacité MCO nulle ou non saisie : à vérifier » plutôt que noté.
Principe : **la cible peut regarder l'avenir, la sélection des lignes et les variables non.** y est un résultat : il a le droit d'utiliser t+1 et au-delà. Choisir les lignes avec l'avenir crée un biais de sélection. Deux règles ont été écartées pour cette raison : « 0 lit en t et plus aucune activité MCO après t » retirait les sites à 0 lit qui s'arrêtent et gardait ceux qui continuent (le modèle aurait appris « 0 lit, donc pas de sortie », et le filtre est inapplicable en production) ; « retirer le passage qui suit une fermeture en cours d'année » regarde aussi après t, puisque la fermeture en cours d'année exige « plus aucune activité après t ». La règle de champ ne lit que t.
Pré-analyse (`scripts/04_preanalyse.py`, question 9 ; `champ_lignes_zero_capacite.csv`, `champ_par_partie.csv`, `champ_controle_indicateur.csv`) : 47 lignes évaluées déclarent 0 lit et 0 place MCO en t. Décrites en regardant la suite : 31 passages qui suivent une fermeture en cours d'année (le même événement compté deux fois, et trivial à prédire), 6 fermetures pendant 2013 (sans passage avant pour les compter), 7 capacités non saisies (des lits l'année d'avant et l'année d'après, par exemple 28 → 0 → 20), 3 sans année d'avant connue. Toutes sont retirées, qu'elles sortent ou non : 37 sorties, 7 décrochages, 3 stables. Le coût est assumé : 10 lignes qui ne sont pas des sorties, des erreurs de déclaration qu'il vaut mieux signaler que prédire. Le passage où le site ferme garde son y = 1 ; seul le passage suivant sort du champ.
Effet : 32 lignes retirées à l'entraînement (24 sorties, 5 décrochages, 3 stables), 6 au test (4, 2, 0), 9 dans les passages Covid (9, 0, 0). Contrôle à l'entraînement : `inc_lits_zero_avec_journees` passe de 28 lignes (18 sorties, 89 % de y = 1) à 6 (1 sortie, 67 %), et l'AUC de l'activité seule pour les sorties de 0,837 à 0,812 : des cas triviaux ont été retirés, et l'indicateur n'annonce pas l'inverse d'une sortie (pas de trace de biais). Les métriques des sorties seront aussi données avec ces lignes. Variante : `perimetre.capacite_mco_requise: false`.

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

**Mouvements de structure : ce que la SAE permet de voir** *(validé le 20/11/2026)*
Définitions retenues selon l'observation de terrain et le guide de remplissage (SAE_AR_2024) ; chiffres vérifiés sur la table ID et le panel MCO (questions 7 à 9 de la pré-analyse, et vérifications du 20/11/2026). Le FINESS d'un site porte son département dans ses premiers chiffres (vrai pour 96,8 % des lignes du panel ; les écarts sont des codes d'outre-mer).

| Événement | Ce que c'est | Ce qui change dans les FINESS | Ce que montre la table ID | Dans le projet |
|---|---|---|---|---|
| Création | un établissement nouveau, *ex nihilo* | un nouveau FINESS | `typmd1` | une entrée dans le panel |
| Fusion | deux entités juridiques ou plus n'en forment plus qu'une | les anciennes **entités** disparaissent ; les **sites** gardent le plus souvent leur FINESS et changent d'entité | `typmd2` ; `fifu1-3` : les établissements d'avant (205 des 550 FINESS cités par un autre établissement sont des FINESS d'entité ; 84 % des déclarants sont encore là l'année d'après) | restructuration probable si le site est cité (règle 2) |
| Absorption (une fusion) | une entité en absorbe une autre ; celle qui absorbe garde son FINESS et change de périmètre | l'entité absorbée disparaît | `typmd2` ; `fifu` : l'absorbé et celui qui se maintient | comme la fusion |
| Regroupement | un site rejoint un site ou une entité qui existe déjà | le site regroupé disparaît | pas de colonne dédiée ; `fifu` / `scfu` en citent une partie (le site ou son entité pour 7 des 28 reprises trouvées) | reprise des capacités (règle 3) |
| Scission | une entité se divise | le FINESS d'origine, puis de nouveaux FINESS | `typmd3` ; `scfu1` : l'origine, puis les nouveaux | restructuration probable si le site est cité (règle 2) |
| Cession | un changement de propriétaire | le site garde son FINESS ; l'entité change | pas de colonne « cession » ; le changement de `fi_ej` est toujours visible, `chlej0` et `fipre` une fois sur deux (48,7 % des 261 changements d'entité de sites MCO) ; rien n'est déclaré dans 42 % des cas ; une cession ne se distingue pas d'une fusion | ni sortie ni décrochage : la cible suit le FINESS du site ; `changement_de_groupe` en information |
| Transfert | un déménagement du **même établissement** (définition retenue) : même entité juridique et même SIREN ; le SIRET, rattaché à l'adresse, change normalement ; la raison sociale n'est qu'un indice, elle peut changer avec le lieu | un nouveau FINESS de site | rien de codé (le guide : « en commentaire ») ; testable avec `fi_ej` et les 9 premiers chiffres de `sir` (SIREN ou SIRET selon le groupe d'interrogation) : sur les 28 reprises trouvées, 9 ont la même entité et le même SIREN, toutes déjà retirées par les règles (1) et (2) | reprise des capacités |
| Fermeture | le site arrête toute activité | le FINESS disparaît | fermée en cours d'année : activité déclarée, 0 lit au 31 décembre | sortie, y = 1 |
| Arrêt du MCO | le site arrête le MCO et garde une autre activité (SMR, USLD, HAD) | le FINESS reste | présent dans la SAE, sans MCO | sortie, y = 1 (l'activité MCO est perdue) |
| Autre modification | ni création, ni fusion, ni scission | variable | `modej` = 1 sans type coché (3 des 261 changements d'entité) | information |

Seules une baisse réelle de l'activité MCO, une fermeture et un arrêt du MCO comptent comme y = 1. Une fusion, une absorption, un regroupement, une scission, une cession ou un transfert déplacent l'activité sans la faire disparaître.

**Reprise des capacités par un autre site** *(validé le 19/11/2026)*
Un décrochage ou une sortie est aussi une restructuration probable si (3) ses lits et places MCO sont repris en t+1 par un autre site du même département : le site perd au moins 30 lits et places et **toutes ses capacités** (absent en t+1, ou 0 lit et 0 place : il ferme ; un site qui garde des lits décroche) ; un autre site gagne la même capacité (à 2 près ou à 10 % près) ; au plus 6 sites sont dans ce cas en France ; et le repreneur gagne au moins la moitié de l'activité perdue (`config.yaml` › `cible.reprise`, `src/cible.py` › `reprises_de_capacites`). La colonne `reprise_meme_ej` dit si le repreneur est dans la même entité juridique ; elle est une information, pas une variable explicative (elle vient de t+1, comme `reprise_capacites`).
Vocabulaire : voir le tableau des mouvements de structure ci-dessus. Le guide de remplissage (SAE_AR_2024) précise que le transfert d'activité entre établissements d'une même entité n'est pas codé (seulement en commentaire), et qu'un établissement fermé en cours d'année déclare l'activité faite avant la fermeture, ses capacités étant celles du 31 décembre (d'où des journées avec 0 lit).
Pré-analyse (`scripts/04_preanalyse.py`, question 7, cible d'avant cette règle ; perte d'au moins 30 % des capacités, puis vérification que le site disparaît) :
- les mouvements déclarés dans la table ID (`chlej0`, `fipre`, `modej`, `typmd1-3`, `fifu1-3`, `scfu1-3`) ne suffisent pas comme preuve (`mouvements_declares.csv`) : à l'entraînement, au moins un mouvement déclaré pour 6,7 % des lignes stables, 8,9 % des décrochages gardés et 17,0 % des sorties gardées ; `fiaut1-7` et `rsaut1-7` décrivent les autres structures installées dans l'établissement (imagerie, laboratoire), pas une restructuration ;
- chercher la même capacité « partout », sans condition, ne prouve rien : 80 à 96 % des fortes pertes trouvent une correspondance, chez les stables comme dans le placebo (gains de t−1 à t, qui ne peuvent pas venir de la perte) ;
- la règle stricte sépare (`reprise_capacites.csv`, seuil 30, entraînement) : reprise pour 1 stable sur 34 (2,9 %), 4 décrochages gardés sur 42 (9,5 %), 6 sorties gardées sur 23 (26,1 %), placebo à 0 % pour ces trois groupes ; elle retrouve aussi 14 cas déjà repérés par les règles (1) et (2) ;
- seuil de 20 lits et places : les mêmes 14 nouveaux cas, stables à 1,9 % et placebo à 0 % ; le seuil de 30 est retenu ;
- 28 passages y = 1 avec une reprise, dont 14 nouveaux (`reprises_trouvees.csv`) : aucun des 14 n'a son repreneur dans la même entité juridique (9 sur 14 parmi les cas déjà repérés). Avec la définition retenue (un transfert garde l'entité juridique et le SIREN), aucun n'est donc un transfert ; c'est une conséquence de la définition, pas un constat indépendant : 10 sont le même établissement repris par un autre exploitant (souvent un GCS du même nom, ou « Nouvelle clinique… », parfois déclaré en `fipre`), 4 une activité absorbée par un hôpital d'une autre entité.
- l'ancien site a-t-il vraiment disparu ? (colonnes `capacite_t1` et `annees_dans_la_sae_apres_t`) Pour 12 des 14 : oui. Les 9 sorties ne sont plus jamais dans la SAE ; 3 décrochages (Clinique des Diaconesses en 2015, Clinique chirurgicale du Libournais en 2018, Clinique du Pays de Seine en 2023) déclarent 0 lit et 0 place en t+1, une activité résiduelle (fermeture en cours d'année), puis disparaissent. Les 2 autres gardent des lits et restent dans la SAE jusqu'en 2025 : HIA Desgenettes (2017 : 136 → 79 lits et places, activité qui baisse ensuite chaque année) et Hôpital privé d'Athis-Mons, site Caron (2018 : 64 → 25, activité qui remonte ensuite). Ce ne sont pas des reprises : la règle exige que le site perde toutes ses capacités, et ces 2 cas restent des décrochages (y = 1).
Chiffre retenu : **12 reprises**. Les autres nombres sont des étapes de la pré-analyse : 28 passages y = 1 dont les lits se retrouvent ailleurs (avant d'exiger la fermeture complète), dont 14 que les règles (1) et (2) ne retiraient pas déjà, dont 12 dont le site perd toutes ses capacités ; les 2 autres (HIA Desgenettes, Athis-Mons) gardent des lits et restent des décrochages.
Effet : 12 lignes y = 1 de plus mises à part, 8 à l'entraînement (6 sorties, 2 décrochages), 3 au test, 1 dans les passages Covid. Ces lignes ne sont ni des décrochages ni des stables : elles sont retirées des lignes évaluées (`cible.retirer_restructurations`), le modèle ne les voit pas. Elles ne passent pas à y = 0 : la preuve de la reprise n'existe qu'en t+1, et le modèle apprendrait qu'un site sur le point de fermer est stable. Limites : les seuils ont été choisis en regardant ces données ; les deux sites de Guyane de 2024 passent sous une même nouvelle entité en 2025, à vérifier dans le répertoire FINESS. Variante pour l'analyse de robustesse : cible sans cette règle (`cible.reprise.active: false`).

**Fermeture en cours d'année : une sortie, pas un décrochage** *(validé le 19/11/2026)*
Un décrochage devient une sortie quand le site, encore actif en t+1, déclare 0 lit et 0 place MCO en t+1 alors qu'il en avait en t, et n'a plus aucune activité après t+1 (`config.yaml` › `cible.fermeture_en_cours_est_une_sortie`, `src/cible.py` › `fermetures_en_cours`). Le guide de remplissage (SAE_AR_2024) l'explique : un établissement fermé en cours d'année déclare l'activité faite avant la fermeture, et ses capacités au 31 décembre. y ne change pas (décrochage et sortie valent 1), donc la table de modélisation non plus ; seule l'étiquette change, ce qui compte pour évaluer à part les décrochages et les sorties. La colonne `fermeture_en_cours` est une information de t+1, interdite comme variable.
Pré-analyse (`scripts/04_preanalyse.py`, question 8, cible d'avant cette règle ; `fermeture_en_cours_bilan.csv`, `fermeture_en_cours_par_partie.csv`, `fermeture_en_cours_cas.csv`) : 104 passages actifs en t+1 avec 0 lit et 0 place en t+1 (capacité positive en t). 87 ne sont plus jamais actifs après t+1, 11 le sont à nouveau plus tard, 6 ont une suite inconnue (t+1 = 2025). Parmi les 62 décrochages gardés : 48 fermetures définitives, 10 actifs à nouveau plus tard (dont 4 après un trou d'au moins un an), 4 de suite inconnue ; leur activité de t+1 vaut, en médiane, 38 % de celle de t (la part de l'année faite avant de fermer).
Choix : (a) les 4 décrochages de 2024 → 2025 dont la suite est inconnue restent des décrochages : on n'affirme que ce qu'on observe, comme pour les sorties qui réapparaissent. Les 7 stables (y = 0) concernés ne changent pas : leur activité de t+1 reste normale (93 % de celle de t en médiane) ; le site ferme en fin d'année, et c'est son passage suivant qui est une sortie.
Effet sur les lignes évaluées : entraînement 547 décrochages et 89 sorties (au lieu de 583 et 53), test 128 et 21 (au lieu de 133 et 16), passages Covid 234 et 28 (au lieu de 241 et 21). Variante pour l'analyse de robustesse : `cible.fermeture_en_cours_est_une_sortie: false`. Le passage qui suit une fermeture en cours d'année est retiré par la règle de champ (section Périmètre).

**Classes de y = 1, pour le rapport seulement : décrochage, fermeture, arrêt du MCO** *(validé le 20/11/2026)*
Le modèle se construit sur les sites qui ont du MCO en t, et y mesure leur activité MCO en t+1 : qu'un site ferme ou garde une autre activité, son activité MCO tombe à 0 et y = 1. La distinction sert seulement à décrire les résultats. Décrochage : le site garde du MCO en t+1. Fermeture : le site disparaît de toute la SAE. Arrêt du MCO : le site reste dans la SAE avec une autre activité (SMR, USLD, HAD), le plus souvent une reconversion du MCO vers le SMR (sur 36 arrêts qui avaient des lits MCO, 20 gagnent sur le même site au moins la moitié de ces lits en SMR ; aucun ne ressemble à une reprise, même en cherchant sans minimum de lits). Pré-analyse (question 9, `classes_y1_rapport.csv`, lignes dans le champ) : à l'entraînement, 542 décrochages, 41 fermetures, 23 arrêts du MCO avec une activité SMR ensuite et 1 site encore dans la SAE sans SMR (« fermeture ou arrêt du MCO ») ; au test, 126, 10, 3 et 4. Les résultats seront donnés par classe : le modèle peut repérer plus facilement les reconversions, grâce à `a_smr` (du SMR déjà présent en t). Les 3 passages 2024 → 2025 dont le site est encore dans la table ID en 2025 sans aucune activité (la suite ne peut pas être confirmée) : métriques du test avec et sans eux.

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
*Mise à jour du 20/11/2026, après la reprise des capacités (section Cible) et la règle de champ (section Périmètre)* : entraînement 11 587 lignes, 607 y = 1 (5,24 % ; « toujours 0 » : 94,76 % d'exactitude ; 542 décrochages, 65 sorties) ; test 2 796 lignes, 143 y = 1 (5,11 %) ; passages Covid 2 827 lignes, 253 y = 1 (`resultats/03_exploration/tableaux/table_modelisation_controles.csv`). Les chiffres de cette section et les tableaux de la question 6 gardent la cible telle qu'elle était à ces décisions ; le partage reste à 80 / 20 environ.

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

## Variables

Vocabulaire. Une **variable explicative** est une colonne connue en t que le modèle peut utiliser. L'**AUC d'une variable seule** est la probabilité qu'un passage y = 1 tiré au hasard ait une valeur plus extrême qu'un passage y = 0 tiré au hasard (0,5 : le hasard ; 1 : séparation parfaite). Exploration : `scripts/07_exploration.py`, sur l'entraînement seulement (11 587 lignes : 10 980 stables, 542 décrochages, 65 sorties) ; tableaux dans `resultats/03_exploration/`. Fonctions : `src/variables.py`.

**53 variables connues en t, jamais d'information de t+1** *(validé le 19/11/2026)*
Les 29 quantités MCO (lits, journées exploitables, journées, séjours de complète, séjours de 0 jour, places, venues, pour la médecine, la chirurgie, l'obstétrique et le total, plus les séances) ; l'activité et son logarithme ; 6 ratios (taux d'occupation, part de la partielle, durée moyenne de séjour, part des journées de médecine, de chirurgie et d'obstétrique) ; le nombre de sites actifs de l'entité juridique en t et la part du site dans son activité ; 3 variables catégorielles (`stjr`, `catr`, `reg_actuelle`), gardées en texte et encodées dans chaque modèle ; 5 indicateurs d'offre (`a_*`) et 6 indicateurs d'incohérence (`inc_*`). Un ratio dont le dénominateur est nul ou vide reste vide (aucune valeur inventée). Les identifiants et tout ce qui vient de t+1 ou sert à construire la cible sont refusés (`VARIABLES_INTERDITES` ; le script 05 s'arrête si l'un d'eux est parmi les variables). La table garde aussi la classe (stable, décrochage, sortie), pour l'évaluation seulement.

**Taux d'occupation impossible : un indicateur, pas une correction** *(validé le 19/11/2026)*
`inc_occupation_superieure_a_1_5` vaut 1 quand le taux d'occupation (journées / journées exploitables) dépasse 1,5 : 33 lignes à l'entraînement (26 stables, 5 décrochages, 2 sorties), 21,2 % de y = 1 contre 5,2 % sans (`taux_occupation.csv`, `indicateurs_par_classe.csv`). Médiane du taux : 0,759 ; 99e centile : 1,114 ; maximum : 54,5. Des journées exploitables trop basses (moins de 0,5 × lits × 365) n'expliquent que 9 des 33 cas ; les autres viennent de très petits nombres de lits (1 à 5 lits pour 1 000 à 4 400 journées) ou de journées trop nombreuses pour des lits cohérents. L'indicateur porte donc sur le taux, quelle que soit la cause. Aucune valeur n'est corrigée.

**Modalités rares regroupées** *(validé le 19/11/2026)*
Une modalité de moins de 100 lignes à l'entraînement recevrait un coefficient appris sur presque rien (PNL3 : 8 lignes, 25 % de y = 1). Chaque catégorie rare de `catr` n'a qu'un statut juridique : elles sont regroupées par statut (`REGROUPEMENT_CATR`) en PUB_autres (PUB3, PUB10 : 188 lignes, 12,2 % de y = 1), PLU_autres (PLU5, PLU7, PLU8, PLU10 : 107 lignes, 9,3 %) et PNL_autres (PNL3, PNL7, PNL8 : 100 lignes, 5,0 %). Les régions d'outre-mer (01, 02, 03, 04, 06) forment une modalité `outre_mer` (310 lignes, 7,1 %) ; la Corse (94, 103 lignes) reste seule. Les listes sont fixées une fois, d'après l'entraînement, et appliquées à toutes les parties (`modalites_categorielles.csv` montre chaque modalité déclarée et son regroupement).

**Redondances : un diagnostic, pas une sélection forcée** *(validé le 19/11/2026)*
Trois corrélations sur chaque paire de variables numériques (`correlations_paires.csv`) : Pearson (lien linéaire, sensible aux valeurs extrêmes), Spearman (corrélation des rangs) et Kendall (part des paires d'établissements rangées dans le même ordre par les deux variables, moins la part rangée en sens inverse ; robuste aux ex-aequo). Kendall vaut à peu près 0,8 × Spearman (médiane 0,800 sur les paires où |Spearman| ≥ 0,3) : un Kendall de 0,75 correspond à peu près à un Spearman de 0,9. Paires ≥ 0,9 : 49 (Pearson), 48 (Spearman), 15 (Kendall). Les trois mesures retrouvent les mêmes familles : la taille (activité, journées, lits, journées exploitables, séjours), les lits et les journées exploitables (Kendall 0,97 à 0,99), et des variables qui se complètent (nombre de sites et part du site : Kendall −0,91 ; parts de journées de médecine et de chirurgie : −0,85). Aucune variable n'est retirée à la main : les modèles linéaires sont pénalisés (Ridge, Lasso, ElasticNet), les arbres supportent la redondance.

**Modèles linéaires seulement : logarithme des quantités et plafond du taux d'occupation** *(validé le 19/11/2026)*
L'écart entre Pearson et Spearman montre des valeurs extrêmes : `sej0_chi` et `jou_chi` ont un Pearson de 0,21 mais un Spearman de 0,80 ; l'activité et son logarithme, rangés exactement dans le même ordre, ont un Pearson de 0,80. Pour les modèles linéaires, les quantités passent par log(1 + x) dans le pipeline, et le taux d'occupation est plafonné au 99e centile calculé sur l'entraînement de chaque pli (1,114 sur tout l'entraînement : 115 lignes plafonnées) ; l'indicateur d'occupation impossible garde l'information que le plafond efface. Les modèles à arbres gardent les valeurs brutes.

**La règle naïve à battre : l'activité seule** *(validé le 19/11/2026)*
La meilleure variable seule est l'activité (AUC 0,762) ; les 15 premières sont toutes des mesures de taille (`lien_cible.csv`). Part de y = 1 par quintile d'activité, du plus petit au plus grand : 12,6 %, 8,1 %, 3,9 %, 1,4 %, 0,3 % (figure `y1_par_quintile_activite.png`). Règle naïve : « plus l'établissement est petit, plus il est à risque », c'est-à-dire un score égal à l'opposé de l'activité. Un modèle qui ne la bat pas, pli par pli, n'apporte rien. Kendall et Spearman avec y rangent les variables comme l'AUC : pour une cible 0/1, ils ne disent rien de plus.

**Décrochages et sorties évalués à part** *(validé le 19/11/2026)*
La taille sépare mieux les sorties que les décrochages : AUC de l'activité seule 0,812 pour les sorties contre les stables, 0,756 pour les décrochages contre les stables. Avant la règle de champ, les indicateurs d'incohérence annonçaient surtout des sorties (`inc_lits_zero_avec_journees` : 28 lignes, dont 18 sorties) : c'étaient des fermetures déjà faites en t ; il en reste 6 lignes, dont 1 sortie. Les urgences et la pédiatrie protègent presque totalement d'une sortie (2 sorties sur 5 005 lignes avec urgences, aucune sur 2 492 avec pédiatrie). Un score global peut donc paraître bon en ne trouvant que des sorties : chaque score est aussi donné pour les décrochages seuls et pour les sorties seules.

## Définitions en phrases simples

- **FINESS** : le numéro d'identification de chaque établissement de santé en France (9 caractères). Un **site** (FINESS géographique, `fi`) est un lieu précis où l'on soigne ; une **entité juridique** (FINESS juridique, `fi_ej`) est la structure qui le possède et le gère, et peut avoir plusieurs sites.
- **Groupe** : dans ce projet, l'ensemble des sites qui ont la même entité juridique une année donnée.
- **Sortie** : un établissement présent et actif en t qui n'apparaît plus, ou n'a plus d'activité, l'année suivante.
- **Réapparition** : un établissement absent une année puis de nouveau présent plus tard ; son activité pendant l'absence est inconnue.
- **Fusion** : deux entités juridiques (ou plus) n'en forment plus qu'une ; les sites gardent le plus souvent leur numéro et changent d'entité. Dans une **absorption**, l'entité qui absorbe garde son numéro et l'activité de l'absorbée passe chez elle.
- **Regroupement** : un site rejoint un autre site ou une autre entité ; le site regroupé disparaît et ses lits se retrouvent ailleurs.
- **Cession** : l'établissement change de propriétaire ; il garde son numéro de site, son entité juridique change.
- **Transfert** : le déménagement d'un même établissement (même entité juridique, même SIREN) ; l'activité change de lieu et de numéro de site, le SIRET change normalement avec l'adresse, et le nom peut changer aussi.
- **Arrêt du MCO** : le site arrête la médecine, la chirurgie et l'obstétrique mais garde une autre activité (le plus souvent des soins de suite, SMR).
- **Hors champ** : un passage dont le site ne déclare ni lit ni place MCO en t ; il n'est ni appris ni évalué.
- **Scission** : un établissement est coupé en plusieurs ; une partie de son activité continue sous un autre numéro.
- **Changement de numéro FINESS** : le même lieu de soins est déclaré sous un nouveau numéro (souvent après une fusion ou un changement de gestionnaire).
- **Changement d'entité juridique** : le site change de propriétaire ou de gestionnaire (rachat, reprise) ; il continue de soigner au même endroit.
- **Transfert d'activité** : un service ferme sur un site et rouvre sur un autre site du même groupe ; le premier baisse, le second augmente.
- **Compensation** : la part de ce qu'un site a perdu qu'on retrouve en plus dans les autres sites de son groupe, au-delà de leur croissance normale.
- **Restructuration probable** : une baisse ou une disparition qui s'explique très probablement par un transfert, une fusion ou une scission plutôt que par un vrai déclin.
