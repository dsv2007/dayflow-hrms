# 🚨 Incident Report: urn:li:dataset:(urn:li:dataPlatform:dbt,fct_sales,PROD)

## Root Cause Analysis
**Data Sentinel** automatically traced the lineage of `urn:li:dataset:(urn:li:dataPlatform:dbt,fct_sales,PROD)` via **DataHub** and discovered a breaking schema change in the upstream dataset `urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_transactions,PROD)`.

**Changes Detected:**
```json
{
  "timestamp": "2026-08-10T10:00:00Z",
  "changes": [
    {
      "type": "DROP_COLUMN",
      "field": "txn_amount"
    },
    {
      "type": "ADD_COLUMN",
      "field": "total_amount"
    }
  ]
}
```

## Proposed Resolution
Data Sentinel has generated the following fix to accommodate the new schema in the downstream model:

```sql
WITH raw_data AS (
    SELECT * FROM {{ source('production', 'raw_transactions') }}
)
SELECT 
    id,
    total_amount * 0.9 AS discounted_amount
FROM raw_data
```
