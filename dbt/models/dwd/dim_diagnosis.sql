-- ============================================================
-- 诊断维度表（SCD Type 1）
-- 来源：ods.conditions 中的去重诊断代码
-- ============================================================

SELECT DISTINCT
    code,
    -- 取该诊断代码的第一个非空描述作为标准名称
    first_value(description) OVER (
        PARTITION BY code
        ORDER BY condition_start DESC NULLS LAST
    ) AS description,
    'ICD-10-CM' AS code_system,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'conditions') }}
WHERE code IS NOT NULL
