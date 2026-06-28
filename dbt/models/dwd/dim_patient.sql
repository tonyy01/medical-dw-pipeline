-- ============================================================
-- 病人维度表
-- 来源：ods.patients（原始数据清洗后）
-- ============================================================

WITH patient_base AS (
    SELECT
        patient_id,
        birth_date,
        death_date,
        gender,
        race,
        ethnicity,
        marital_status,
        blood_type,
        address_city,
        address_state,
        address_county,
        income
    FROM {{ source('ods', 'patients') }}
)

SELECT
    -- Surrogate Key
    row_number() OVER (ORDER BY patient_id) AS patient_sk,
    patient_id,
    birth_date,
    -- 年龄（取整年）
    CASE
        WHEN death_date IS NOT NULL
            THEN EXTRACT(YEAR FROM age(death_date, birth_date))::integer
        ELSE EXTRACT(YEAR FROM age(birth_date))::integer
    END AS age_years,
    -- 年龄分组
    CASE
        WHEN birth_date IS NULL THEN '未知'
        WHEN EXTRACT(YEAR FROM age(birth_date)) < 1 THEN '婴儿'
        WHEN EXTRACT(YEAR FROM age(birth_date)) < 18 THEN '儿童青少年'
        WHEN EXTRACT(YEAR FROM age(birth_date)) < 45 THEN '青年'
        WHEN EXTRACT(YEAR FROM age(birth_date)) < 65 THEN '中年'
        ELSE '老年'
    END AS age_group,
    gender,
    race,
    ethnicity,
    marital_status,
    blood_type,
    address_city,
    address_state,
    address_county,
    -- 收入分层
    CASE
        WHEN income IS NULL THEN '未知'
        WHEN income < 30000 THEN '低收入'
        WHEN income < 75000 THEN '中低收入'
        WHEN income < 125000 THEN '中高收入'
        ELSE '高收入'
    END AS income_bracket,
    CASE WHEN death_date IS NOT NULL THEN TRUE ELSE FALSE END AS is_deceased,
    death_date,
    current_timestamp AS _etl_loaded_at
FROM patient_base
