# graph/reboot_bridge.py
import duckdb
from neo4j import GraphDatabase

con = duckdb.connect('data/hatvp.duckdb')
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))

def bridge():
    mappings = [
        ('Santé', 'santé'), ('Santé', 'sécurité sociale'),
        ('Agriculture', 'agricole'), ('Energie', 'énergie'),
        ('Environnement', 'écologie'), ('Numérique', 'numérique')
    ]
    
    for domaine, keyword in mappings:
        print(f"Calcul des liens pour {domaine}...")
        query = f"""
            SELECT DISTINCT CAST(org_id AS VARCHAR), scrutin_id
            FROM stg_lobbying l
            JOIN stg_scrutins s ON (s.scrutin_titre ILIKE '%{keyword}%')
            WHERE l.lobbying_domaines LIKE '%{domaine}%'
        """
        links = con.execute(query).fetchall()
        
        if links:
            print(f"  📥 Injection de {len(links)} liens...")
            batch_size = 5000
            for i in range(0, len(links), batch_size):
                batch = links[i:i + batch_size]
                with driver.session() as session:
                    # Ici on utilise MATCH pour être SUR de ne pas créer de nœuds vides
                    session.run("""
                        UNWIND $data AS row
                        MATCH (l:Lobbyiste {id: row[0]})
                        MATCH (s:Scrutin {id: row[1]})
                        CREATE (l)-[:VEUT_INFLUENCER]->(s)
                    """, data=batch)

if __name__ == "__main__":
    bridge()