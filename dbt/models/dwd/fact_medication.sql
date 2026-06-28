-- ============================================================
-- 用药事实表
-- 粒度：每次用药处方一行
-- 来源：ods.medications + 维度表
-- ============================================================

SELECT
    m.medication_id,
    COALESCE(dp.patient_sk, -1) AS patient_sk,
    COALESCE(fe.encounter_sk, -1) AS encounter_sk,
    COALESCE(dd.date_sk, -1) AS date_sk,
    m.code,
    m.description,
    m.base_cost,
    m.payer_coverage,
    m.total_cost,
    m.dispenses,
    m.reasondescription,
    m.start_date,
    m.stop_date,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'medications') }} m
LEFT JOIN {{ ref('dim_patient') }} dp
    ON m.patient_id = dp.patient_id
LEFT JOIN {{ ref('fact_encounter') }} fe
    ON m.encounter_id = fe.encounter_id
LEFT JOIN {{ ref('dim_date') }} dd
    ON m.start_date::date = dd.full_date
