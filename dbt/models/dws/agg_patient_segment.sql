-- ============================================================
-- DWS：患者群体分析
-- 按性别 + 年龄组 + 年度聚合
-- ============================================================

WITH patient_encounters AS (
    SELECT
        dp.patient_id,
        dp.gender,
        dp.age_group,
        dd.year,
        COUNT(fe.encounter_id) AS encounter_count,
        SUM(fe.total_claim_cost) AS annual_cost
    FROM {{ ref('fact_encounter') }} fe
    LEFT JOIN {{ ref('dim_patient') }} dp
        ON fe.patient_sk = dp.patient_sk
    LEFT JOIN {{ ref('dim_date') }} dd
        ON fe.date_sk = dd.date_sk
    GROUP BY dp.patient_id, dp.gender, dp.age_group, dd.year
)

SELECT
    gender,
    age_group,
    year,
    count(DISTINCT patient_id) AS patient_count,
    round(avg(encounter_count), 2) AS avg_annual_encounters,
    round(avg(annual_cost), 2) AS avg_annual_cost
FROM patient_encounters
WHERE gender IS NOT NULL AND age_group IS NOT NULL
GROUP BY gender, age_group, year
ORDER BY year, gender, age_group
