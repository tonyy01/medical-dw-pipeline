-- ============================================================
-- 日期维度表 — 支持基于日期的分层聚合
-- ============================================================

WITH date_series AS (
    SELECT generate_series(
        '2010-01-01'::date,
        '2030-12-31'::date,
        '1 day'::interval
    )::date AS full_date
)

SELECT
    -- Surrogate Key: YYYYMMDD 格式整数
    to_char(full_date, 'YYYYMMDD')::integer AS date_sk,
    full_date,
    EXTRACT(YEAR FROM full_date)::integer AS year,
    EXTRACT(QUARTER FROM full_date)::integer AS quarter,
    EXTRACT(MONTH FROM full_date)::integer AS month,
    to_char(full_date, 'Month') AS month_name,
    EXTRACT(WEEK FROM full_date)::integer AS week,
    EXTRACT(DOY FROM full_date)::integer AS day_of_year,
    EXTRACT(DAY FROM full_date)::integer AS day_of_month,
    EXTRACT(DOW FROM full_date)::integer AS day_of_week,
    to_char(full_date, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM full_date) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    FALSE AS is_holiday
FROM date_series
