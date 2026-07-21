# Twitter Follow tracker

Surveille les **nouveaux comptes suivis** par une liste de comptes X (Twitter) cibles, et envoie une alerte Telegram + un log CSV à chaque nouveau follow détecté. Pensé pour de la veille : dealflow, sourcing, détection de signaux faibles sur qui suit quoi.

Le principe est simple. Chaque jour, le script récupère la liste des abonnements de chaque compte cible, la compare à la photo de la veille, et ne remonte que la différence _(les nouveaux follows)_. Chaque nouveau compte est enrichi_ (nom, bio, followers, localisation, site, badge vérifié, ancienneté)_ et signalé s'il est aussi suivi par d'autres de tes cibles _(« mutuals »)_.

Il tourne en autonomie via **GitHub Actions** _(cron quotidien)_, sans serveur à gérer. L'état est persisté en committant les fichiers de données dans le dépôt lui-même.

---

## ⚠️ À lire avant de commencer - Fork ce repo

Ce dépôt est un **template public**. Il ne contient volontairement **aucune donnée** : ni la liste des comptes surveillés, ni les follows détectés.

Le workflow persiste son état en committant `data/*.json` et `nouveaux_follows_*.csv` dans le dépôt à chaque exécution. **Si tu actives le cron sur un dépôt public, tu exposes publiquement ta liste de cibles et tes signaux de veille dès le premier run.** Les noms de fichiers dans `data/` sont directement les handles surveillés.

La seule configuration propre :

- **Dépôt public** = ce template (scripts + doc, `data/` vide). Tu ne branches jamais le cron dessus.
- **Fork de ce repo**, où les commits de données restent confidentiels.

---

## Ce que tu dois apporter

Trois choses, injectées via les **secrets** du dépôt (jamais en dur dans le code) :

| Secret | Rôle | Où l'obtenir |
|---|---|---|
| `API_KEY` | Clé RapidAPI pour l'API Twitter241 | [RapidAPI → Twitter241](https://rapidapi.com/), onglet abonnement, `X-RapidAPI-Key` |
| `TELEGRAM_TOKEN` | Token du bot Telegram qui envoie les alertes | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | ID du canal/groupe/conversation où recevoir les alertes | crée le bot, ajoute-le à ton groupe/canal, envoie un message, puis appelle `https://api.telegram.org/bot<TON_TOKEN>/getUpdates` et lis le champ `chat.id`. Pour un canal, l'ID commence souvent par `-100`.|
| `TARGETS` | Liste des comptes à surveiller, séparés par des virgules |pas de `@`, séparés par des virgules, ex : `TARGETS = compte1,compte2,compte3`.

Notes :

- **`API_HOST`** est fixé à `twitter241.p.rapidapi.com` dans `config.py`. Si tu utilises un autre fournisseur RapidAPI compatible, change-le là. Les endpoints appelés sont `/following-ids`, `/get-users` et `/user`.

Telegram est optionnel : si `TELEGRAM_TOKEN` est vide, les alertes sont désactivées et seul le CSV est écrit.

---

## Mise en route (GitHub Actions, recommandé)

1. Fork ce dépôt en **privé** (ou crée un nouveau repo privé et copie ces fichiers).
2. Ajoute les secrets : `Settings → Secrets and variables → Actions → New repository secret`, pour `API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `TARGETS`.
3. Autorise les Actions à écrire dans le dépôt : `Settings → Actions → General → Workflow permissions → Read and write permissions`.
4. Lance un premier run à la main : onglet `Actions → Twitter Tracker Daily Run → Run workflow`.

**Le premier run n'envoie aucune alerte** : il ne fait qu'initialiser la base (`data/<handle>_ids.json` pour chaque cible). C'est la photo de référence. Les alertes commencent au deuxième run, sur le diff. Le cron est réglé sur `34 5 * * *` (05h34 UTC) ; modifie-le dans `.github/workflows/daily_tracker.yml`.

---

## Utilisation en local

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

## Les scripts

- **`tracker.py`** — le cœur. Récupère les abonnements de chaque cible, calcule le diff, enrichit les nouveaux comptes, écrit le CSV du jour et envoie les alertes Telegram. C'est ce que lance le workflow.
- **`add_account.py`** — ajoute une cible en local de façon interactive : récupère sa photo de départ (`data/<handle>_ids.json`) et l'ajoute à `config.py`. Outil local uniquement ; en production, la liste canonique vit dans le secret `TARGETS`.
- **`count_history.py`** — parcourt tous les `nouveaux_follows_*.csv` et compte le nombre de comptes uniques détectés sur l'historique (dédoublonné).
- **`config.py`** — chargeur de configuration depuis l'environnement. Pas de secret.
- **`.github/workflows/daily_tracker.yml`** — le cron GitHub Actions.

---

## Sorties

- **`data/<handle>_ids.json`** — la photo courante des abonnements de chaque cible (l'état persistant).
- **`nouveaux_follows_AAAA-MM-JJ.csv`** — un fichier par jour où des follows sont détectés. Colonnes : `Cible, Handle, Nom, Bio, Followers, Mutuals, Date, Location, Website, Verified`.

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

MIT. Voir `LICENSE`.
