"""Récupération des données de la SAE.

Partie 1 : récupérer les archives de la DREES et vérifier qu'elles sont exactement
celles du projet (empreinte md5). donnees/sources_donnees_brutes.csv donne, pour
chaque année, le nom de l'archive, son adresse et son md5.

Partie 2 : extraire des archives les seules tables utiles au projet.

Partie 3 : lire une table extraite, sans rien interpréter (après la vérification
de son encodage, src.qualite.encodages_valides).
"""

import csv
import hashlib
import re
import urllib.request
from pathlib import Path, PurePosixPath

import pandas as pd
import py7zr

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


# =============================================================================
# Partie 2 : extraction des tables
# =============================================================================

# La table SSR (soins de suite et de réadaptation) devient SMR à partir de 2025.
ANNEE_SSR_DEVIENT_SMR = 2025

# Dans les archives, chaque table existe sous la forme <TABLE>_<ANNEE><lettre>.csv,
# où la lettre vaut « r » ou « a » selon les tables et les années.
MOTIF_FICHIER = r"{table}_{annee}[a-z]?\.csv"


def tables_attendues(tables, annee):
    """Tables à chercher pour une année : SSR jusqu'en 2024, SMR à partir de 2025.

    tables : liste de config.yaml (donnees.tables), qui contient SSR et SMR.
    """
    if annee < ANNEE_SSR_DEVIENT_SMR:
        return [t for t in tables if t != "SMR"]
    return [t for t in tables if t != "SSR"]


def trouver_csv(noms, table, annee, dossier="Bases CSV"):
    """Chemin, dans une archive, du CSV d'une table pour une année.

    noms : liste des chemins contenus dans l'archive.
    Seuls les fichiers rangés directement dans le dossier `dossier` sont retenus
    (en 2025, le dossier « Bases CSV ancienne casse » est donc écarté).
    Lève ValueError si la table est absente, ou présente plusieurs fois.
    """
    motif = re.compile(MOTIF_FICHIER.format(table=re.escape(table), annee=annee), re.IGNORECASE)
    candidats = [n for n in noms
                 if motif.fullmatch(PurePosixPath(n).name)
                 and PurePosixPath(n).parent.name == dossier]
    if not candidats:
        raise ValueError(f"Table {table} {annee} introuvable dans le dossier « {dossier} » de l'archive.")
    if len(candidats) > 1:
        raise ValueError(f"Table {table} {annee} présente plusieurs fois : {candidats}")
    return candidats[0]


def extraire_tables(archive, annee, tables, destination, dossier="Bases CSV"):
    """Extrait d'une archive les CSV des tables demandées.

    Les fichiers sont écrits dans destination/<annee>/, sous leur nom d'origine
    (par exemple MCOPED_2013a.csv). Renvoie un dictionnaire {table: chemin}.
    """
    destination = Path(destination) / str(annee)
    destination.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(archive) as z:
        noms = z.getnames()
    choisis = {table: trouver_csv(noms, table, annee, dossier) for table in tables}

    # py7zr extrait en recréant l'arborescence de l'archive : on extrait dans un
    # dossier provisoire, puis on déplace chaque fichier à plat dans destination.
    provisoire = destination / "_extraction"
    with py7zr.SevenZipFile(archive) as z:
        z.extract(path=provisoire, targets=list(choisis.values()))
    resultat = {}
    for table, nom in choisis.items():
        final = destination / PurePosixPath(nom).name
        (provisoire / nom).replace(final)
        resultat[table] = final
    _supprimer_dossier(provisoire)
    return resultat


def _supprimer_dossier(dossier):
    """Supprime un dossier (devenu vide de fichiers) et ses sous-dossiers."""
    for chemin in sorted(Path(dossier).rglob("*"), reverse=True):
        chemin.unlink() if chemin.is_file() else chemin.rmdir()
    Path(dossier).rmdir()


# =============================================================================
# Partie 3 : lecture d'une table extraite
# =============================================================================

def octets_invalides(chemin, encodage):
    """Positions des octets d'un fichier qui n'existent pas dans l'encodage donné.

    Renvoie une liste de positions (vide si tout le fichier est lisible).
    Exemple : l'octet 0x90 n'existe pas en Windows-1252.
    """
    contenu = Path(chemin).read_bytes()
    positions = []
    debut = 0
    while True:
        try:
            contenu[debut:].decode(encodage)
            return positions
        except UnicodeDecodeError as erreur:
            positions.append(debut + erreur.start)
            debut = debut + erreur.end


def lire_table(chemin, encodage="cp1252", separateur=";", erreurs="strict"):
    """Lit un CSV de la SAE, sans rien interpréter.

    - Toutes les colonnes sont lues comme du TEXTE : le FINESS « 010000024 »
      garde son zéro de tête, et rien n'est converti en silence.
      La conversion en nombres se fait ensuite, de façon contrôlée.
    - Seule une case vide est considérée comme manquante (« NA » reste du texte).
    - Les noms de colonnes sont mis en minuscules : on écrit toujours « fi »,
      « an », « jou_mco », quelle que soit la casse du fichier d'origine.
    - erreurs : « strict » (par défaut) s'arrête sur un octet illisible ;
      « replace » le remplace par « � ». Dans ce cas, compter d'abord les
      remplacements avec octets_invalides() et les documenter.
    """
    table = pd.read_csv(chemin, sep=separateur, encoding=encodage, dtype=str,
                        keep_default_na=False, na_values=[""], encoding_errors=erreurs)
    table.columns = [c.strip().lower() for c in table.columns]
    doublons = table.columns[table.columns.duplicated()].tolist()
    if doublons:
        raise ValueError(f"{Path(chemin).name} : colonnes en double après mise en minuscules : {doublons}")
    return table


def trouver_table_extraite(dossier_extraites, table, annee):
    """Chemin du CSV extrait d'une table pour une année (lettre finale « r » ou « a »)."""
    dossier = Path(dossier_extraites) / str(annee)
    motif = re.compile(MOTIF_FICHIER.format(table=re.escape(table), annee=annee), re.IGNORECASE)
    candidats = [p for p in dossier.glob("*.csv") if motif.fullmatch(p.name)] if dossier.exists() else []
    if len(candidats) != 1:
        raise FileNotFoundError(f"Table {table} {annee} : {len(candidats)} fichier(s) trouvé(s) "
                                f"dans {dossier} (attendu : 1). Lancer scripts/01_extraire.py ?")
    return candidats[0]
