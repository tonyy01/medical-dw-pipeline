-- ============================================================
-- DWS：每日入院/就诊汇总
-- 用于监控每日医疗业务量
-- ============================================================

SELECT
    dd.date_sk,
    count(*) AS total_admissions,
    count(*) FILTER (WHERE fe.encounter_class IN ('emergency', 'urgent')) AS emergency_admissions,
    count(*) FILTER (WHERE fe.encounter_class = 'inpatient') AS inpatient_admissions,
    count(*) FILTER (WHERE fe.encounter_class IN ('ambulatory', 'wellness', 'outpatient')) AS outpatient_visits,
    count(DISTINCT fe.patient_sk) AS unique_patients,
    avg(fe.base_encounter_cost) AS avg_encounter_cost,
    sum(fe.total_claim_cost) AS total_claim_cost
FROM {{ ref('fact_encounter') }} fe
LEFT JOIN {{ ref('dim_date') }} dd
    ON fe.date_sk = dd.date_sk
GROUP BY dd.date_sk
ORDER BY dd.date_sk
