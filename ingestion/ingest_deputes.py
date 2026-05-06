# ingestion/ingest_deputes.py
import json
import glob
import duckdb
import pandas as pd

def parser_acteur(fichier):
    with open(fichier) as f:
        data = json.load(f)
    
    a = data['acteur']
    uid = a.get('uid', {}).get('#text') if isinstance(a.get('uid'), dict) else a.get('uid')
    
    # État civil
    ec = a.get('etatCivil', {})
    ident = ec.get('ident', {})
    
    # Mandat pour trouver le groupe politique (GP)
    mandats = a.get('mandats', {}).get('mandat', [])
    if isinstance(mandats, dict):
        mandats = [mandats]
    
    groupe_id = None
    for m in mandats:
        # On cherche le mandat au sein d'un groupe politique (GP)
        if m.get('typeOrgane') == 'GP':
            # NOUVELLE STRUCTURE : c'est dans ['organes']['organeRef']
            organes_data = m.get('organes', {})
            if isinstance(organes_data, dict):
                groupe_id = organes_data.get('organeRef')
            
            # Si on a trouvé un mandat de groupe actif (dateFin est null), on s'arrête
            if not m.get('dateFin'):
                break

    return {
        'acteur_ref': uid,
        'nom': ident.get('nom'),
        'prenom': ident.get('prenom'),
        'profession': a.get('profession', {}).get('libelleCourant') if a.get('profession') else None,
        'groupe_id': groupe_id
    }
    
def main():
    fichiers = glob.glob('data/raw/deputes_17/acteur/*.json')
    print(f"Fichiers acteurs trouvés : {len(fichiers)}")

    acteurs = []
    for f in fichiers:
        try:
            acteurs.append(parser_acteur(f))
        except Exception as e:
            continue

    con = duckdb.connect('data/hatvp.duckdb')
    df_deputes = pd.DataFrame(acteurs)

    con.execute("DROP TABLE IF EXISTS deputes")
    con.execute("CREATE TABLE deputes AS SELECT * FROM df_deputes")

    # On récupère aussi les noms des groupes (organes)
    print("Parsing des noms de groupes...")
    organes = []
    for f in glob.glob('data/raw/deputes_17/organe/*.json'):
        with open(f) as fp:
            data = json.load(fp)
            o = data['organe']
            if o.get('codeType') == 'GP':
                organes.append({
                    'groupe_id': o.get('uid'),
                    'groupe_libelle': o.get('libelle'),
                    'groupe_abrege': o.get('libelleAbrev')
                })
    
    df_groups = pd.DataFrame(organes)
    con.execute("DROP TABLE IF EXISTS groupes_politiques")
    con.execute("CREATE TABLE groupes_politiques AS SELECT * FROM df_groups")

    print(f"✓ {len(acteurs)} députés chargés.")
    print(f"✓ {len(organes)} groupes politiques chargés.")
    con.close()

if __name__ == '__main__':
    main()