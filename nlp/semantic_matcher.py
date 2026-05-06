# nlp/semantic_matcher.py
import spacy
import duckdb
import pandas as pd

print("Chargement du modèle NLP français (Medium)...")
nlp = spacy.load("fr_core_news_md")

def main():
    con = duckdb.connect('data/hatvp.duckdb')
    
    # On restreint drastiquement pour le test
    print("Extraction des données...")
    df = con.execute("""
        SELECT 
            l.lobbying_objet, 
            s.scrutin_titre
        FROM stg_lobbying l, stg_scrutins s
        WHERE l.lobbying_domaines LIKE '%Santé%'
        AND (s.scrutin_titre LIKE '%santé%' OR s.scrutin_titre LIKE '%sécurité sociale%')
        LIMIT 50
    """).df()

    if df.empty:
        print("Aucune paire trouvée avec ces filtres.")
        return

    print(f"Calcul de similarité sur {len(df)} paires...")
    
    # On transforme les colonnes en listes pour le pipe
    objets = list(df['lobbying_objet'])
    titres = list(df['scrutin_titre'])
    
    # Traitement batch
    docs_objets = list(nlp.pipe(objets))
    docs_titres = list(nlp.pipe(titres))
    
    similarities = []
    for d1, d2 in zip(docs_objets, docs_titres):
        similarities.append(d1.similarity(d2))
    
    df['similarity'] = similarities

    print("\n=== TOP MATCHES TROUVÉS ===")
    print(df.sort_values(by='similarity', ascending=False).head(10))

if __name__ == '__main__':
    main()