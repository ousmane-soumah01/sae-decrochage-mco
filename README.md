# SAE – Décrochage d'activité MCO

**Peut-on prévoir, un an à l'avance, qu'un établissement de santé va nettement perdre de l'activité en médecine, chirurgie et obstétrique (MCO) ?**

Projet de machine learning (M2, UE « ML & IA fiable ») — Ousmane SOUMAH et Adrien LAUZE.

## La cible

Pour chaque établissement et chaque année *t*, on regarde s'il **décroche** l'année suivante (*t+1*) :

| Règle | Choix |
|---|---|
| Activité | journées d'hospitalisation complète + 0,5 × (venues de partielle + séjours de 0 jour), en journées-équivalentes |
| Établissements étudiés | au moins 1 000 journées-équivalentes en *t* |
| Référence | évolution de l'activité MCO de toute la France (pondérée par l'activité) |
| Décrochage | évolution de l'établissement inférieure à la référence − 15 points |
| Sortie | établissement absent ou sans activité en *t+1* : compte comme un décrochage |
| Restructuration probable | baisse retrouvée ailleurs dans le groupe, ou fusion / scission déclarée : repérée et mise à part |

Chaque règle est justifiée, chiffres à l'appui, dans [`docs/decisions.md`](docs/decisions.md), qui contient aussi des définitions en phrases simples (FINESS, entité juridique, fusion, scission…). Les valeurs sont dans [`config.yaml`](config.yaml).

## Les données

**Source :** DREES, *Statistique annuelle des établissements de santé* (SAE), **bases statistiques 2013 à 2025**.
**Licence des données :** Licence Ouverte v2.0 (Etalab).

Les données ne sont **pas** dans le dépôt. Leurs adresses de téléchargement et leurs empreintes md5 sont dans [`donnees/sources_donnees_brutes.csv`](donnees/sources_donnees_brutes.csv) ; le premier script les télécharge et les vérifie.

## Installation

```bash
git clone https://github.com/ousmane-soumah01/sae-decrochage-mco.git
cd sae-decrochage-mco
python -m pip install -r requirements.txt
```

Testé avec Python 3.14.

## Reproduire le travail

Toutes les commandes se lancent depuis la racine du dépôt, dans l'ordre :

```bash
python scripts/00_telecharger.py       # télécharge les 13 archives (~290 Mo) et vérifie leur md5
python scripts/01_extraire.py          # extrait les 7 tables utiles, prouve l'encodage de chaque fichier, les lit
python scripts/02_audit_qualite.py     # audit : colonnes, manquants, types, clés, règles de l'activité MCO
python scripts/03_panel.py             # panel : une ligne par établissement et par année
python scripts/04_preanalyse.py        # pré-analyse des règles de la cible
python -m pytest                       # tous les tests (unitaires et intégration)
```

Chaque script dit, en tête de fichier, ce qu'il produit.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `donnees/` | liste des sources ; `brutes/`, `extraites/` et `preparees/` ne sont pas versionnés |
| `src/` | fonctions réutilisables : configuration, chargement, qualité, nettoyage, panel, activité, cible |
| `scripts/` | étapes numérotées, à lancer dans l'ordre |
| `tests/` | tests unitaires (une fonction à la fois) et test d'intégration (de bout en bout) |
| `resultats/` | tableaux et figures produits par les scripts, rangés par étape |
| `docs/` | journal des décisions et journal du nettoyage des données |

## Où en est le projet

| Étape | État |
|---|---|
| Données : téléchargement, extraction, encodages, audit de qualité | fait |
| Panel : nettoyage, identité, région actuelle, indicateurs | fait |
| Règles de la cible, avec leur pré-analyse | fait |
| Table de modélisation, modèles, évaluation | à venir |
| Application et rapport | à venir |

## Licence

Code sous licence [MIT](LICENSE). Données : DREES, Licence Ouverte v2.0 (Etalab).
