"""Récupération des données de la SAE.

Récupérer les archives de la DREES et vérifier qu'elles sont exactement celles
du projet (empreinte md5). donnees/sources_donnees_brutes.csv donne, pour chaque
année, le nom de l'archive, son adresse et son md5.
"""

import csv
import hashlib
import urllib.request
from pathlib import Path

# Colonnes attendues dans donnees/sources_donnees_brutes.csv
COLONNES_SOURCES = ["annee", "fichier", "octets", "md5", "derniere_modif_serveur", "url"]

# Nom de client envoyé au serveur de la DREES (certains serveurs refusent un client anonyme)
AGENT = "sae-decrochage-mco (projet universitaire)"


class Md5Incorrect(Exception):
    """L'empreinte md5 d'une archive ne correspond pas à celle attendue."""


def lire_sources(chemin):
    """Lit la liste des archives à récupérer.

    Renvoie une liste de dictionnaires, un par archive :
    {"annee": 2013, "fichier": "...", "octets": 17705899, "md5": "...", "url": "..."}.
    """
    chemin = Path(chemin)
    if not chemin.exists():
        raise FileNotFoundError(f"Liste des sources introuvable : {chemin}")
    with open(chemin, encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f, delimiter=";")
        if lecteur.fieldnames != COLONNES_SOURCES:
            raise ValueError(f"Colonnes inattendues dans {chemin.name} : {lecteur.fieldnames} "
                             f"(attendu : {COLONNES_SOURCES})")
        sources = []
        for ligne in lecteur:
            ligne["annee"] = int(ligne["annee"])
            ligne["octets"] = int(ligne["octets"])
            ligne["md5"] = ligne["md5"].strip().lower()
            sources.append(ligne)
    if not sources:
        raise ValueError(f"{chemin.name} ne contient aucune archive.")
    annees = [s["annee"] for s in sources]
    if len(annees) != len(set(annees)):
        raise ValueError(f"{chemin.name} contient deux fois la même année.")
    return sources


def md5_fichier(chemin, taille_bloc=1024 * 1024):
    """Empreinte md5 d'un fichier, lue par blocs (sans charger tout le fichier en mémoire)."""
    empreinte = hashlib.md5()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(taille_bloc), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def etat_archive(chemin, md5_attendu):
    """État d'une archive sur le disque.

    Renvoie « absente », « ok » (md5 identique) ou « md5_different ».
    """
    chemin = Path(chemin)
    if not chemin.exists():
        return "absente"
    return "ok" if md5_fichier(chemin) == md5_attendu.lower() else "md5_different"


def telecharger_fichier(url, destination, delai=120):
    """Télécharge url dans destination.

    Le fichier est d'abord écrit sous un nom temporaire (.partiel), puis renommé :
    un téléchargement interrompu ne laisse jamais un fichier tronqué à son vrai nom.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partiel = destination.with_name(destination.name + ".partiel")
    requete = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(requete, timeout=delai) as reponse, open(partiel, "wb") as f:
            while bloc := reponse.read(1024 * 1024):
                f.write(bloc)
        partiel.replace(destination)
    finally:
        if partiel.exists():
            partiel.unlink()


def recuperer_archive(source, dossier):
    """Garantit qu'une archive est présente et intacte dans dossier.

    source : un élément renvoyé par lire_sources().
    Renvoie « deja_presente » (rien à faire) ou « telechargee ».
    Lève Md5Incorrect si l'archive téléchargée n'a pas le md5 attendu :
    le fichier fautif est alors supprimé.
    """
    chemin = Path(dossier) / source["fichier"]
    if etat_archive(chemin, source["md5"]) == "ok":
        return "deja_presente"

    telecharger_fichier(source["url"], chemin)
    obtenu = md5_fichier(chemin)
    if obtenu != source["md5"]:
        chemin.unlink()
        raise Md5Incorrect(f"{source['fichier']} : md5 obtenu {obtenu}, attendu {source['md5']}. "
                           f"Téléchargement abîmé ou nouvelle version publiée par la DREES.")
    return "telechargee"
