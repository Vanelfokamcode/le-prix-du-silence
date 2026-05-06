# graph/reboot_lobbyists.py
import duckdb
from neo4j import GraphDatabase
import os

# Configuration des chemins pour Dagster
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "hatvp.duckdb")

def reboot():
    con = duckdb.connect(DB_PATH)
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    
    # On récupère les données propres
    data = con.execute("SELECT DISTINCT CAST(org_id AS VARCHAR), org_nom, org_categorie FROM stg_lobbying").fetchall()
    
    with driver.session() as session:
        print("Nettoyage des anciens lobbyistes...")
        session.run("MATCH (l:Lobbyiste) DETACH DELETE l")
        
        print("Gestion de l'index...")
        # On essaie la syntaxe standard, si ça échoue on ignore (l'index est peut-être déjà là)
        try:
            session.run("CREATE INDEX lobbyist_id_idx FOR (l:Lobbyiste) ON (l.id)")
        except Exception as e:
            print(f"Note: L'index existe déjà ou syntaxe non supportée, on continue... ({e})")
        
        print(f"Import de {len(data)} lobbyistes...")
        session.run("""
            UNWIND $data AS row
            CREATE (:Lobbyiste {id: row[0], name: row[1], cat: row[2]})
        """, data=data)
        
    print("🚀 Reboot Lobbyistes terminé.")
    driver.close()
    con.close()

if __name__ == "__main__":
    reboot()