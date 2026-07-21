# Twitter Follow Tracker

Surveille les **nouveaux comptes suivis** par une liste de comptes X (Twitter) cibles, et envoie une alerte Telegram plus un log CSV à chaque nouveau follow détecté. Pensé pour de la veille : dealflow, sourcing, détection de signaux faibles sur qui suit quoi.

Le principe est simple. Chaque jour, le script récupère la liste des abonnements de chaque compte cible, la compare à la photo de la veille, et ne remonte que la différence, c'est-à-dire les nouveaux follows. Chaque nouveau compte est enrichi (nom, bio, followers, localisation, site, badge vérifié, ancienneté) et signalé s'il est aussi suivi par d'autres de tes cibles (les « mutuals »).

Il tourne en autonomie via **GitHub Actions** (cron quotidien), sans serveur à gérer. L'état est persisté en committant les fichiers de données dans le dépôt lui-même.

---

## ⚠️ À lire avant tout : confidentialité

Ce dépôt est un **template public**. Il ne contient volontairement **aucune donnée** : ni la liste des comptes surveillés, ni les follows détectés.

Le workflow persiste son état en committant `data/*.json` et `nouveaux_follows_*.csv` dans le dépôt à chaque exécution. **Sur un dépôt public, ta liste de cibles et tes signaux de veille seraient donc visibles par tout le monde dès le premier passage.** Les noms de fichiers dans `data/` sont directement les handles surveillés.

Attention, un simple « Fork » ne protège pas : le fork d'un dépôt public reste public. La règle est donc : **ta copie doit être privée**, créée par import (voir l'étape 4 du guide ci-dessous). Ne branche jamais le tracker sur un dépôt public.

---

## Ce que tu dois apporter

Trois choses (quatre secrets), injectées via le coffre à secrets du dépôt, jamais en dur dans le code. Le détail pas à pas est dans le guide plus bas.

| Secret | Rôle | Où l'obtenir |
|---|---|---|
| `API_KEY` | Clé RapidAPI pour l'API Twitter241 | [RapidAPI → TwttrAPI](https://rapidapi.com/), onglet abonnement, en-tête `X-RapidAPI-Key` |
| `TELEGRAM_TOKEN` | Token du bot Telegram qui envoie les alertes | [@BotFather](https://t.me/BotFather) puis `/newbot` |
| `TELEGRAM_CHAT_ID` | ID de la conversation, du groupe ou du canal de réception | appel `getUpdates`, voir étape 3 |
| `TARGETS` | Liste des comptes à surveiller | pseudos séparés par des virgules, sans `@`, ex : `compte1,compte2,compte3` |

`API_HOST` est fixé à `twitter241.p.rapidapi.com` dans `config.py`. Si tu passes par un autre fournisseur RapidAPI compatible, change-le là. Les endpoints appelés sont `/following-ids`, `/get-users` et `/user`.

Telegram est optionnel : si `TELEGRAM_TOKEN` est vide, les alertes sont désactivées et seul le CSV est écrit.

---

## Installation pas à pas

Ce guide part de zéro. Aucune compétence en code n'est requise : tout se fait dans l'interface web de GitHub et de Telegram. Compte environ 20 minutes. À la fin, le tracker tournera tout seul chaque jour et t'enverra les nouveaux follows de tes comptes cibles sur Telegram.

### Étape 1 : obtenir une clé API Twitter241 (RapidAPI)

Le tracker lit les abonnements des comptes via l'API Twitter241, hébergée sur RapidAPI.

1. Crée un compte gratuit sur [rapidapi.com](https://rapidapi.com).
2. Cherche [Twtter API](https://rapidapi.com/davethebeast/api/twitter241)
3. Onglet **Pricing** : souscris à un plan. Il existe un palier gratuit pour tester, mais il est limité en nombre d'appels. Selon le nombre de cibles et la taille de leurs abonnements, tu passeras vite sur un plan payant. Surveille ton quota.
4. Une fois abonné, va dans l'onglet **Endpoints**. Dans le panneau de code à droite, repère l'en-tête `X-RapidAPI-Key`. La longue chaîne de caractères après le nom, c'est ta clé. Copie-la et garde-la de côté.

Cette clé donne accès à un service payant à ton nom. Ne la partage jamais et ne la colle jamais en clair dans un fichier du dépôt.

### Étape 2 : créer un bot Telegram

Les alertes arrivent via un bot que tu crées en deux minutes. Cette étape est optionnelle : si tu la sautes, le tracker écrira quand même les résultats dans des fichiers CSV, il n'enverra juste pas de notification.

1. Dans Telegram, ouvre une conversation avec [@BotFather](https://t.me/BotFather).
2. Envoie la commande `/newbot`.
3. Suis les instructions : donne un nom au bot, puis un identifiant se terminant par `bot`.
4. BotFather te renvoie un message avec un **token** (une chaîne du type `123456789:AAE...`). Copie-le et garde-le de côté. C'est le `TELEGRAM_TOKEN`.

### Étape 3 : récupérer ton identifiant de discussion Telegram

Le bot doit savoir à qui envoyer les alertes. Cet identifiant, c'est le `TELEGRAM_CHAT_ID`.

Pour recevoir les alertes en message privé :

1. Ouvre une conversation avec ton nouveau bot et envoie-lui n'importe quel message (par exemple « salut »).
2. Dans ton navigateur, ouvre l'adresse suivante en remplaçant `TON_TOKEN` par le token de l'étape 2 :
   ```
   https://api.telegram.org/botTON_TOKEN/getUpdates
   ```
3. Dans la page qui s'affiche, cherche le champ `"chat":{"id":...}`. Le nombre qui suit `"id":` est ton chat ID. Copie-le.

Pour recevoir les alertes dans un groupe ou un canal : ajoute d'abord le bot au groupe (ou comme administrateur du canal), poste un message, puis fais le même appel `getUpdates`. Pour un canal, l'identifiant commence généralement par `-100`.

### Étape 4 : créer ta copie privée du dépôt

C'est l'étape clé pour la confidentialité. Un « Fork » classique sur GitHub reste public, ce qui exposerait tes données. On crée donc une copie privée par import.

1. Va sur [github.com/new/import](https://github.com/new/import).
2. Dans « Your old repository's clone URL », colle l'adresse du dépôt template :
   ```
   https://github.com/pabcrypto99-debug/twitterfollowtracker
   ```
3. Donne un nom à ton nouveau dépôt.
4. Choisis **Private**.
5. Clique sur « Begin import ». Au bout de quelques secondes, tu as ta copie privée, identique au template.

Alternative en un clic, si ce dépôt est marqué comme « Template repository » par son auteur : utilise le bouton vert **Use this template** sur la page du dépôt, puis « Create a new repository » en choisissant **Private**.

### Étape 5 : enregistrer tes secrets

Tes clés ne se mettent jamais dans le code. Elles vivent dans le coffre à secrets de ton dépôt, où GitHub les chiffre.

Dans ton dépôt privé, va dans `Settings → Secrets and variables → Actions`, puis clique sur « New repository secret » pour créer chacun des quatre secrets suivants. Le nom doit être écrit exactement comme indiqué, en majuscules.

| Nom du secret | Valeur à coller |
|---|---|
| `API_KEY` | ta clé RapidAPI de l'étape 1 |
| `TELEGRAM_TOKEN` | le token du bot de l'étape 2 (laisse vide si tu ne veux pas d'alertes) |
| `TELEGRAM_CHAT_ID` | ton chat ID de l'étape 3 |
| `TARGETS` | la liste des comptes à surveiller |

Pour `TARGETS` : les pseudos séparés par des virgules, sans le `@` et sans espaces superflus. Exemple :
```
zacxbt,cobie,punk6529
```

### Étape 6 : autoriser le workflow à écrire

Le tracker a besoin d'enregistrer son état dans le dépôt à chaque passage. Il faut lui en donner le droit une fois pour toutes.

Va dans `Settings → Actions → General`, descends jusqu'à « Workflow permissions », coche **Read and write permissions** et enregistre. Sans ça, le tracker tournera mais ne pourra pas sauvegarder sa mémoire, et repartira de zéro à chaque fois.

### Étape 7 : le premier lancement (initialisation)

Ce premier passage ne t'enverra aucune alerte, c'est normal et voulu. Il prend simplement une photo de départ des abonnements de chaque cible, pour avoir une base de comparaison.

1. Va dans l'onglet **Actions** de ton dépôt.
2. Si GitHub demande d'activer les workflows sur un dépôt importé, confirme.
3. Dans la colonne de gauche, clique sur « Twitter Tracker Daily Run ».
4. Clique sur le bouton **Run workflow** à droite, puis confirme.
5. Attends une minute. Un point vert signifie que l'initialisation a réussi. Tu verras apparaître des fichiers dans le dossier `data/`, un par cible.

### Étape 8 : la détection réelle

À partir de maintenant, le tracker tourne automatiquement chaque jour à 05h34 UTC. À chaque passage, il compare la liste du jour à celle de la veille et t'alerte sur Telegram pour chaque nouveau compte suivi par une de tes cibles.

Tu peux aussi relancer un passage à la main quand tu veux, via **Run workflow**, comme à l'étape 7.

Pour changer l'heure du passage automatique, ouvre `.github/workflows/daily_tracker.yml` et modifie la ligne `cron`. Le format est en temps UTC. Par exemple `0 7 * * *` pour 07h00 UTC.

---

## Ajouter ou retirer un compte surveillé

Tu n'as pas besoin de toucher au code. Va dans `Settings → Secrets and variables → Actions`, ouvre le secret `TARGETS`, et modifie la liste séparée par des virgules. Au prochain passage, un compte ajouté sera d'abord initialisé sans alerte (comme à l'étape 7), puis suivi normalement ensuite.

---

## Utilisation en local (optionnel)

Pour tester sur ta machine sans passer par GitHub Actions :

```bash
pip install -r requirements.txt

export API_KEY="ta_cle_rapidapi"
export TELEGRAM_TOKEN="ton_token_bot"      # optionnel
export TELEGRAM_CHAT_ID="ton_chat_id"      # optionnel
export TARGETS="compte1,compte2,compte3"

python tracker.py
```

`config.py` lit ces variables d'environnement. Il ne contient aucun secret et peut rester versionné.

---

## En cas de problème

Si le workflow échoue (point rouge dans l'onglet Actions), clique dessus pour lire le journal. Les causes les plus fréquentes :

- **Aucune alerte alors que le workflow réussit** : c'est attendu au premier passage. Si ça persiste, vérifie ton `TELEGRAM_TOKEN` et ton `TELEGRAM_CHAT_ID`, et assure-toi d'avoir bien envoyé un message au bot au moins une fois.
- **Échec à l'étape « Run Tracker »** : ta clé `API_KEY` est probablement invalide, expirée, ou ton quota RapidAPI est dépassé.
- **Échec à l'étape de sauvegarde** : les permissions d'écriture ne sont pas activées, reviens à l'étape 6.
- **Une cible ne remonte rien** : le compte est peut-être privé, suspendu, ou inexistant. Le tracker les ignore silencieusement.

---

## Les scripts

- **`tracker.py`** : le cœur. Récupère les abonnements de chaque cible, calcule le diff, enrichit les nouveaux comptes, écrit le CSV du jour et envoie les alertes Telegram. C'est ce que lance le workflow.
- **`add_account.py`** : ajoute une cible en local de façon interactive. Récupère sa photo de départ (`data/<handle>_ids.json`) et l'ajoute à `config.py`. Outil local uniquement. En production, la liste canonique vit dans le secret `TARGETS`.
- **`count_history.py`** : parcourt tous les `nouveaux_follows_*.csv` et compte le nombre de comptes uniques détectés sur l'historique (dédoublonné).
- **`config.py`** : chargeur de configuration depuis l'environnement. Pas de secret.
- **`.github/workflows/daily_tracker.yml`** : le cron GitHub Actions.

---

## Sorties

- **`data/<handle>_ids.json`** : la photo courante des abonnements de chaque cible (l'état persistant).
- **`nouveaux_follows_AAAA-MM-JJ.csv`** : un fichier par jour où des follows sont détectés. Colonnes : `Cible, Handle, Nom, Bio, Followers, Mutuals, Date, Location, Website, Verified`.

---

## Garde-fous intégrés

Quelques seuils codés en dur dans `tracker.py`, à ajuster selon ton usage :

- **Anti-flood** : si une cible gagne plus de 200 nouveaux follows d'un coup (mass-follow, purge), la mise à jour est silencieuse, sans alerte.
- **Filtre bruit** : les comptes de plus de 15 000 abonnés sont loggés dans le CSV mais **pas** notifiés sur Telegram (logique « too late » pour de la détection early).
- **Plafond gros comptes** : la récupération des abonnements s'arrête à 15 000 IDs par cible.
- **Cadence API** : 0,2 s entre chaque appel, retry sur les `429` Telegram.

---

## Coûts et limites

- L'API Twitter241 est **payante à l'usage** (RapidAPI). Le volume d'appels dépend du nombre de cibles et de la taille de leurs abonnements. Surveille ton quota.
- Comptes privés, supprimés ou suspendus : ignorés silencieusement.
- Aucune garantie de stabilité de l'API tierce : si les schémas de réponse changent, l'extraction (`extract_info_smart`) peut nécessiter un ajustement.

---

## Licence

MIT. Voir [`LICENSE`](LICENSE).
