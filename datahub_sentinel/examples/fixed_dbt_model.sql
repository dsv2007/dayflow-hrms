WITH raw_data AS (
    SELECT * FROM {{ source('production', 'raw_transactions') }}
)
SELECT 
    id,
    total_amount * 0.9 AS discounted_amount
FROM raw_data
