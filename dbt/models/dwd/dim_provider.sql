-- ============================================================
-- 医生/提供者维度表
-- 来源：ods.providers + ods.organizations
-- ============================================================

SELECT
    row_number() OVER (ORDER BY p.provider_id) AS provider_sk,
    p.provider_id,
    p.name,
    p.gender,
    p.specialty,
    p.organization_id,
    o.name AS organization_name,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'providers') }} p
LEFT JOIN {{ source('ods', 'organizations') }} o
    ON p.organization_id = o.organization_id
