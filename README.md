# Adaptive Conversation Coach — façade Streamlit publique

Cette façade peut être publiée sur un dépôt GitHub public. Elle contient seulement l’interface Streamlit et son adaptateur de jetons. Le module React/LiveKit et l’agent Python restent dans le dépôt privé et sont hébergés séparément.

**Le site peut être public ; l’usage vocal est réservé au propriétaire connecté.** Un visiteur anonyme ne peut pas obtenir de jeton LiveKit par ce code. ENABLE_VOICE_SERVICES="0" désactive les services par défaut. Aucun appel vocal réel ni déploiement n’a encore été validé.

## Pourquoi une façade publique ?

La [documentation Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app) indique une seule application privée, et une création initialement privée depuis un dépôt privé. Si cet emplacement est déjà utilisé, utiliser ce dépôt public évite d’avoir à modifier l’application privée existante. Cette procédure ne change aucun réglage d’une autre application.

Les permissions GitHub du dépôt et l’autorisation d’utiliser le moteur vocal sont différentes : le code de cette façade est public, mais les clés et l’identité autorisée sont uniquement dans les Secrets Streamlit.

## Contenu autorisé : huit fichiers

- streamlit_app.py et streamlit_support.py ;
- requirements.txt ;
- .streamlit/config.toml et .streamlit/secrets.toml.example ;
- README.md et .gitignore ;
- tests/test_preview_no_api.py : test de non-chargement, sans API.

Aucun code du worker, composant React, historique Git privé, statistique personnelle, enregistrement, clé ou rapport n’est inclus. La signature d’un JWT est une opération cryptographique locale, sans appel IA ; le secret de signature reste côté serveur.

Ne pas ajouter d’autres fichiers. Le .gitignore refuse tout sauf cette liste. Ne jamais utiliser git add -f pour y ajouter des secrets.

## Préparer le dépôt GitHub public

Le dossier exporté possède un historique Git neuf, sans lien avec l’historique privé. Depuis ce dossier uniquement :

```powershell
git status --short
git diff --cached --stat
git commit -m "Prepare minimal public Streamlit facade"
```

Créer manuellement un dépôt GitHub public vide nommé, par exemple, adaptive-conversation-coach-streamlit. Puis, seulement après revue :

```powershell
git remote add origin https://github.com/VOTRE_COMPTE/adaptive-conversation-coach-streamlit.git
git push -u origin main
```

Ne pas rendre public le dépôt complet du coach et ne modifier aucun dépôt d’une autre application. Ces commandes n’ont pas été exécutées sur GitHub.

## Hébergements et URL à configurer

| Service | URL / configuration |
|---|---|
| Cette façade Streamlit | https://VOTRE-COACH.streamlit.app |
| Module web privé existant, service Next.js HTTPS | VOICE_WEB_URL = "https://VOTRE-MODULE/streamlit" dans les Secrets Streamlit |
| Origines acceptées par le module web | STREAMLIT_ALLOWED_ORIGINS=https://VOTRE-COACH.streamlit.app sur son hébergeur |
| Agent Python existant | Processus LiveKit permanent, sur PC ou hébergeur séparé |
| Projet LiveKit | LIVEKIT_URL=wss://VOTRE-PROJET.livekit.cloud, même projet pour Streamlit et agent |

Le code source du module peut rester privé, mais son URL HTTPS doit être joignable par le navigateur du PC et du smartphone. Il reçoit seulement des jetons temporaires. Ne pas lui donner les clés LiveKit pour le mode Streamlit.

Ne pas lancer Next.js en mode dev sur Internet : l’ancien endpoint local /api/token doit rester refusé en production. Il n’est pas utilisé par cette façade. Ne pas démarrer l’agent comme sous-processus de Streamlit Cloud.

## Connexion propriétaire : OIDC + adresse vérifiée

La connexion utilise les [fonctions officielles Streamlit](https://docs.streamlit.io/develop/api-reference/user/st.login). Authentification, state, nonce et cookie d’identité sont gérés par Streamlit/Authlib.

Avant tout usage vocal :
1. Configurer une application OIDC Web chez un fournisseur compatible, par exemple Google. Aucun compte, API ou abonnement n’a été activé par cette préparation.
2. Enregistrer l’URI exacte https://VOTRE-COACH.streamlit.app/oauth2callback chez ce fournisseur.
3. Renseigner les secrets ci-dessous, en dehors de Git. Générer cookie_secret aléatoirement, par exemple avec python -c "import secrets; print(secrets.token_urlsafe(48))".
4. Mettre uniquement l’adresse propriétaire dans ALLOWED_EMAILS. Le fournisseur doit retourner email_verified=true, sous forme de booléen ; un email non vérifié ou un autre compte est refusé.
5. Ne pas activer expose_tokens : les jetons OIDC n’ont pas à être exposés à l’application.

Un champ de formulaire, un paramètre d’URL ou un message du composant ne peut pas définir l’identité serveur. Même si le drapeau vocal est à 1, le serveur bloque les visiteurs non autorisés avant de rendre le composant vocal. Le signataire applique aussi son propre refus par défaut.

## Secrets Community Cloud

Copier la structure de .streamlit/secrets.toml.example dans les Secrets du **nouveau coach uniquement**, puis remplir les valeurs. Ne pas modifier les Secrets d’une application existante.

```toml
VOICE_WEB_URL = "https://VOTRE-MODULE/streamlit"
ENABLE_VOICE_SERVICES = "0"
LIVEKIT_URL = "wss://VOTRE-PROJET.livekit.cloud"
LIVEKIT_API_KEY = ""
LIVEKIT_API_SECRET = ""
ALLOWED_EMAILS = "owner@example.invalid"

[auth]
redirect_uri = "https://VOTRE-COACH.streamlit.app/oauth2callback"
cookie_secret = ""
client_id = ""
client_secret = ""
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Les champs vides doivent être remplis uniquement dans le gestionnaire de secrets. Ne pas mettre votre vraie adresse dans ce README ou le fichier exemple public. Le drapeau ne constitue pas un plafond de dépenses.

## Déploiement Community Cloud : procédure manuelle, non exécutée

1. Publier uniquement les huit fichiers de ce dépôt public.
2. Dans Community Cloud, créer une nouvelle app depuis ce dépôt, branche main, entrée streamlit_app.py, Python 3.13. L’app sera publique par défaut ; ne changer la visibilité d’aucune autre application.
3. Ajouter les Secrets ci-dessus et laisser ENABLE_VOICE_SERVICES="0" pour la première vérification.
4. Préparer séparément les hébergements du module et du worker, leurs secrets et origines. L’agent reste désactivé tant que les coûts ne sont pas autorisés.
5. Ouvrir l’URL Streamlit directement dans un onglet du PC et du smartphone. La connexion OIDC ne doit pas être effectuée en embarquant toute l’app Streamlit dans une autre iframe.
6. Vérifier anonymement : pas de jeton accessible ni de bouton vocal actif. Puis se connecter avec le seul compte autorisé.
7. Vérifier le refus d’un autre compte connecté. Garder le drapeau à 0 tant que ces contrôles ne sont pas réussis.
8. Après accord explicite sur les quotas/coûts, activer les drapeaux côté Streamlit et agent et effectuer le premier essai audio.

## Microphone, HTTPS et limites

- Utiliser HTTPS pour Streamlit et le module, WSS pour LiveKit ; jamais localhost dans la configuration cloud.
- Autoriser microphone et lecture audio sur l’origine du module. Les en-têtes du module doivent permettre l’iframe depuis Streamlit (CSP frame-ancestors et Permissions-Policy appropriées).
- Sur smartphone, utiliser un navigateur récent, rester sur l’onglet au premier plan et appuyer sur Démarrer/Activer le son. Les autorisations dépendent du navigateur ; PC et smartphone restent à tester avec de l’audio réel.
- La voix circule en WebRTC entre navigateur et LiveKit, sans enregistrements successifs. Le worker conserve record=False.
- Un jeton LiveKit est une capacité temporaire de cinq minutes : ne pas le partager. La déconnexion ne révoque pas instantanément une copie déjà volée. Après incident, désactiver les services et révoquer les clés selon les procédures des fournisseurs.
- La configuration OIDC réelle, les cookies/redirections, les en-têtes HTTPS et les permissions micro doivent être vérifiés sur les hébergements finaux avant activation. Les tests locaux ne prouvent pas ces réglages distants.
- Aucun coût n’a été engagé pendant la préparation. Les usages LiveKit/modèle peuvent être facturables au-delà des crédits disponibles.

## Démarrage local sans service vocal

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:ENABLE_VOICE_SERVICES = "0"
.\.venv\Scripts\python.exe -m streamlit run .\streamlit_app.py
```

Avec ENABLE_VOICE_SERVICES="0", seul un message de disponibilité après configuration est affiché : aucune iframe, URL de module ou connexion vocale n’est chargée. Les fichiers React et Python LiveKit nécessaires restent dans le projet privé ; ils ne sont pas inclus ici.

Test de régression sans API : python -m unittest discover -s tests -p test_preview_no_api.py
