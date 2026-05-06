# graph/ingest_neo4j.py
from neo4j import GraphDatabase
import duckdb

class SilenceGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_nodes(self):
        con = duckdb.connect('data/hatvp.duckdb')
        
        # 1. Créer les Députés
        deputes = con.execute("SELECT acteur_id, prenom, nom, groupe_abrege FROM stg_deputes").fetchall()
        with self.driver.session() as session:
            session.run("UNWIND $data AS row CREATE (:Depute {id: row[0], name: row[1] + ' ' + row[2], groupe: row[3]})", data=deputes)

        # 2. Créer les Lobbyistes (Organisations)
        orgs = con.execute("SELECT DISTINCT org_id, org_nom, org_categorie FROM stg_lobbying").fetchall()
        with self.driver.session() as session:
            session.run("UNWIND $data AS row CREATE (:Lobbyiste {id: row[0], name: row[1], cat: row[2]})", data=orgs)

        print("Nodes créés dans Neo4j.")

def main():
    # Remplace par tes identifiants Neo4j
    graph = SilenceGraph("bolt://localhost:7687", "neo4j", "password123")
    graph.create_nodes()
    graph.close()

if __name__ == '__main__':
    main()