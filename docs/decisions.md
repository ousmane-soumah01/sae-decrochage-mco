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
