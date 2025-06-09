Execute an inline SQL query against the data warehouse and return a sample of results. Useful for quickly testing queries or exploring data.

# Key dbt_show Tool Information

## 1. Use the `limit` parameter instead of LIMIT in SQL
- **Don't do this:** `SELECT * FROM table LIMIT 5` 
- **Do this:** Use the `limit` parameter: `limit: 5` with `SELECT * FROM table`
- **Reason:** Including LIMIT in the SQL query causes a compilation error ("syntax error line 3 at position 2 unexpected 'limit'")
- The tool has a built-in default of 5 and a max of 10.

## 2. Use direct table references instead of dbt ref() syntax
- **Don't do this:** `SELECT * FROM {{ ref('core__fact_blocks') }}`
- **Do this:** `SELECT * FROM BITCOIN_DEV.core.fact_blocks`
- **Reason:** The `{{ ref() }}` Jinja syntax isn't compiled properly in `dbt show` and causes SQL compilation errors

## Example Usage:
```
{
  `limit`: 5,
  `sql_query`: `SELECT block_number, block_timestamp, block_hash, tx_count FROM BITCOIN_DEV.core.fact_blocks ORDER BY block_number DESC`
}
```

This approach successfully executes queries against the data warehouse and returns formatted JSON results that can be displayed in a readable table format.
