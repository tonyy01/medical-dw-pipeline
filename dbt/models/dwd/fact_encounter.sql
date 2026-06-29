-- ============================================================
-- 就诊事实表 — 核心事实表
-- 粒度：每次就诊一行
-- 来源：ods.encounters + 维度表
-- ============================================================

SELECT
    row_number() OVER (ORDER BY e.encounter_id) AS encounter_sk,
    e.encounter_id,
    COALESCE(dp.patient_sk, -1) AS patient_sk,
    COALESCE(dpr.provider_sk, -1) AS provider_sk,
    COALESCE(do2.organization_sk, -1) AS organization_sk,
    COALESCE(dd.date_sk, -1) AS date_sk,
    e.encounter_class,
    e.description,
    e.encounter_start,
    e.encounter_stop,
    -- 就诊时长（分钟）
    CASE
        WHEN e.encounter_stop IS NOT NULL AND e.encounter_start IS NOT NULL
            THEN EXTRACT(EPOCH FROM (e.encounter_stop - e.encounter_start)) / 60
        ELSE NULL
    END::integer AS encounter_duration_minutes,
    e.base_encounter_cost,
    e.total_claim_cost,
    e.payer_coverage,
    current_timestamp AS _etl_loaded_at
FROM {{ source('ods', 'encounters') }} e
LEFT JOIN {{ ref('dim_patient') }} dp
    ON e.patient_id = dp.patient_id
LEFT JOIN {{ ref('dim_provider') }} dpr
    ON e.provider_id = dpr.provider_id
LEFT JOIN {{ ref('dim_organization') }} do2
    ON e.organization_id = do2.organization_id
LEFT JOIN {{ ref('dim_date') }} dd
    ON e.encounter_start::date = dd.full_date
