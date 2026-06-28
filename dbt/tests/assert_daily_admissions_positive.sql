-- 断言：每日入院数应为正数
SELECT
    date_sk,
    total_admissions
FROM {{ ref('agg_daily_admissions') }}
WHERE total_admissions < 0
