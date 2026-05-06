-- On ne garde que les textes uniques pour gagner du temps
WITH unique_lobbying AS (
    SELECT DISTINCT lobbying_objet 
    FROM {{ ref('stg_lobbying') }}
    WHERE lobbying_objet IS NOT NULL
),
unique_scrutins AS (
    SELECT DISTINCT scrutin_id, scrutin_titre 
    FROM {{ ref('stg_scrutins') }}
    WHERE scrutin_titre IS NOT NULL
)

SELECT 
    l.lobbying_objet,
    s.scrutin_id,
    s.scrutin_titre
FROM unique_lobbying l
CROSS JOIN unique_scrutins s
-- On peut déjà filtrer par mots-clés simples pour réduire le bruit (optionnel)
-- Ou par date (un vote ne peut pas être influencé par un lobbying qui a lieu 1 an après)
