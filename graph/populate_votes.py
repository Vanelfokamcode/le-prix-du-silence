from neo4j import GraphDatabase
import duckdb

class SilenceGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def populate_votes(self):
        con = duckdb.connect('data/hatvp.duckdb')
        
        # 1. Créer les Scrutins
        # On cast la date en VARCHAR directement en SQL
        print("Création des Scrutins...")
        scrutins = con.execute("""
            SELECT scrutin_id, scrutin_titre, CAST(date_scrutin AS VARCHAR) 
            FROM stg_scrutins
        """).fetchall()
        
        with self.driver.session() as session:
            session.run("""
                UNWIND $data AS row 
                CREATE (:Scrutin {id: row[0], title: row[1], date: row[2]})
            """, data=scrutins)

        # 2. Créer les relations de Vote
        print("Création des relations de Vote (pours/contres)...")
        # On s'assure que les IDs sont bien traités comme des strings
        votes = con.execute("""
            SELECT CAST(acteur_id AS VARCHAR), scrutin_id, vote_position 
            FROM stg_votes 
            WHERE vote_position IN ('pours', 'contres')
        """).fetchall()
        
        batch_size = 5000 # On réduit un peu la taille pour la stabilité
        for i in range(0, len(votes), batch_size):
            batch = votes[i:i + batch_size]
            with self.driver.session() as session:
                session.run("""
                    UNWIND $data AS row
                    MATCH (d:Depute {id: row[0]})
                    MATCH (s:Scrutin {id: row[1]})
                    MERGE (d)-[:A_VOTE {position: row[2]}]->(s)
                """, data=batch)
            if i % 25000 == 0:
                print(f"  Processed {i} votes...")
def main():
    graph = SilenceGraph("bolt://localhost:7687", "neo4j", "password123")
    graph.populate_votes()
    graph.close()

if __name__ == '__main__':
    main()