import os
import glob
import csv

def count_unique_history():
    # Trouve tous les fichiers CSV qui commencent par "nouveaux_follows_"
    files = glob.glob("nouveaux_follows_*.csv")
    
    # Un 'set' est une liste qui interdit les doublons
    unique_handles = set()
    total_lines = 0

    print(f"📂 Analyse de {len(files)} fichiers CSV...")

    for filename in files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                # On saute la ligne d'en-tête (Cible, Nouveau Compte, etc.)
                next(reader, None)
                
                for row in reader:
                    if len(row) > 1:
                        # La colonne 1 contient le handle (ex: @ProjetX ou ID_123)
                        handle = row[1]
                        
                        # On l'ajoute au set. Si il y est déjà, ça ne fait rien.
                        unique_handles.add(handle)
                        total_lines += 1
                        
        except Exception as e:
            print(f"⚠️ Erreur lecture {filename}: {e}")

    unique_count = len(unique_handles)

    print("\n" + "="*40)
    print(f"📊 RÉSULTAT DÉDOUBLONNÉ")
    print("="*40)
    print(f"Total des alertes envoyées : {total_lines}")
    print(f"✅ PROJETS UNIQUES RÉELS   : {unique_count}")
    print("="*40)
    print(f"👉 C'est ce chiffre ({unique_count}) qu'il faut entrer")
    print("   dans 'Anciens (Legacy)' sur PythonAnywhere.")

if __name__ == "__main__":
    count_unique_history()