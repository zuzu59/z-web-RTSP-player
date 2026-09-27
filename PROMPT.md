# Mission

Réalise dans ce dépôt une petite application web Python permettant de
visionner en direct, dans un navigateur, le flux d’une caméra RTSP.

Commence par examiner le dépôt et ses consignes. Préserve les changements
existants de l’utilisateur et limite les modifications au périmètre demandé.

# Exigences fonctionnelles

- Au démarrage, affiche une page permettant de saisir l’URL RTSP de la caméra.
- Le format attendu est :
  `rtsp://admin:[PASSWORD]@[IP_CAMERA]:554/user=admin_password=[PASSWORD]_channel=1_stream=0.sdp`
- Affiche le flux vidéo en direct dans le navigateur après validation de l’URL.
- Distingue clairement l’attente, la connexion en cours, le flux actif et les
  erreurs. Indique à l’utilisateur les vérifications utiles si le flux échoue.
- Si aucun flux vidéo ne peut être reçu, ne présente pas la page comme une
  connexion réussie.

# Contraintes d’exécution

- Le serveur Python doit écouter sur `0.0.0.0:8089` par défaut.
- Documente les prérequis et les commandes de lancement et de test.
- Choisis une solution adaptée au dépôt; n’ajoute pas de dépendances Python
  non nécessaires. Si un binaire externe est requis (par exemple FFmpeg),
  vérifie sa disponibilité et explique son rôle.
- N’écris pas l’URL complète ni les identifiants sur disque ou dans les logs.
  Ne les expose pas dans les réponses d’erreur, la console du navigateur ou le
  compte rendu.
- Ne conserve les identifiants que le temps et à l’endroit nécessaires au
  fonctionnement. N’ajoute pas de persistance sans demande explicite.
- Le serveur n’ayant pas nécessairement d’authentification, signale le risque
  d’exposition réseau et ne le présente pas comme prêt à être exposé sur
  Internet.

# Tests et validation navigateur

1. Lance les tests automatisés pertinents et corrige les échecs.
2. Démarre réellement l’application et vérifie qu’elle écoute sur
   `0.0.0.0:8089`.
3. Utilise Chromium headless avec Playwright pour ouvrir l’application et
   parcourir le formulaire.
4. Si une caméra et une URL de test autorisée sont disponibles, teste le flux
   réel et vérifie qu’au moins une image vidéo est reçue et affichée. Ne
   prétends pas que le flux réel fonctionne si cette vérification échoue.
5. Teste aussi le comportement d’une URL invalide et, si possible, d’une
   caméra inaccessible.
6. En cas d’échec lié à l’environnement (réseau, caméra, permissions ou
   dépendance absente), rapporte précisément ce qui a été testé, le résultat
   observé et ce qui reste à vérifier. N’invente pas de succès.

# Captures d’écran et historique

- Enregistre dans `screenshots/` les captures utiles prises pendant les étapes
  significatives de validation, sans écraser les captures antérieures.
- Nomme chaque fichier avec la date au format `yymmdd.hhmmss` suivie d’un
  libellé court, par exemple `260927.121530-flux-actif.png`.
- Garde un historique de progression daté dans `screenshots/README.md` :
  étape, résultat vérifié, capture associée et éventuelle limitation.
- Avant chaque capture, vérifie visuellement qu’aucun mot de passe, URL avec
  identifiants, secret ou donnée sensible n’est visible. Masque ou efface ces
  valeurs avant la capture; ne te fie pas uniquement à l’intention du code.
- Ne copie aucun secret dans le dépôt, les captures, l’historique, les
  rapports, les commits ou les messages finaux. Si une capture risque de
  contenir un secret, ne la conserve pas.

# Critères d’acceptation

- L’application démarre et écoute sur `0.0.0.0:8089`.
- La saisie d’une URL RTSP valide lance le flux; l’état « actif » est affiché
  seulement après réception d’une image.
- Les erreurs de saisie et d’accès caméra sont compréhensibles et ne révèlent
  aucun identifiant.
- Les tests automatisés passent et le parcours Chromium est rapporté.
- Les captures et leur historique sont présents dans `screenshots/` et ne
  contiennent aucun mot de passe.
- Le README explique l’installation, le lancement, les tests et les limites
  de sécurité.

# Compte rendu final

Résume les fichiers modifiés, les commandes exécutées, les tests réussis ou
échoués, le résultat de la vérification réelle du flux, l’emplacement des
captures et les éventuelles limites restantes. Ne divulgue aucune valeur
secrète.
