WITH raw_deputes AS (
    SELECT * FROM {{ source('raw', 'deputes') }}
),
raw_groupes AS (
    SELECT * FROM {{ source('raw', 'groupes_politiques') }}
)

SELECT 
    CAST(d.acteur_ref AS VARCHAR) as acteur_id,
    d.prenom,
    d.nom,
    d.profession,
    g.groupe_abrege,
    g.groupe_libelle
FROM raw_deputes d
LEFT JOIN raw_groupes g ON CAST(d.groupe_id AS VARCHAR) = CAST(g.groupe_id AS VARCHAR)
