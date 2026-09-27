# Architecture du projet

## 1. Objectif et périmètre

Ce dépôt contient une petite application web qui reçoit une URL RTSP et
présente le flux vidéo de la caméra dans un navigateur.

Le serveur HTTP est écrit avec la bibliothèque standard de Python. FFmpeg
ouvre le flux RTSP, convertit les images vidéo en JPEG et les transmet au
navigateur sous forme d’un flux MJPEG multipart.

L’application n’enregistre pas les images et ne réalise pas de détection de
personnes. La configuration caméra n’est pas conservée après l’arrêt du
serveur.

## 2. Vue d’ensemble

```text
┌──────────────────────────┐
│ Navigateur               │
│ index.html               │
│ formulaire + <img>       │
└───────────┬──────────────┘
            │ HTTP :8089
            │ POST /connect, GET /stream
            ▼
┌──────────────────────────┐
│ app.py                   │
│ ThreadingHTTPServer      │
│ validation + état mémoire│
└───────────┬──────────────┘
            │ processus enfant par client
            ▼
┌──────────────────────────┐       RTSP/TCP       ┌──────────────┐
│ FFmpeg                   │ ───────────────────▶ │ Caméra RTSP  │
│ H.264 → MJPEG multipart  │                      └──────────────┘
└───────────┬──────────────┘
            │ stdout : octets MJPEG
            └──────────────────────────────▶ navigateur (<img>)
```

Le navigateur ne se connecte pas directement à la caméra. C’est le serveur
Python qui lance FFmpeg et qui relaie sa sortie HTTP. Cette séparation permet
d’utiliser un flux vidéo pris en charge par une balise image HTML, sans
lecteur RTSP natif dans le navigateur.

## 3. Composants

### `app.py` — serveur et relais média

Le module regroupe les responsabilités serveur suivantes :

- lit les paramètres de liaison réseau `HOST` et `PORT`;
- valide l’URL envoyée par le formulaire;
- conserve l’URL caméra en mémoire pendant l’exécution;
- sert la page, le statut de configuration et le flux vidéo;
- démarre et arrête un processus FFmpeg pour chaque client du flux.

Le serveur est créé avec `ThreadingHTTPServer`. Les requêtes HTTP peuvent
ainsi être traitées dans des threads distincts. L’état partagé de la caméra
est protégé par `_camera_lock`.

### `index.html` — interface et comportement navigateur

La page contient le HTML, le CSS et le JavaScript dans un fichier unique.
Elle ne dépend pas d’un framework ou d’un CDN externe.

Le formulaire envoie l’URL à `POST /connect` au format JSON. Une fois la
configuration acceptée, la page efface le champ de saisie, puis affecte
`/stream?ts=<horodatage>` à la source de la balise `<img>`. Le paramètre
changeant à chaque demande évite de réutiliser une réponse en cache.

L’interface présente les états suivants :

- attente de l’URL;
- demande en cours;
- URL acceptée et ouverture du flux;
- flux actif après chargement d’une première image;
- erreur de configuration ou flux indisponible.

Les messages d’état utilisent `role="status"` et `aria-live="polite"` afin
d’être annoncés par les technologies d’assistance.

### `test_app.py` — tests automatisés

Les tests couvrent la validation de l’URL RTSP et quelques routes HTTP :

- acceptation d’une URL RTSP au format attendu;
- rejet d’un schéma incorrect, d’un hôte absent ou d’un port invalide;
- réponse de la page d’accueil et du statut;
- rejet d’une requête de connexion avec une URL invalide.

Le serveur de test écoute sur un port local éphémère. Ces tests ne contactent
pas de caméra et ne vérifient pas le décodage d’un flux vidéo réel.

### Fichiers de documentation et consignes

- `README.md` décrit les prérequis, le démarrage et les tests.
- `PROMPT.md` contient les exigences initiales de réalisation et de
  validation, y compris les règles concernant les captures d’écran et les
  mots de passe.
- `GOGO.md` contient une consigne courte destinée à l’agent de codage; ce
  fichier ne participe pas au fonctionnement du serveur.
- `.gitignore` exclut notamment les caches Python et les environnements
  virtuels.

## 4. Configuration et démarrage

### Prérequis

- Python 3.10 ou version ultérieure;
- FFmpeg accessible dans le `PATH` du processus Python;
- une caméra RTSP joignable depuis la machine qui exécute l’application.

Aucune dépendance Python externe n’est requise pour démarrer le serveur.

### Valeurs par défaut

Le serveur écoute par défaut sur :

```text
HOST=0.0.0.0
PORT=8089
```

`0.0.0.0` signifie que le serveur accepte les connexions sur toutes les
interfaces réseau de la machine. Les variables d’environnement permettent
de remplacer ces valeurs :

```bash
HOST=127.0.0.1 PORT=8090 python3 app.py
```

Démarrage par défaut :

```bash
python3 app.py
```

Puis ouvrir `http://127.0.0.1:8089` sur la machine serveur, ou utiliser son
adresse IP depuis un appareil autorisé sur le réseau local.

## 5. Routes HTTP

| Méthode | Chemin | Rôle | Réponse principale |
| --- | --- | --- | --- |
| `GET` | `/` | Sert `index.html`. | HTML `200` |
| `GET` | `/status` | Indique si une URL a été configurée. | JSON `200` |
| `POST` | `/connect` | Valide et mémorise l’URL. | JSON `200`; erreur `4xx` |
| `GET` | `/stream` | Lance FFmpeg et relaie le flux. | MJPEG multipart |
| toute autre | autre chemin | Signale une route inconnue. | JSON `404` |

`GET /status` indique uniquement si une URL est en mémoire. Il ne vérifie pas
que la caméra répond ni qu’une image est effectivement reçue.

### `POST /connect`

Le corps attendu est un objet JSON semblable à :

```json
{"url":"rtsp://admin:[PASSWORD]@[IP_CAMERA]:554/..."}
```

Le serveur refuse les corps de plus de 8192 octets et vérifie que la valeur
est une chaîne, que le schéma est `rtsp`, qu’un hôte existe et que le port,
s’il est fourni, est valide. L’URL complète est mémorisée dans la variable
module `_camera_url`, protégée par un verrou. Elle n’est pas écrite dans un
fichier.

Une réponse de succès signifie que l’URL a passé cette validation, pas que
la caméra a déjà été contactée. La tentative de connexion RTSP commence
lorsqu’un client demande `/stream`.

### `GET /stream`

Pour chaque requête, le serveur :

1. lit l’URL caméra configurée;
2. lance un nouveau processus FFmpeg;
3. demande à FFmpeg d’utiliser le transport RTSP/TCP et de produire des
   images MJPEG;
4. envoie la sortie standard du processus comme flux multipart HTTP;
5. copie la sortie par morceaux et la vide vers le client;
6. termine FFmpeg lorsque le client se déconnecte ou que la sortie s’arrête.

La réponse utilise `multipart/x-mixed-replace` avec la frontière
`camviewer`. Chaque partie contient une image JPEG. La balise `<img>` du
navigateur peut ainsi actualiser son image au fur et à mesure qu’elle reçoit
les parties suivantes.

Si aucun flux n’a été configuré, `/stream` renvoie `409`. Si FFmpeg est
introuvable, le serveur renvoie `503`. Si FFmpeg démarre mais ne reçoit pas
d’images, la réponse HTTP peut déjà être ouverte; le navigateur signale alors
l’échec du chargement du flux.

## 6. Cycle de vie d’une connexion

```text
Utilisateur        Navigateur          Python             FFmpeg          Caméra
    │                   │                 │                   │               │
    │ saisit URL        │                 │                   │               │
    ├──────────────────▶│                 │                   │               │
    │                   │ POST /connect   │                   │               │
    │                   ├────────────────▶│ valide et mémorise│               │
    │                   │◀────────────────┤ JSON succès/erreur│               │
    │                   │ efface le champ │                   │               │
    │                   │ GET /stream     │                   │               │
    │                   ├────────────────▶│ lance FFmpeg      │               │
    │                   │                 ├──────────────────▶│ RTSP/TCP      │
    │                   │                 │                   ├──────────────▶│
    │                   │                 │                   │ ◀── vidéo ───┤
    │                   │◀────────────────┤◀──── MJPEG ───────┤               │
    │◀── images live ───┤                 │                   │               │
    │                   │                 │                   │               │
    │ ferme la page     ├────────────────▶│ ferme le relais   │               │
    │                   │                 ├──────────────────▶│ termine       │
```

Le JavaScript affiche l’état actif lorsque la balise image déclenche
`onload`. Cela indique qu’une image a pu être chargée, contrairement au
simple succès de `POST /connect`.

## 7. Gestion de l’état et concurrence

L’application conserve une seule URL caméra globale au processus. Si
plusieurs clients configurent une URL, la dernière URL reçue remplace celle
qui était utilisée pour les nouvelles demandes de flux.

Chaque demande `GET /stream` lit l’URL courante au début de la requête et
lance son propre FFmpeg. Un changement d’URL ne modifie pas les processus
FFmpeg qui sont déjà en cours. Plusieurs navigateurs peuvent donc provoquer
plusieurs connexions RTSP simultanées vers la caméra.

Le verrou `_camera_lock` protège la lecture et l’écriture de la variable
partagée. L’état est perdu au redémarrage du serveur.

## 8. Gestion des erreurs et limites actuelles

- La validation vérifie la forme générale de l’URL, mais ne teste pas les
  identifiants ni l’accessibilité réseau de la caméra.
- La connexion RTSP n’est pas testée dans `POST /connect`; l’échec peut se
  produire après l’ouverture HTTP de `/stream`.
- `GET /status` ne fournit pas d’état de santé détaillé du flux.
- L’application ne dispose pas de mécanisme de reconnexion automatique.
- Chaque spectateur consomme un processus FFmpeg et une connexion caméra.
- Le serveur utilise le HTTP simple : aucun TLS ni authentification
  utilisateur n’est configuré.
- La sortie d’erreur de FFmpeg est redirigée vers le périphérique null; les
  détails de diagnostic ne sont donc pas visibles dans l’interface.
- L’application est une visionneuse en direct; elle ne sauvegarde pas de
  vidéo ou d’images et ne détecte pas les personnes.

## 9. Sécurité et confidentialité

Les identifiants RTSP sont des secrets. L’application prend actuellement
plusieurs précautions :

- l’URL caméra est conservée en mémoire seulement;
- le corps de `POST /connect` n’est pas inscrit dans le journal HTTP;
- le champ du navigateur est effacé après acceptation de l’URL;
- les erreurs affichées à l’utilisateur n’incluent pas l’URL complète;
- chaque processus FFmpeg reçoit l’URL comme argument, sans la recopier dans
  les journaux applicatifs. Selon les permissions du système, cette ligne de
  commande peut rester visible dans la liste des processus.

Ces mesures ne rendent pas le serveur adapté à un réseau non fiable. La
requête de connexion et le flux HTTP ne sont pas chiffrés; le serveur n’a pas
d’authentification. Toute personne qui peut joindre son port peut tenter
d’utiliser la visionneuse. Ne pas publier directement le port `8089` sur
Internet. Pour un accès plus large, il faut ajouter un contrôle d’accès et un
transport sécurisé, ou placer l’application derrière un proxy correctement
configuré.

Une capture d’écran prise avant l’effacement du champ ou pendant la saisie
peut révéler le mot de passe. Inspecter chaque capture avant de la conserver
ou de l’ajouter à Git.

## 10. Tests et vérification

Tests automatisés :

```bash
python3 -m unittest -v
```

Vérification de syntaxe facultative :

```bash
python3 -m py_compile app.py test_app.py
```

Les tests automatisés vérifient principalement la validation des URL et les
routes HTTP simples. Ils ne remplacent pas un essai avec une caméra réelle.
Pour valider toute la chaîne, il faut ouvrir l’application dans Chromium,
soumettre une URL autorisée et confirmer qu’une image de la caméra apparaît.
Documenter séparément les cas où la caméra, le réseau ou FFmpeg ne sont pas
disponibles.

## 11. Résumé des échanges

```text
Navigateur ── POST /connect ──▶ Python : validation + mémorisation
Navigateur ── GET /stream ────▶ Python ── RTSP/TCP ──▶ Caméra
Navigateur ◀── MJPEG multipart ─ Python ◀── JPEG ───── FFmpeg
```

Le navigateur ne parle qu’en HTTP au serveur Python. Le serveur Python
orchestre FFmpeg et la connexion RTSP, puis relaie les images au navigateur.
