SELECT 
    fiche_id,
    org_id,
    org_nom,
    org_categorie,
    annee as exercice_annee,
    objet as lobbying_objet,
    domaines as lobbying_domaines,
    vise_depute
FROM {{ source('raw', 'fiches_lobbying') }}
WHERE vise_depute = true
