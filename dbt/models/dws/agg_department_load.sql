-- ============================================================
-- DWS：科室/机构负荷汇总
-- 用于分析各科室的就诊压力
-- ============================================================

SELECT
    fe.organization_sk,
    dd.date_sk,
    count(*) AS total_encounters,
    count(DISTINCT fe.provider_sk) AS unique_providers,
    sum(total_claim_cost) AS total_claim_cost
FROM {{ ref('fact_encounter') }} fe
LEFT JOIN {{ ref('dim_date') }} dd
    ON fe.date_sk = dd.date_sk
GROUP BY fe.organization_sk, dd.date_sk
ORDER BY dd.date_sk, fe.organization_sk
