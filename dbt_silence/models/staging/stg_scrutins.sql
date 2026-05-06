SELECT 
    uid as scrutin_id,
    numero as scrutin_numero,
    legislature,
    CAST(date AS DATE) as date_scrutin,
    titre as scrutin_titre,
    sort as scrutin_sort,
    nb_votants,
    nb_pour,
    nb_contre,
    nb_abstention
FROM {{ source('raw', 'scrutins') }}
