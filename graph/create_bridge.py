# graph/create_bridge.py
from neo4j import GraphDatabase
import duckdb

class SilenceGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_bridge(self):
        con = duckdb.connect('data/hatvp.duckdb')
        
        # On définit des paires (Domaine HATVP, Mot-clé Titre Scrutin)
        # C'est une version simplifiée du NLP du Ch. 06
        mappings = [
            ('Santé', 'santé'),
            ('Santé', 'sécurité sociale'),
            ('Agriculture', 'agricole'),
            ('Energie', 'énergie'),
            ('Energie', 'nucléaire'),
            ('Environnement', 'écologie'),
            ('Environnement', 'climat'),
            ('Numérique', 'numérique'),
            ('Numérique', 'technologie')
        ]

        print("Création des liens d'intérêt (VEUT_INFLUENCER)...")
        
        for domaine, keyword in mappings:
            # On cherche les IDs des fiches et des scrutins qui matchent
            query = f"""
                SELECT DISTINCT org_id, scrutin_id
                FROM stg_lobbying l, stg_scrutins s
                WHERE l.lobbying_domaines LIKE '%{domaine}%'
                AND s.scrutin_titre ILIKE '%{keyword}%'
            """
            links = con.execute(query).fetchall()
            
            if links:
                with self.driver.session() as session:
                    session.run("""
                        UNWIND $data AS row
                        MATCH (l:Lobbyiste {id: row[0]})
                        MATCH (s:Scrutin {id: row[1]})
                        MERGE (l)-[:VEUT_INFLUENCER {domaine: $domaine}]->(s)
                    """, data=links, domaine=domaine)
                print(f"  - {domaine} ({keyword}) : {len(links)} liens créés.")

def main():
    graph = SilenceGraph("bolt://localhost:7687", "neo4j", "password123")
    graph.create_bridge()
    graph.close()

if __name__ == '__main__':
    main()