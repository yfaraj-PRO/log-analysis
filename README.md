# Pipeline Log Analyser

Projet Python d’analyse de journaux d’authentification SSH.

Le programme lit des fichiers de logs, extrait les informations des tentatives d’authentification, recherche le pays des adresses IP et présente les résultats dans un dashboard Matplotlib.

## 1. Objectifs

Le dashboard présente les trois indicateurs demandés :

- Le nombre de tentatives échouées par pays.
- Le nombre de tentatives réussies par utilisateur.
- Le nombre de tentatives échouées avec un utilisateur invalide (`invalid user`).

Le projet enregistre également les erreurs et avertissements de fonctionnement dans `app.log`. Son développement est sauvegardé progressivement dans Git.

## 2. Organisation du projet

```text
log-analysis/
├── data/
│   ├── auth.log.1
│   ├── auth.log.2
│   ├── auth.log.3.gz
│   └── auth.log.4.gz
├── ingestion/
│   └── read.py
├── processing/
│   ├── extract_transform.py
│   └── geolocation.py
├── dashboard.py
├── main.py
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
└── README.md
```

Deux fichiers sont générés pendant l’utilisation :

- `app.log` : messages de fonctionnement, avertissements et erreurs.
- `ip_countries.txt` : cache associant les adresses IP à leurs pays.

Le dossier `data/`, le journal `app.log` et le cache `ip_countries.txt` sont exclus de Git. Ils ne sont donc pas fournis lors du clonage du dépôt.

## 3. Bibliothèques utilisées

| Bibliothèque | Utilisation |
|---|---|
| `os` | Parcourir le dossier des données et construire les chemins |
| `gzip` | Lire les fichiers compressés `.gz` |
| `re` | Extraire les informations avec des expressions régulières |
| `logging` | Enregistrer les messages et erreurs de l’application |
| `requests` | Interroger le service de géolocalisation |
| `matplotlib` | Construire le dashboard |

`os`, `gzip`, `re` et `logging` font partie de Python et ne nécessitent pas d’installation séparée.

`matplotlib.pyplot`, importé sous le nom `plt`, est un module de Matplotlib. Ce n’est pas une bibliothèque supplémentaire.

La configuration du projet déclare aussi `psycopg2-binary`, mais le code actuel ne l’utilise pas : aucune base PostgreSQL n’est nécessaire pour lancer l’application.

## 4. Installation et lancement

### Prérequis

- Python 3.13 ou une version compatible plus récente, conformément à `pyproject.toml`.
- Le gestionnaire d’environnement `uv` pour utiliser `uv.lock`.
- Une connexion Internet pour rechercher les pays des IP absentes du cache.
- Un environnement graphique permettant d’ouvrir une fenêtre Matplotlib.

### Récupérer le projet

```powershell
git clone https://github.com/yfaraj-PRO/log-analysis.git
cd log-analysis
```

### Installer les dépendances

Depuis le dossier du projet :

```powershell
uv sync
```

### Ajouter les données

Créer le dossier `data` s’il n’existe pas, puis y placer les quatre fichiers fournis pour le projet :

```text
auth.log.1
auth.log.2
auth.log.3.gz
auth.log.4.gz
```

Les fichiers `.gz` peuvent rester compressés : le programme les lit directement.

Le dossier doit contenir les fichiers à analyser, sans sous-dossiers.

### Lancer l’application

```powershell
uv run python main.py
```

Avec l’environnement virtuel déjà installé, il est également possible d’utiliser :

```powershell
.\.venv\Scripts\python.exe main.py
```

Il faut lancer la commande depuis le dossier `log-analysis`, car le programme utilise des chemins relatifs comme `./data`.

Le programme affiche les résultats dans le terminal, puis ouvre le dashboard.

## 5. Fonctionnement du pipeline

```text
Fichiers de logs
      ↓
Lecture des lignes
      ↓
Extraction des tentatives SSH
      ↓
Prise en compte des répétitions
      ↓
Comptage et géolocalisation des IP
      ↓
Affichage du dashboard
```

### Lecture — `ingestion/read.py`

La fonction `ingest(path)` :

1. Liste les fichiers du dossier.
2. Ouvre les fichiers `.gz` avec `gzip.open()`.
3. Ouvre les autres fichiers avec `open()`.
4. Lit leur contenu en UTF-8.
5. Rassemble les lignes dans une liste avec `extend()`.
6. Retourne cette liste après avoir parcouru les fichiers.

Le bloc `with` ferme automatiquement chaque fichier après sa lecture.

Si une erreur survient, elle est enregistrée avec le logger du module. Dans la version actuelle, une erreur interrompt la lecture et la fonction renvoie `None`.

### Extraction — `processing/extract_transform.py`

La fonction `extract(row)` utilise deux expressions régulières.

La première extrait :

- Le mois.
- Le jour.
- L’heure.
- Le message.

La seconde recherche une tentative d’authentification et extrait :

- `status` : `Failed` ou `Accepted`.
- `method` : `password` ou `none`.
- `invalid` : la mention `invalid user ` si elle existe, sinon `None`.
- `user` : le nom d’utilisateur, éventuellement vide.
- `ip` : l’adresse IPv4.

Le champ `count` indique le nombre d’occurrences représentées par la ligne.

Exemple de résultat :

```python
{
    "month": "May",
    "day": "24",
    "time": "00:28:00",
    "message": "Failed password for invalid user test from 45.156.87.204 port 41740 ssh2",
    "status": "Failed",
    "method": "password",
    "invalid": "invalid user ",
    "user": "test",
    "ip": "45.156.87.204",
    "count": 1
}
```

Une ligne sans tentative reconnue renvoie `None`. Les messages tels que `CRON` ou `Connection closed` ne sont pas ajoutés aux compteurs.

Une ligne contenant `Failed ` ou `Accepted ` mais non reconnue produit un avertissement dans `app.log`.

### Gestion des répétitions

Certains logs regroupent plusieurs occurrences :

```text
message repeated 4 times: [ Failed password for root from ... ]
```

Pour cette ligne, `count` vaut `4`. Pour une ligne normale, il vaut `1`.

Les compteurs utilisent donc :

```python
compteur += attempt["count"]
```

Ils ne se contentent pas d’ajouter une unité par ligne.

La ligne de résumé contribue pour le nombre indiqué. Une éventuelle ligne précédente, présente séparément dans le fichier, est comptée séparément.

### Géolocalisation — `processing/geolocation.py`

La fonction `geo_location(ip)` interroge :

```text
https://ipinfo.io/<ip>/json
```

Si la réponse HTTP a le code `200`, elle lit le JSON et retourne la valeur de `country`.

Exemples de codes pays :

- `MA` : Maroc.
- `FR` : France.
- `RU` : Russie.
- `NL` : Pays-Bas.

Si le pays est absent ou si la recherche échoue, la fonction renvoie `"Inconnu"`.

La requête utilise `timeout=10` pour limiter l’attente réseau. Les erreurs de requête et les réponses HTTP non réussies sont enregistrées dans `app.log`.

La géolocalisation indique le pays associé à l’IP par le service. Elle ne prouve pas la localisation physique de la personne qui utilise cette adresse.

### Cache des pays — `ip_countries.txt`

Le cache évite de rechercher plusieurs fois le pays d’une même IP.

Chaque ligne contient :

```text
88.147.152.239,RU
```

Au démarrage, le programme charge ces associations dans le dictionnaire `country_by_ip`.

Pour chaque IP liée à un échec :

- Si elle est déjà connue, son pays est réutilisé.
- Sinon, une recherche est effectuée.
- Un pays trouvé est immédiatement ajouté au fichier.

Le mode `"a"` ajoute les nouvelles lignes sans effacer les anciennes.

La valeur `"Inconnu"` n’est pas sauvegardée sur disque. Elle reste toutefois mémorisée pendant l’exécution pour éviter de répéter immédiatement la même recherche.

Le premier lancement peut prendre plusieurs minutes. Les suivants sont plus rapides lorsque les IP sont déjà enregistrées.

Si le cache est absent, le programme continue normalement. Les lignes mal formées sont ignorées avec un avertissement. Les erreurs de lecture ou d’écriture sont enregistrées sans interrompre volontairement le comptage.

### Coordination et comptages — `main.py`

`main.py` configure les logs et relie les différentes étapes du pipeline.

Il construit trois résultats :

| Variable | Contenu |
|---|---|
| `success_by_user` | Nombre de réussites pour chaque utilisateur |
| `invalid_user_failures` | Total des échecs avec utilisateur invalide |
| `failures_by_country` | Nombre d’échecs pour chaque pays |

Les trois comptages prennent en compte `count`.

Les échecs avec utilisateur invalide sont un sous-ensemble des échecs. Il ne faut donc pas les additionner une seconde fois au total des tentatives.

## 6. Dashboard — `dashboard.py`

Le dashboard affiche :

- Tous les pays, triés par nombre d’échecs décroissant et répartis par groupes de 15.
- Les réussites par utilisateur.
- Le total des échecs avec utilisateur invalide.

Les nombres exacts sont affichés à côté des barres.

Tous les graphiques de pays utilisent la même échelle horizontale. Une petite valeur possède donc une petite barre, même si elle apparaît dans une autre colonne.

La fonction `draw_dashboard()` construit la figure.

La fonction `show_dashboard()` appelle le dessin et enregistre les erreurs éventuelles. Un message dans le terminal indique alors de consulter `app.log`.

Pour une meilleure lecture, maximiser la fenêtre.

## 7. Résultats sur les fichiers fournis

Après prise en compte des répétitions :

| Mesure | Résultat |
|---|---:|
| Lignes de logs lues | 65 565 |
| Lignes de tentatives reconnues | 10 967 |
| Tentatives échouées représentées | 16 361 |
| Tentatives réussies représentées | 1 |
| Total des tentatives représentées | 16 362 |
| Échecs avec utilisateur invalide | 3 253 |

La réussite enregistrée concerne l’utilisateur `adminesisa`.

Le nombre de tentatives est supérieur au nombre de lignes reconnues, car certaines lignes regroupent plusieurs occurrences.

La vérification des totaux est :

```text
16 361 échecs + 1 réussite = 16 362 tentatives
```

Les 3 253 échecs avec utilisateur invalide sont déjà inclus dans les 16 361 échecs.

Ces résultats correspondent uniquement aux fichiers fournis pour ce projet.

## 8. Journalisation

La configuration de `logging` se trouve dans `main.py`.

Le format utilisé est :

```text
date et heure|nom du module|niveau|message
```

Les principaux niveaux utilisés sont :

- `INFO` : information de fonctionnement, comme l’absence initiale du cache.
- `WARNING` : anomalie non bloquante, comme une ligne de cache mal formée ou une tentative non reconnue.
- `ERROR` : erreur de lecture, de requête, de sauvegarde ou d’affichage.

`logging.getLogger(__name__)` identifie le module à l’origine du message. Pour `main.py` exécuté directement, ce nom est `__main__`.

Le journal applicatif `app.log` ne doit pas être confondu avec les données du dossier `data/` :

- `data/` contient les logs SSH analysés.
- `app.log` contient les messages de notre programme Python.

La journalisation couvre les cas traités dans le code ; elle ne garantit pas que toute erreur imprévue sera interceptée.

## 9. Interprétation des messages SSH

### `Accepted password`

L’authentification par mot de passe a réussi.

### `Failed password`

Une tentative d’authentification par mot de passe a échoué.

### `Failed none`

Une tentative utilisant la méthode d’authentification `none` a échoué. Elle est incluse dans les échecs reconnus par ce projet.

### `invalid user`

Le nom présenté n’est pas reconnu comme un utilisateur valide par le serveur. Cette mention ne signifie pas simplement qu’un mot de passe est incorrect.

### `Connection closed`

La connexion réseau a été fermée. Cela ne suffit pas à conclure qu’une tentative de mot de passe a échoué.

Le programme ne compte donc pas ces messages comme de nouveaux échecs. Ils peuvent concerner une tentative déjà enregistrée ou une connexion fermée sans tentative d’authentification.

## 10. Limites actuelles

- L’extraction reconnaît les méthodes `password` et `none`.
- Le motif d’adresse IP reconnaît les IPv4, pas les IPv6, et ne valide pas chaque nombre de l’adresse.
- Les dates des logs ne contiennent pas d’année ni de fuseau horaire explicite.
- Les lignes sont chargées en mémoire ; cette approche convient aux fichiers du projet, mais peut être coûteuse pour de très gros volumes.
- Une erreur de lecture d’un fichier interrompt actuellement l’ingestion.
- Les pays mis en cache ne sont pas actualisés automatiquement.
- Les recherches sans cache dépendent du réseau, de la disponibilité et des limites du service de géolocalisation.
- La disposition du dashboard est adaptée au volume de pays et d’utilisateurs des données fournies.

## 11. Gestion du projet avec Git

Le travail est enregistré progressivement par module : lecture, extraction, géolocalisation, pipeline et dashboard.

Les éléments locaux suivants sont ignorés :

```text
.venv/
__pycache__/
data/
app.log
ip_countries.txt
```

Une personne qui récupère le dépôt doit donc ajouter les fichiers de données. Son premier lancement reconstruira le cache des pays.

## 12. Points essentiels à comprendre pour présenter le projet

- **Pourquoi utiliser `extend()` dans la lecture ?**  
  Pour ajouter les lignes d’un fichier à une liste commune, sans créer une liste de listes.

- **Pourquoi utiliser `append()` dans `main.py` ?**  
  Pour ajouter chaque dictionnaire représentant une ligne de tentative comme un élément de la liste.

- **Quelle différence entre `print()` et `return` ?**  
  `print()` affiche une information ; `return` la transmet au code qui a appelé la fonction.

- **Pourquoi utiliser des dictionnaires ?**  
  Pour associer directement une clé à une valeur : utilisateur et compteur, pays et compteur, ou IP et pays.

- **Pourquoi conserver `count` ?**  
  Parce qu’une ligne de log peut représenter plusieurs occurrences.

- **Pourquoi utiliser un cache ?**  
  Pour éviter des requêtes réseau répétées et accélérer les prochains lancements.

- **Pourquoi ne pas compter toutes les lignes du fichier ?**  
  Parce que les logs contiennent aussi des tâches système, des ouvertures ou fermetures de session et d’autres messages qui ne représentent pas de nouvelles tentatives reconnues.

- **Pourquoi utiliser la même échelle pour tous les pays ?**  
  Pour que la longueur des barres reste comparable entre les colonnes.