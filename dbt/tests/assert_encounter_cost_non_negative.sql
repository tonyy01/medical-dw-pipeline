-- 断言：就诊费用不应为负数
SELECT
    encounter_id,
    total_claim_cost
FROM {{ ref('fact_encounter') }}
WHERE total_claim_cost < 0
