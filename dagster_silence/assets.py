# dagster_silence/assets.py
from dagster import asset
import os
import subprocess

@asset
def raw_data_files():
    """Vérifie la présence des fichiers JSON bruts"""
    # Ici on pourrait mettre le code de wget/curl pour automatiser le download
    return os.listdir("data/raw")

@asset(deps=[raw_data_files])
def hatvp_duckdb():
    """Lance l'ingestion Python vers DuckDB"""
    subprocess.run(["python", "ingestion/ingest_hatvp.py"], check=True)
    subprocess.run(["python", "ingestion/ingest_scrutins.py"], check=True)

@asset(deps=[hatvp_duckdb])
def neo4j_graph():
    """Peuple le graphe Neo4j et crée les liens sémantiques"""
    # On enchaîne tes scripts de reconstruction
    subprocess.run(["python", "graph/reboot_lobbyists.py"], check=True)
    subprocess.run(["python", "graph/reboot_bridge.py"], check=True)

@asset(deps=[neo4j_graph])
def frontend_cache():
    """Matérialise le cache DuckDB pour la vitesse de l'API"""
    subprocess.run(["python", "graph/materialize.py"], check=True)