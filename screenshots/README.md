# Historique des captures de validation

Les captures ci-dessous documentent l’interface et un cas d’erreur. Elles
ont été inspectées avant conservation : aucun mot de passe ni flux caméra
réel n’y apparaît.

## 2026-09-27

- `260927.084333-initial.png` — page d’accueil au démarrage; champ RTSP vide.
- `260927.084334-url-invalide.png` — URL invalide; message d’erreur affiché.
- Tests automatisés : 5 tests réussis (`python3 -m unittest -v`).
- Vérifications du lanceur : démarrage sur un port personnalisé, endpoint
  `/status` en HTTP 200, syntaxe Bash valide.

## Vérification antérieure du flux réel

Un essai précédent dans Chromium headless a confirmé la réception et
l’affichage du flux d’une caméra autorisée (image 2288 × 1288). Le contenu
vidéo n’a pas été ajouté au dépôt afin de ne pas publier des images privées.
Les anciennes captures temporaires n’ont pas été copiées dans ce dossier;
seules les images vérifiées ci-dessus sont conservées ici.
