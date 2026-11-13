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
