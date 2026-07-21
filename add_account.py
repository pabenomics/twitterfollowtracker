import tracker  # On réutilise votre code existant (API, Sauvegarde)
import config
import os

def add_single_target():
    print("--- AJOUT D'UNE NOUVELLE CIBLE ---")
    
    # 1. Demande du pseudo
    raw_handle = input("Entrez le pseudo (ex: @NASA) : ")
    # Nettoyage
    handle = raw_handle.replace("@", "").strip()
    
    if not handle:
        print("❌ Pseudo vide.")
        return

    # 2. Vérification si déjà présent
    if handle in config.TARGETS:
        print(f"⚠️ {handle} est déjà dans votre liste TARGETS.")
        # On continue quand même pour forcer la mise à jour des données si besoin
    
    # 3. Initialisation des données (Appel API)
    print(f"\n📥 Initialisation de la base pour @{handle}...")
    
    # On s'assure que le dossier data existe
    tracker.check_data_folder()
    
    # On utilise la fonction de tracker.py pour récupérer les IDs
    ids = tracker.get_following_ids(handle)
    
    if ids:
        count = len(ids)
        print(f"✅ Succès ! {count} abonnements trouvés.")
        
        # 4. Sauvegarde du fichier JSON (La "Photo" de départ)
        tracker.save_current_follows(handle, ids)
        print(f"💾 Fichier 'data/{handle}_ids.json' créé.")
        
        # 5. Ajout automatique à config.py
        if handle not in config.TARGETS:
            print("\n✍️  Ajout au fichier config.py...")
            try:
                with open("config.py", "a") as f:
                    # On ajoute une ligne de code python qui s'exécutera au prochain lancement
                    f.write(f'\nTARGETS.append("{handle}") # Ajouté via script\n')
                print("✅ config.py mis à jour !")
            except Exception as e:
                print(f"❌ Erreur lors de l'écriture dans config.py : {e}")
                print(f"👉 Ajoutez manuellement '{handle}' dans la liste TARGETS.")
        else:
            print("ℹ️  Le pseudo est déjà dans config.py, rien à modifier.")
            
        print(f"\n🚀 Terminé ! Au prochain lancement de 'tracker.py', @{handle} sera surveillé.")
        
    else:
        print("❌ Impossible de récupérer les données (Compte privé, inexistant ou erreur API).")
        print("   Rien n'a été modifié.")

if __name__ == "__main__":
    add_single_target()