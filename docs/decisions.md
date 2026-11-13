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
