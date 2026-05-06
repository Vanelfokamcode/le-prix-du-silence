# (Simulations de liens basés sur les secteurs pour le test)
query = """
MATCH (l:Lobbyiste)
MATCH (s:Scrutin)
WHERE (l.name CONTAINS 'MUTUALITE' AND s.title CONTAINS 'santé')
   OR (l.name CONTAINS 'ENERGIE' AND s.title CONTAINS 'énergie')
MERGE (l)-[:VEUT_INFLUENCER]->(s)
"""