-- 断言：病人年龄应合理（不超过 120 岁）
SELECT
    patient_id,
    age_years
FROM {{ ref('dim_patient') }}
WHERE age_years > 120
