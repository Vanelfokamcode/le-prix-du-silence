# ingestion/ingest_scrutins.py
import json
import glob
import duckdb
import pandas as pd
from pathlib import Path

def parser_scrutin(fichier):
    """
    Retourne (scrutin_row, liste de position_vote rows)
    """
    with open(fichier) as f:
        data = json.load(f)

    s = data['scrutin']

    scrutin_row = {
        'uid':          s.get('uid'),
        'numero':       s.get('numero'),
        'legislature':  s.get('legislature'),
        'date':         s.get('dateScrutin'),
        'titre':        s.get('titre'),
        'sort':         s.get('sort', {}).get('code'),
        'nb_votants':   s.get('syntheseVote', {}).get('nombreVotants'),
        'nb_pour':      s.get('syntheseVote', {}).get('decompte', {}).get('pour'),
        'nb_contre':    s.get('syntheseVote', {}).get('decompte', {}).get('contre'),
        'nb_abstention':s.get('syntheseVote', {}).get('decompte', {}).get('abstentions'),
    }

    positions = []

    groupes = s.get('ventilationVotes', {}).get('organe', {}).get('groupes', {}).get('groupe', [])
    if isinstance(groupes, dict):
        groupes = [groupes]

    for groupe in groupes:
        organe_ref = groupe.get('organeRef')
        decompte   = groupe.get('vote', {}).get('decompteNominatif', {})
        if not isinstance(decompte, dict):
            continue

        for position in ['pours', 'contres', 'abstentions', 'nonVotants']:
            bloc = decompte.get(position, {})
            if not isinstance(bloc, dict):
                continue
            votants = bloc.get('votant', [])
            if isinstance(votants, dict):
                votants = [votants]
            if not isinstance(votants, list):
                continue

            for votant in votants:
                positions.append({
                    'scrutin_uid':   s.get('uid'),
                    'acteur_ref':    votant.get('acteurRef'),
                    'mandat_ref':    votant.get('mandatRef'),
                    'position':      position,        # pours/contres/abstentions/nonVotants
                    'par_delegation': votant.get('parDelegation') == 'true',
                    'organe_ref':    organe_ref,
                })

    return scrutin_row, positions


def main():
    fichiers = glob.glob('data/raw/scrutins/**/*.json', recursive=True)
    print(f"Fichiers scrutins trouvés : {len(fichiers)}")

    tous_scrutins  = []
    toutes_positions = []
    erreurs = 0

    for i, fichier in enumerate(fichiers):
        if i % 500 == 0:
            print(f"  {i}/{len(fichiers)}...")
        try:
            scrutin_row, positions = parser_scrutin(fichier)
            tous_scrutins.append(scrutin_row)
            toutes_positions.extend(positions)
        except Exception as e:
            erreurs += 1

    print(f"  Erreurs : {erreurs}")
    print(f"  Scrutins parsés : {len(tous_scrutins)}")
    print(f"  Positions de vote : {len(toutes_positions):,}")

    con = duckdb.connect('data/hatvp.duckdb')

    df_scrutins   = pd.DataFrame(tous_scrutins)
    df_positions  = pd.DataFrame(toutes_positions)

    con.execute("DROP TABLE IF EXISTS scrutins")
    con.execute("DROP TABLE IF EXISTS positions_vote")

    con.execute("CREATE TABLE scrutins AS SELECT * FROM df_scrutins")
    con.execute("CREATE TABLE positions_vote AS SELECT * FROM df_positions")

    # Vérification
    print()
    print(f"✓ scrutins        : {con.execute('SELECT COUNT(*) FROM scrutins').fetchone()[0]:,} lignes")
    print(f"✓ positions_vote  : {con.execute('SELECT COUNT(*) FROM positions_vote').fetchone()[0]:,} lignes")
    print()

    print("=== RÉPARTITION PAR LEGISLATURE ===")
    print(con.execute("""
        SELECT legislature, COUNT(*) as nb_scrutins
        FROM scrutins
        GROUP BY legislature
        ORDER BY legislature
    """).df().to_string(index=False))

    print()
    print("=== TOP 10 ACTEURS LES PLUS VOTANTS ===")
    print(con.execute("""
        SELECT acteur_ref, COUNT(*) as nb_votes
        FROM positions_vote
        WHERE position = 'pours'
        GROUP BY acteur_ref
        ORDER BY nb_votes DESC
        LIMIT 10
    """).df().to_string(index=False))

    con.close()
    print("\nDuckDB saved → data/hatvp.duckdb")

if __name__ == '__main__':
    main()