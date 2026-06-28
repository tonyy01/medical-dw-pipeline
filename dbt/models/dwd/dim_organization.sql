-- ============================================================
-- 医疗机构维度表
-- 来源：ods.organizations
-- ============================================================

SELECT
    row_number() OVER (ORDER BY organization_id) AS organization_sk,
    organization_id,
    name,
    address_city,
    address_state,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'organizations') }}
