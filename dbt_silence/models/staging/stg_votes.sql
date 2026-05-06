SELECT 
    scrutin_uid as scrutin_id,
    CAST(acteur_ref AS VARCHAR) as acteur_id,
    position as vote_position,
    par_delegation
FROM {{ source('raw', 'positions_vote') }}
