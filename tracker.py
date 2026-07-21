import requests
import json
import csv
import os
import time
from datetime import datetime, timezone
import config

# --- RÉGLAGES ---
API_DELAY = 0.2  # Pause entre chaque appel API (sécurité)
TIMEOUT_SEC = 20 # Temps avant d'abandonner une requête

def wait_for_api():
    time.sleep(API_DELAY)

# --- 1. GESTION DES FICHIERS ---

def check_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")

def get_clean_filename(target_handle):
    # Nettoie le handle pour le nom de fichier (enlève le @)
    return os.path.join("data", f"{target_handle.replace('@', '').strip()}_ids.json")

def load_previous_follows(target_handle):
    filename = get_clean_filename(target_handle)
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return set(str(x) for x in json.load(f))
        except:
            return set()
    return set()

def save_current_follows(target_handle, id_list):
    if not id_list: return 
    check_data_folder()
    with open(get_clean_filename(target_handle), "w") as f:
        json.dump([str(x) for x in id_list], f)

def get_mutual_follows(new_uid, current_target):
    # Vérifie si vos autres cibles suivent déjà ce nouveau compte
    mutuals = []
    new_uid_str = str(new_uid)
    for raw_target in config.TARGETS:
        target = raw_target.replace("@", "").strip()
        if target == current_target: continue
        other_ids = load_previous_follows(target)
        if new_uid_str in other_ids:
            mutuals.append(target)
    return mutuals

# --- 2. NOTIFICATION TELEGRAM (MODIFIÉ) ---

def send_telegram_alert(target, handle_display, name, bio, followers, mutuals, created_at, location, website, is_verified):
    if not hasattr(config, 'TELEGRAM_TOKEN') or not config.TELEGRAM_TOKEN:
        return
    
    # Nettoyage HTML pour éviter les bugs
    name_clean = str(name).replace("<", "&lt;").replace(">", "&gt;")
    bio_clean = str(bio).replace("<", "&lt;").replace(">", "&gt;")[:800] # Limite taille bio
    
    # Gestion du badge vérifié
    verified_icon = "☑️" if is_verified else ""

    # Création du lien cliquable
    user_line = ""
    if handle_display.startswith("@"):
        pure_handle = handle_display.replace("@", "")
        url = f"https://x.com/{pure_handle}"
        user_line = f'👉 <b>{name_clean}</b> {verified_icon} (<a href="{url}">{handle_display}</a>)'
    else:
        user_line = f"👉 <b>{name_clean}</b> {verified_icon} ({handle_display})"

    followers_str = f"{followers:,}".replace(",", " ") if isinstance(followers, int) else "Inconnu"

    age_line = ""
    if created_at:
        try:
            created_dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            days_old = (now - created_dt).days
            if days_old < 4:
                age_line = f"\n⚠️ <b>EARLY : Créé il y a {days_old} jours !</b>"
        except: pass

    loc_line = f"\n📍 <b>Loc :</b> {str(location).replace('<', '&lt;')}" if location else ""
    
    mutuals_text = ""
    if mutuals:
        names = ", ".join([f"@{m}" for m in mutuals[:3]])
        if len(mutuals) > 3: names += f" (+{len(mutuals)-3})"
        mutuals_text = f"\n\n🤝 <b>Déjà suivi par :</b> {names}"

    # Construction du message
    message = (
        f"🚨 <b>Nouveau Follow !</b>\n"
        f"👤 <b>@{target}</b> a suivi :\n\n"
        f"{user_line}\n"
        f"📊 <b>Abonnés :</b> {followers_str}"
        f"{loc_line}"
        f"{age_line}\n"
        f"ℹ️ <i>{bio_clean}</i>"
        f"{mutuals_text}"
    )
    
    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": config.TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    
    # Envoi avec système de Retry (Anti-Bug Telegram)
    for attempt in range(3):
        try:
            r = requests.get(api_url, params=params, timeout=20)
            if r.status_code == 200:
                return # Succès
            elif r.status_code == 429:
                # Trop de requêtes, on attend un peu
                sleep_time = int(r.json().get('parameters', {}).get('retry_after', 10))
                time.sleep(sleep_time + 1)
            else:
                print(f"❌ Erreur Telegram {r.status_code}: {r.text}")
                break
        except Exception as e:
            time.sleep(2)

# --- 3. MOTEUR API (EXTRACTION MODIFIÉE) ---

def get_headers():
    return {
        "x-rapidapi-key": config.API_KEY,
        "x-rapidapi-host": config.API_HOST
    }

def get_following_ids(handle):
    all_ids = []
    cursor = ""
    print(f"    📥 Téléchargement IDs de @{handle}...")
    url = f"{config.BASE_URL}/following-ids"
    
    while True:
        try:
            wait_for_api()
            querystring = {"username": handle, "count": "500", "cursor": cursor}
            r = requests.get(url, headers=get_headers(), params=querystring, timeout=TIMEOUT_SEC)
            
            if r.status_code != 200: break
            data = r.json()
            ids_chunk = data.get('ids', []) or data.get('results', [])
            
            if not ids_chunk: break
            all_ids.extend([str(x) for x in ids_chunk])
            
            if len(all_ids) % 2000 == 0: print(f"      -> {len(all_ids)} IDs...")
            
            cursor = data.get('next_cursor_str')
            if not cursor or cursor == "0": break
            if len(all_ids) > 15000: break # Sécurité gros comptes
        except: break
    return set(all_ids)

def find_legacy_object(data, depth=0):
    # Cherche l'objet 'legacy' qui contient les infos utiles dans le JSON Twitter
    if depth > 10: return None, None
    if isinstance(data, dict):
        if 'legacy' in data and isinstance(data['legacy'], dict): return data['legacy'], data 
        if 'screen_name' in data: return data, data
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                res, par = find_legacy_object(v, depth+1)
                if res: return res, par
    elif isinstance(data, list):
        for item in data:
            res, par = find_legacy_object(item, depth+1)
            if res: return res, par
    return None, None

def extract_info_smart(user_data_raw):
    try:
        legacy, parent_obj = find_legacy_object(user_data_raw)
        if not legacy: return {"handle": None, "name": "Inconnu", "description": "-", "followers": 0, "created_at": None, "location": None, "website": None, "verified": False}

        handle = legacy.get('screen_name')
        loc = legacy.get('location') 
        # Parfois la location est cachée un niveau au dessus
        if not loc and parent_obj and 'location' in parent_obj:
            l = parent_obj['location']
            loc = l.get('location') if isinstance(l, dict) else l
        
        # MODIFICATION : Extraction du site web
        website = None
        if 'entities' in legacy and 'url' in legacy['entities']:
            try:
                urls = legacy['entities']['url'].get('urls', [])
                if urls: website = urls[0].get('expanded_url')
            except: pass

        # MODIFICATION : Extraction du statut vérifié
        is_verified = legacy.get('verified', False)

        return {
            "handle": handle,
            "name": legacy.get('name'),
            "description": legacy.get('description'),
            "followers": legacy.get('followers_count', 0),
            "created_at": legacy.get('created_at'),
            "location": loc,
            "website": website,
            "verified": is_verified
        }
    except: return None

def get_users_bulk_details(id_list):
    results_map = {} 
    chunk_size = 40
    id_list_list = list(id_list)
    url = f"{config.BASE_URL}/get-users"

    for i in range(0, len(id_list_list), chunk_size):
        chunk = id_list_list[i:i + chunk_size]
        print(f"    🔍 Analyse de {len(chunk)} profils...")
        ids_string = ",".join(str(uid) for uid in chunk)
        
        try:
            wait_for_api()
            r = requests.get(url, headers=get_headers(), params={"users": ids_string}, timeout=TIMEOUT_SEC)
            if r.status_code != 200: continue
            data = r.json()
            
            users_found = []
            if 'result' in data and 'data' in data['result']: users_found = data['result']['data'].get('users', [])
            elif 'results' in data: users_found = data['results']
            elif 'data' in data: users_found = data['data']
            
            for user in users_found:
                uid = None
                if 'result' in user and 'rest_id' in user['result']: uid = str(user['result']['rest_id'])
                else: uid = str(user.get('rest_id') or user.get('id'))
                
                if uid:
                    info = extract_info_smart(user)
                    if info and info['handle']: results_map[uid] = info
        except: pass
    return results_map

def get_user_details_fallback(user_id):
    # Méthode de secours si le bulk échoue
    url = f"{config.BASE_URL}/user"
    try:
        wait_for_api()
        r = requests.get(url, headers=get_headers(), params={"userId": str(user_id)}, timeout=TIMEOUT_SEC)
        return extract_info_smart(r.json()) 
    except: pass
    return None

# --- 4. PROGRAMME PRINCIPAL ---

def main():
    check_data_folder()
    today_str = datetime.now().strftime("%Y-%m-%d")
    csv_filename = f"nouveaux_follows_{today_str}.csv"
    
    print(f"\n=== Dealflow Twitter 50 Partners ===")
    
    # Création du CSV si besoin (MODIFICATION : Ajout des colonnes Website et Verified)
    if not os.path.isfile(csv_filename):
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Cible", "Handle", "Nom", "Bio", "Followers", "Mutuals", "Date", "Location", "Website", "Verified"])

    # Boucle sur chaque cible
    for raw_target in config.TARGETS:
        target = raw_target.replace("@", "").strip()
        print(f"\n--- Analyse de @{target} ---")
        
        # 1. Récupérer la liste actuelle
        current_ids = get_following_ids(target)
        if not current_ids:
            print(f"⚠️ Aucun ID trouvé ou erreur API.")
            continue
        
        # 2. Comparer avec la liste précédente
        previous_ids = load_previous_follows(target)
        if not previous_ids:
            print(f"ℹ️ Première analyse ({len(current_ids)} abonnements). Base de données initialisée.")
            save_current_follows(target, current_ids)
            continue
        
        new_ids = current_ids - previous_ids
        
        # 3. Traiter les nouveaux
        if len(new_ids) > 0:
            # Sécurité anti-flood (si + de 200 d'un coup, on ignore pour éviter le spam)
            if len(new_ids) > 200:
                print(f"⛔ SÉCURITÉ : {len(new_ids)} nouveaux follows. Mise à jour silencieuse.")
                save_current_follows(target, current_ids)
                continue 

            print(f"🚨 {len(new_ids)} NOUVEAUX FOLLOWS !")
            
            # Récupérer les détails (Bio, Nom, etc.)
            details_map = get_users_bulk_details(new_ids)
            
            for new_uid in new_ids:
                new_uid_str = str(new_uid)
                info = details_map.get(new_uid_str)
                
                # Si pas d'info dans le bulk, on tente le fallback
                if not info or info['handle'].startswith("ID_"):
                     fallback = get_user_details_fallback(new_uid_str)
                     if fallback and fallback['handle']: info = fallback

                # Valeurs par défaut
                handle_display = f"ID_{new_uid_str}"
                name_display = "Inconnu"
                bio_display = "-"
                followers_val = 0
                created_at_val = None
                location_val = None
                website_val = None
                verified_val = False
                
                if info:
                    if info['handle']: handle_display = f"@{info['handle']}"
                    name_display = info['name'] or "Inconnu"
                    bio_display = str(info['description']).replace("\n", " ") if info['description'] else "-"
                    followers_val = info.get('followers', 0)
                    created_at_val = info.get('created_at')
                    location_val = info.get('location')
                    website_val = info.get('website')
                    verified_val = info.get('verified', False)

                # Vérifier les follows mutuels
                mutuals_list = get_mutual_follows(new_uid_str, target)
                mutuals_str = ", ".join(mutuals_list) if mutuals_list else "-"
                
                # 4. Enregistrer dans le CSV (MODIFICATION : Ajout des données)
                csv_loc = str(location_val) if location_val else "-"
                csv_web = str(website_val) if website_val else "-"
                csv_ver = "Oui" if verified_val else "Non"

                with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([target, handle_display, name_display, bio_display, followers_val, mutuals_str, today_str, csv_loc, csv_web, csv_ver])
                    print(f"    ✅ CSV : {handle_display}")

                # 5. Envoyer l'alerte Telegram (MODIFICATION : Passage des nouveaux arguments)
                # On filtre : Si plus de 15 000 abonnés, on n'envoie PAS sur Telegram
                if followers_val > 15000:
                    print(f"    🔕 Ignoré (Too late : {followers_val} abos) : {handle_display}")
                else:
                    # Sinon, on envoie l'alerte normalement
                    print(f"    ✅ {handle_display}")
                    send_telegram_alert(target, handle_display, name_display, bio_display, followers_val, mutuals_list, created_at_val, location_val, website_val, verified_val)
                    time.sleep(2)

                # Petite pause pour ne pas stresser l'API Telegram
                time.sleep(2) 
        else:
            print("💤 Rien de nouveau.")
            
        # 6. Sauvegarder l'état actuel pour la prochaine fois
        save_current_follows(target, current_ids)

    print("\n=== Terminé ===")

if __name__ == "__main__":
    main()