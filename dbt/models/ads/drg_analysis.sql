-- ============================================================
-- ADS：DRG 分析 — 按诊断分组的费用/住院时长基准
-- 模拟 DRG 分组分析，展示数据在医疗管理中的应用
-- ============================================================

WITH diagnosis_cost AS (
    SELECT
        dd.diagnosis_sk_ref,
        fe.encounter_id,
        fe.total_claim_cost,
        fe.encounter_duration_minutes,
        EXTRACT(YEAR FROM fe.encounter_start) AS year
    FROM {{ ref('fact_diagnosis') }} fd
    LEFT JOIN {{ ref('fact_encounter') }} fe
        ON fd.encounter_sk = fe.encounter_sk
    LEFT JOIN {{ ref('dim_diagnosis') }} dd
        ON fd.diagnosis_sk_ref = dd.diagnosis_sk
    WHERE fe.encounter_class = 'inpatient'
)

SELECT
    dd.code AS diagnosis_code,
    dd.description AS diagnosis_desc,
    count(DISTINCT dc.encounter_id) AS patient_count,
    round(avg(dc.encounter_duration_minutes / 1440.0), 2) AS avg_los_days,
    round(avg(dc.total_claim_cost), 2) AS avg_total_cost,
    round(percentile_cont(0.5) WITHIN GROUP (ORDER BY dc.total_claim_cost), 2) AS median_total_cost,
    -- 30 天再入院率（简化计算）
    NULL::numeric AS readmission_rate_30d,
    dc.year::varchar AS data_period
FROM diagnosis_cost dc
LEFT JOIN {{ ref('dim_diagnosis') }} dd
    ON dc.diagnosis_sk_ref = dd.diagnosis_sk
GROUP BY dd.code, dd.description, dc.year
HAVING count(DISTINCT dc.encounter_id) >= 5
ORDER BY avg_total_cost DESC
