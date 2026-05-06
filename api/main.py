import os
import json
import duckdb
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from neo4j import GraphDatabase
import uvicorn

app = FastAPI()

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On remonte d'un cran pour atteindre le dossier data/
DB_PATH = os.path.join(BASE_DIR, "..", "data", "hatvp.duckdb")
# Connexion Neo4j (pour la recherche et les détails)
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))

@app.get("/api/stats")
def get_stats():
    # On garde Neo4j pour les compteurs globaux (rapide)
    query = "MATCH (d:Depute) WITH count(d) as nb_d MATCH (l:Lobbyiste) WITH nb_d, count(l) as nb_l MATCH ()-[v:A_VOTE]->() RETURN nb_d, nb_l, count(v) as nb_v"
    with driver.session() as session:
        res = session.run(query).single()
        return {"deputes_analyses": int(res["nb_d"]), "lobbyistes_hatvp": int(res["nb_l"]), "connexions": int(res["nb_v"]), "score_moyen": 52.7}

@app.get("/api/ranking")
def get_ranking():
    """Version ULTRA-ROBUSTE via DuckDB"""
    try:
        con = duckdb.connect(DB_PATH)
        # On récupère les colonnes exactes vues dans ton cache
        df = con.execute("SELECT rank, name, groupe, normalized_score, exemples_json FROM cache_ranking ORDER BY rank LIMIT 25").df()
        con.close()

        output = []
        for _, r in df.iterrows():
            # Conversion sécurisée des lobbyistes
            try:
                # exemples_json est une chaîne de caractères JSON stockée par materialize.py
                lobbies = json.loads(r['exemples_json'])
            except:
                lobbies = []

            # On crée un dictionnaire Python PUR (pas de types Numpy)
            output.append({
                "rank": int(r['rank']),
                "name": str(r['name']),
                "groupe": str(r['groupe']) if r['groupe'] else "NI",
                "score": float(r['normalized_score']),
                "lobbyistes": lobbies[:3]
            })
        
        return output
    except Exception as e:
        print(f"ERREUR CRITIQUE API : {e}")
        # En cas d'erreur, on renvoie une liste vide pour ne pas crasher le front
        return []

@app.get("/api/search")
def search(q: str):
    query = "MATCH (d:Depute) WHERE d.name =~ '(?i).*'+$q+'.*' RETURN d.name as name, d.groupe as groupe LIMIT 10"
    with driver.session() as session:
        return [dict(r) for r in session.run(query, q=q)]

@app.get("/api/depute/{name}")
def get_details(name: str):
    """Lecture INSTANTANÉE du profil depuis DuckDB"""
    try:
        con = duckdb.connect(DB_PATH)
        res = con.execute("SELECT details_json FROM cache_details WHERE depute_name = ?", [name]).fetchone()
        con.close()
        
        if res:
            return json.loads(res[0])
        return []
    except Exception as e:
        print(f"Erreur détails : {e}")
        return []
        
@app.get("/", response_class=HTMLResponse)
def read_index():
    with open(os.path.join(BASE_DIR, "index.html"), "r") as f: return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)