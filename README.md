# z-web-RTSP-player

Visionneuse web légère pour afficher en direct le flux d’une caméra RTSP.
Le serveur Python utilise FFmpeg pour convertir la vidéo en MJPEG, un format
qu’un navigateur peut afficher dans une balise image.

## Prérequis

- Linux ou un système compatible avec Bash;
- Python 3.10 ou plus récent;
- FFmpeg installé et accessible dans le `PATH`;
- accès réseau depuis le serveur jusqu’à la caméra RTSP.

Aucune dépendance Python supplémentaire n’est nécessaire. Sur Ubuntu ou
Debian, les outils peuvent être installés avec :

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

## Installer sur un autre serveur

Récupérez le dépôt sur le serveur qui pourra joindre la caméra :

```bash
git clone <URL_DU_DEPOT> z-web-RTSP-player
cd z-web-RTSP-player
```

Le script `start.sh` ne dépend pas du répertoire courant. Il vérifie Python,
sa version, FFmpeg et les fichiers nécessaires, puis démarre l’application
en arrière-plan :

```bash
./start.sh
```

Si le bit d’exécution n’est pas conservé lors du transfert, utilisez :

```bash
bash start.sh
```

Les commandes de gestion utilisent le même script :

```bash
./start.sh status   # vérifier si le serveur tourne
./start.sh stop     # arrêter le serveur
./start.sh restart  # le redémarrer
```

Le PID et le journal sont stockés dans `.runtime/`. Pour suivre les logs :

```bash
tail -f .runtime/server.log
```

## Adresse et port

Par défaut, le serveur écoute sur `0.0.0.0:8089`. Pour modifier l’adresse ou
le port, définissez `HOST` et `PORT` au démarrage :

```bash
HOST=127.0.0.1 PORT=8090 ./start.sh
```

Avec `HOST=0.0.0.0`, ouvrez `http://127.0.0.1:8089` sur le serveur, ou
`http://<IP_DU_SERVEUR>:8089` depuis un appareil autorisé sur le réseau.
Vérifiez que le pare-feu autorise le port choisi et que le serveur peut
atteindre la caméra.

## Utiliser la visionneuse

1. Démarrez le serveur avec `./start.sh`.
2. Ouvrez son adresse dans un navigateur.
3. Saisissez l’URL RTSP de la caméra. Concaténez ces deux parties sans
   espace : `rtsp://admin:[PASSWORD]@[IP_CAMERA]:554/` +
   `user=admin_password=[PASSWORD]_channel=1_stream=0.sdp`.

4. Cliquez sur **Afficher le flux**. L’interface indique l’attente, la
   connexion ou l’état du flux.

Le flux est ouvert par FFmpeg côté serveur, puis transmis au navigateur en
MJPEG. Chaque navigateur qui demande le flux lance son propre processus
FFmpeg. L’URL caméra est conservée en mémoire jusqu’à l’arrêt du serveur.

## Tests

Lancez les tests automatisés avec :

```bash
python3 -m unittest -v
```

Pour valider l’affichage de la vidéo, démarrez l’application et testez-la
depuis un navigateur avec une caméra RTSP accessible. Les tests automatisés
ne contactent pas de caméra réelle.

## Sécurité

Le serveur n’inclut pas d’authentification utilisateur ni de HTTPS. Ne
l’exposez pas directement sur Internet. Sur un réseau partagé, utilisez un
pare-feu et, si un accès distant est nécessaire, placez l’application derrière
un proxy sécurisé avec contrôle d’accès.

Ne partagez pas l’URL RTSP : elle peut contenir les identifiants de la caméra.
Le champ est effacé après acceptation, mais le navigateur et le serveur doivent
recevoir l’URL pour établir le flux. Les captures d’écran prises pendant la
saisie peuvent révéler le mot de passe; vérifiez-les avant de les conserver.
