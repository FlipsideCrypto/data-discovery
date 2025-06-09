
The file `catalog.json` contains information from your data-warehouse about the tables and views produced and defined by the resources in your project. Today, dbt uses this file to populate metadata, such as column types and table statistics, in the docs site.

### Top-level keys

- [`metadata`](https://docs.getdbt.com/reference/artifacts/dbt-artifacts#common-metadata)
- `nodes`: Dictionary containing information about database objects corresponding to dbt models, seeds, and snapshots.
- `sources`: Dictionary containing information about database objects corresponding to dbt sources.
- `errors`: Errors received while running metadata queries during `dbt docs generate`.

### Resource details

Within `sources` and `nodes`, each dictionary key is a resource `unique_id`. Each nested resource contains:
- `unique_id`: `<resource_type>.<package>.<resource_name>`, same as dictionary key, maps to `nodes` and `sources` in the `manifest.json`
- `metadata`
    - `type`: table, view, etc.
    - `database`
    - `schema`
    - `name`
    - `comment`
    - `owner`
- `columns` (array)
    - `name`
    - `type`: data type
    - `comment`
    - `index`: ordinal
- `stats`: differs by database and relation type

Fetched from the [dbt docs](https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/reference/artifacts/catalog-json.md) on 2025-06-09.
