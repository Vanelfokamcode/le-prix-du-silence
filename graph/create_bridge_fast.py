# graph/create_bridge_fast.py
from neo4j import GraphDatabase
import duckdb

class SilenceGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_bridge(self):
        con = duckdb.connect('data/hatvp.duckdb')
        
        mappings = [
            ('Santé', 'santé'), ('Santé', 'sécurité sociale'),
            ('Agriculture', 'agricole'), ('Energie', 'énergie'),
            ('Environnement', 'écologie'), ('Numérique', 'numérique')
        ]

        print("🚀 Démarrage du pontage Turbo...")
        
        for domaine, keyword in mappings:
            # OPTIMISATION : On ne prend que les orgs qui ont réellement des fiches
            query = f"""
                SELECT DISTINCT org_id, scrutin_id
                FROM stg_lobbying l
                JOIN stg_scrutins s ON (s.scrutin_titre ILIKE '%{keyword}%')
                WHERE l.lobbying_domaines LIKE '%{domaine}%'
            """
            links = con.execute(query).fetchall()
            
            if not links: continue

            print(f"  📥 Injection de {len(links)} liens pour {domaine}...")
            
            # Injection par batchs de 10 000
            batch_size = 10000
            for i in range(0, len(links), batch_size):
                batch = links[i:i + batch_size]
                with self.driver.session() as session:
                    session.run("""
                        UNWIND $data AS row
                        MATCH (l:Lobbyiste {id: row[0]})
                        MATCH (s:Scrutin {id: row[1]})
                        CREATE (l)-[:VEUT_INFLUENCER]->(s)
                    """, data=batch)
            print(f"  ✅ {domaine} terminé.")

def main():
    graph = SilenceGraph("bolt://localhost:7687", "neo4j", "password123")
    graph.create_bridge()
    graph.close()

if __name__ == '__main__':
    main()