-- ============================================================
-- ADS：再入院风险评估
-- 识别高风险再入院患者，辅助医疗质量管理
-- ============================================================

WITH patient_admissions AS (
    SELECT
        fe.patient_sk,
        dp.patient_id,
        fe.encounter_start,
        fe.encounter_id,
        -- 同一患者的上一次入院日期
        lag(fe.encounter_start) OVER (
            PARTITION BY fe.patient_sk
            ORDER BY fe.encounter_start
        ) AS prev_admission
    FROM {{ ref('fact_encounter') }} fe
    LEFT JOIN {{ ref('dim_patient') }} dp
        ON fe.patient_sk = dp.patient_sk
    WHERE fe.encounter_class = 'inpatient'
),

patient_summary AS (
    SELECT
        patient_sk,
        patient_id,
        count(*) AS total_admissions,
        min(encounter_start) AS first_admission,
        max(encounter_start) AS last_admission,
        -- 入院间隔
        min(EXTRACT(DAY FROM (encounter_start - prev_admission))) AS days_between_admissions
    FROM patient_admissions
    WHERE total_admissions > 1
    GROUP BY patient_sk, patient_id
),

chronic_count AS (
    SELECT
        patient_sk,
        count(DISTINCT diagnosis_sk_ref) AS num_chronic_conditions
    FROM {{ ref('fact_diagnosis') }}
    WHERE is_active = TRUE
    GROUP BY patient_sk
)

SELECT
    ps.patient_id,
    ps.total_admissions,
    ps.first_admission,
    ps.last_admission,
    ps.days_between_admissions,
    COALESCE(cc.num_chronic_conditions, 0) AS num_chronic_conditions,
    CASE
        WHEN ps.total_admissions >= 5 OR ps.days_between_admissions <= 30 THEN '高风险'
        WHEN ps.total_admissions >= 3 OR ps.days_between_admissions <= 90 THEN '中风险'
        ELSE '低风险'
    END AS risk_level
FROM patient_summary ps
LEFT JOIN chronic_count cc
    ON ps.patient_sk = cc.patient_sk
ORDER BY risk_level, ps.total_admissions DESC
