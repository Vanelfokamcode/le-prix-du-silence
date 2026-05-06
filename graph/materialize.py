# graph/materialize.py
import duckdb
from neo4j import GraphDatabase
import json

# Connexion
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
con = duckdb.connect('data/hatvp.duckdb')

def materialize_ranking():
    print("🚀 Calcul lourd du Score du Silence en cours (Neo4j)...")
    query = """
    MATCH (d:Depute)-[:A_VOTE {position: 'pours'}]->(s:Scrutin)<-[:VEUT_INFLUENCER]-(l:Lobbyiste)
    WHERE l.name IS NOT NULL
    WITH d, count(DISTINCT s) AS score, count(DISTINCT l) AS lobby_count
    ORDER BY score DESC
    CALL (d) {
        MATCH (d)-[:A_VOTE {position: 'pours'}]->(s2:Scrutin)<-[:VEUT_INFLUENCER]-(l2:Lobbyiste)
        WHERE l2.name IS NOT NULL
        RETURN collect(DISTINCT l2.name)[0..5] AS exemples
    }
    RETURN d.name as name, d.groupe as groupe, score, exemples
    """
    
    with driver.session() as session:
        result = session.run(query)
        records = [dict(r) for r in result]
        
    if not records:
        print("Erreur : aucune donnée trouvée.")
        return

    # Normalisation
    max_score = records[0]['score']
    for i, r in enumerate(records):
        r['rank'] = i + 1
        r['normalized_score'] = round((r['score'] / max_score) * 100, 1)
        r['exemples_json'] = json.dumps(r['exemples']) # DuckDB aime le texte pour les listes

    # Stockage dans DuckDB (Table de cache)
    print("💾 Stockage des résultats dans DuckDB pour accès instantané...")
    import pandas as pd
    df = pd.DataFrame(records)
    
    con.execute("DROP TABLE IF EXISTS cache_ranking")
    con.execute("CREATE TABLE cache_ranking AS SELECT * FROM df")
    print(f"✅ Terminé. {len(df)} députés mis en cache.")

# graph/materialize.py (Ajout à la fin du fichier)

def materialize_details():
    print("🚀 Pré-calcul des profils détaillés (ceci peut prendre 2-3 minutes)...")
    # Cette requête calcule d'un coup le top 10 pour TOUS les députés
    query = """
    MATCH (d:Depute)-[:A_VOTE {position: 'pours'}]->(s:Scrutin)<-[:VEUT_INFLUENCER]-(l:Lobbyiste)
    WHERE l.name IS NOT NULL
    WITH d.name as depute_name, l.name as lobbyist, count(s) as strength
    ORDER BY strength DESC
    WITH depute_name, collect({lobbyist: lobbyist, strength: strength})[0..10] as top_lobbies
    RETURN depute_name, top_lobbies
    """
    
    with driver.session() as session:
        result = session.run(query)
        records = [dict(r) for r in result]
    
    # Transformation pour DuckDB
    import pandas as pd
    processed = []
    for r in records:
        processed.append({
            "depute_name": r['depute_name'],
            "details_json": json.dumps(r['top_lobbies'])
        })
    
    df = pd.DataFrame(processed)
    con.execute("DROP TABLE IF EXISTS cache_details")
    con.execute("CREATE TABLE cache_details AS SELECT * FROM df")
    con.execute("CREATE INDEX idx_depute ON cache_details (depute_name)")
    print(f"✅ Profils de {len(df)} députés mis en cache.")

if __name__ == "__main__":
    materialize_ranking() # Ton ancien calcul
    materialize_details() # Le nouveau calcul
    driver.close()