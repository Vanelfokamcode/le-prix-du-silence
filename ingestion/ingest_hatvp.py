import json
import pandas as pd
import duckdb

def extraire_fiches(data):
    """
    Parcourt le JSON HATVP et retourne une liste de dicts plats.
    Une ligne = une fiche d'activité déclarée.
    """
    fiches = []

    for org in data['publications']:
        org_id        = org.get('identifiantNational')
        org_nom       = org.get('denomination')
        org_nom_usage = org.get('nomUsage')
        org_categorie = org.get('categorieOrganisation', {})
        org_cat_label = org_categorie.get('label') if isinstance(org_categorie, dict) else None

        for exercice in org.get('exercices', []):
            pub = exercice.get('publicationCourante', {})
            if not isinstance(pub, dict):
                continue

            annee_debut = pub.get('dateDebut', '')[-4:]

            activites = pub.get('activites', [])
            if not isinstance(activites, list):
                continue

            for acte in activites:
                fiche = acte.get('publicationCourante', {})
                if not isinstance(fiche, dict):
                    continue

                fiche_id   = fiche.get('identifiantFiche')
                objet      = fiche.get('objet')
                domaines   = fiche.get('domainesIntervention', [])
                domaines_str = ' | '.join(domaines) if isinstance(domaines, list) else None

                # Actions : on aplatit aussi — une fiche peut avoir plusieurs actions
                actions = fiche.get('actionsRepresentationInteret', [])
                if not isinstance(actions, list) or len(actions) == 0:
                    # Fiche sans actions — on garde quand même
                    fiches.append({
                        'fiche_id':           fiche_id,
                        'org_id':             org_id,
                        'org_nom':            org_nom,
                        'org_nom_usage':      org_nom_usage,
                        'org_categorie':      org_cat_label,
                        'annee':              annee_debut,
                        'objet':              objet,
                        'domaines':           domaines_str,
                        'responsables':       None,
                        'decisions':          None,
                        'actions_menees':     None,
                        'vise_depute':        False,
                    })
                    continue

                for action in actions:
                    resp  = action.get('reponsablesPublics', [])
                    dec   = action.get('decisionsConcernees', [])
                    actes = action.get('actionsMenees', [])

                    resp_str  = ' | '.join(resp)  if isinstance(resp, list)  else None
                    dec_str   = ' | '.join(dec)   if isinstance(dec, list)   else None
                    actes_str = ' | '.join(actes) if isinstance(actes, list) else None

                    vise_depute = any(
                        'député' in r.lower() or 'parlement' in r.lower()
                        for r in (resp or [])
                    )

                    fiches.append({
                        'fiche_id':        fiche_id,
                        'org_id':          org_id,
                        'org_nom':         org_nom,
                        'org_nom_usage':   org_nom_usage,
                        'org_categorie':   org_cat_label,
                        'annee':           annee_debut,
                        'objet':           objet,
                        'domaines':        domaines_str,
                        'responsables':    resp_str,
                        'decisions':       dec_str,
                        'actions_menees':  actes_str,
                        'vise_depute':     vise_depute,
                    })

    return fiches


def main():
    print("Chargement du JSON HATVP...")
    with open('data/raw/hatvp.json') as f:
        data = json.load(f)

    print("Extraction des fiches...")
    fiches = extraire_fiches(data)
    print(f"  → {len(fiches)} lignes extraites")

    print("Chargement dans DuckDB...")
    con = duckdb.connect('data/hatvp.duckdb')

    print("Chargement dans DuckDB...")
    con = duckdb.connect('data/hatvp.duckdb')

    df = pd.DataFrame(fiches)
    con.execute("DROP TABLE IF EXISTS fiches_lobbying")
    con.execute("CREATE TABLE fiches_lobbying AS SELECT * FROM df")

    # Vérification
    total     = con.execute("SELECT COUNT(*) FROM fiches_lobbying").fetchone()[0]
    deputes   = con.execute("SELECT COUNT(*) FROM fiches_lobbying WHERE vise_depute = true").fetchone()[0]
    nb_orgs   = con.execute("SELECT COUNT(DISTINCT org_id) FROM fiches_lobbying").fetchone()[0]
    nb_annees = con.execute("SELECT DISTINCT annee FROM fiches_lobbying ORDER BY annee").fetchall()

    print(f"\n✓ Table fiches_lobbying chargée")
    print(f"  Total lignes    : {total:,}")
    print(f"  Visant députés  : {deputes:,}")
    print(f"  Organisations   : {nb_orgs:,}")
    print(f"  Années          : {[a[0] for a in nb_annees]}")

    con.close()
    print("\nDuckDB saved → data/hatvp.duckdb")


if __name__ == '__main__':
    main()