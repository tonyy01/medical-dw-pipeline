-- ============================================================
-- 诊断事实表
-- 粒度：每条诊断记录一行
-- 来源：ods.conditions + 维度表
-- ============================================================

SELECT
    c.condition_id,
    COALESCE(dp.patient_sk, -1) AS patient_sk,
    COALESCE(fe.encounter_sk, -1) AS encounter_sk,
    dd.diagnosis_sk AS diagnosis_sk_ref,
    COALESCE(dd2.date_sk, -1) AS date_sk,
    c.condition_start,
    c.condition_stop,
    CASE WHEN c.condition_stop IS NULL THEN TRUE ELSE FALSE END AS is_active,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'conditions') }} c
LEFT JOIN {{ ref('dim_patient') }} dp
    ON c.patient_id = dp.patient_id
LEFT JOIN {{ ref('fact_encounter') }} fe
    ON c.encounter_id = fe.encounter_id
LEFT JOIN {{ ref('dim_diagnosis') }} dd
    ON c.code = dd.code
LEFT JOIN {{ ref('dim_date') }} dd2
    ON c.condition_start = dd2.full_date
