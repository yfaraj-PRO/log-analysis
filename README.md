# Log Analysis

Projet Python réalisé pour analyser des fichiers de logs SSH et afficher les résultats avec Matplotlib.

## Objectif

Le programme permet de connaître :

- Le nombre de tentatives échouées par pays.
- Le nombre de tentatives réussies par utilisateur.
- Le nombre de tentatives échouées avec un utilisateur invalide.

## Organisation du projet

- `ingestion/read.py` : lecture des fichiers simples et compressés `.gz`.
- `processing/extract_transform.py` : extraction des informations avec les expressions régulières.
- `processing/geolocation.py` : recherche du pays d’une adresse IP.
- `main.py` : lancement des étapes, gestion du cache et comptage.
- `dashboard.py` : affichage des résultats.
- `data/` : dossier contenant les logs à analyser.

## Bibliothèques utilisées

J’utilise `os`, `gzip`, `re` et `logging`, qui sont inclus dans Python.

Les bibliothèques externes utilisées sont :

- `requests` pour la géolocalisation des IP.
- `matplotlib` pour les graphiques.

`psycopg2-binary` est aussi déclaré dans la configuration, mais il n’est pas utilisé dans cette version.

## Installation et lancement

Le projet utilise Python 3.13 et un environnement géré avec `uv`.

Depuis le dossier du projet, installer les dépendances :

```powershell
uv sync
```

Créer un dossier `data` et y placer les fichiers fournis :

```text
auth.log.1
auth.log.2
auth.log.3.gz
auth.log.4.gz
```

Puis lancer :

```powershell
uv run python main.py
```

Il faut exécuter cette commande depuis le dossier du projet pour que le chemin `./data` soit trouvé.

## Fonctionnement

Le programme commence par lire les fichiers et rassembler leurs lignes.

Il utilise ensuite des expressions régulières pour récupérer la date, l’heure, le résultat, la méthode d’authentification, l’utilisateur et l’adresse IP.

Les messages `Failed password`, `Accepted password` et `Failed none` sont reconnus. Les autres messages, comme `Connection closed`, ne sont pas comptés comme de nouvelles tentatives.

Certaines lignes contiennent `message repeated ... times`. Le programme utilise ce nombre pour compter les répétitions au lieu de compter seulement une tentative par ligne.

Pour les échecs, le pays de chaque IP est recherché avec le service IPinfo. Les résultats sont ensuite affichés dans le dashboard.

## Cache des pays

Le fichier `ip_countries.txt` enregistre les IP et leurs pays pour éviter de refaire les mêmes recherches.

Le premier lancement peut être long, car il nécessite des requêtes sur Internet. Les lancements suivants réutilisent les pays enregistrés.

Si une recherche échoue, le pays est indiqué comme `Inconnu`. Cette valeur n’est pas enregistrée dans le fichier pour permettre une nouvelle recherche au prochain lancement.

## Dashboard

Le dashboard affiche les trois indicateurs demandés.

Les pays sont triés par nombre d’échecs décroissant et répartis en plusieurs colonnes. Les graphiques de pays utilisent la même échelle et les nombres exacts sont affichés à côté des barres.

Il est préférable de maximiser la fenêtre pour bien lire les résultats.

## Résultats obtenus

Sur les fichiers fournis :

- 10 967 lignes de tentatives reconnues.
- 16 361 tentatives échouées après prise en compte des répétitions.
- 1 tentative réussie pour `adminesisa`.
- 3 253 échecs avec un utilisateur invalide.

Les échecs avec utilisateur invalide sont déjà inclus dans le total des échecs.

## Gestion des erreurs

Les erreurs et avertissements sont enregistrés dans `app.log`, avec la date, le module et le niveau du message.

Cela concerne notamment la lecture des fichiers, la géolocalisation, le cache et l’affichage du dashboard. Les tentatives non reconnues par l’extraction produisent un avertissement.

## Limites

L’extraction actuelle reconnaît les IPv4 et les méthodes d’authentification `password` et `none`.

La géolocalisation dépend d’un service externe et les pays enregistrés dans le cache ne sont pas actualisés automatiquement.

## Git

Le travail est sauvegardé progressivement par module.

Le dossier `data/`, le fichier `app.log` et le cache `ip_countries.txt` sont exclus du dépôt. Il faut donc ajouter les données après avoir récupéré le projet.