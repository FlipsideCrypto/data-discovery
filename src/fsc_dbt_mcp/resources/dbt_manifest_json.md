The dbt file `manifest.json` is produced by any command that parses a dbt project. This single file contains a full representation of your dbt project's resources (models, tests, macros, etc), including all node configurations and resource properties. Even if you're only running some models or tests, all resources will appear in the manifest (unless they are disabled) with most of their properties. (A few node properties, such as `compiled_sql`, only appear for executed nodes.)

Today, dbt uses this file to populate the [docs site](/docs/explore/build-and-view-your-docs), and to perform [state comparison](/reference/node-selection/syntax#about-node-selection). Members of the community have used this file to run checks on how many models have descriptions and tests.

### Top-level keys

- [`metadata`](https://docs.getdbt.com/reference/artifacts/dbt-artifacts#common-metadata)
- `nodes`: Dictionary of all analyses, models, seeds, snapshots, and tests.
- `sources`: Dictionary of sources.
- `metrics`: Dictionary of metrics.
- `exposures`: Dictionary of exposures.
- `groups`: Dictionary of groups. (**Note:** Added in v1.5)
- `macros`: Dictionary of macros.
- `docs`: Dictionary of `docs` blocks.
- `parent_map`: Dictionary that contains the first-order parents of each resource.
- `child_map`: Dictionary that contains the first-order children of each resource.
- `group_map`: Dictionary that maps group names to their resource nodes.
- `selectors`: Expanded dictionary representation of [YAML `selectors`](/reference/node-selection/yaml-selectors).
- `disabled`: Array of resources with `enabled: false`.

### Resource details

All resources nested within `nodes`, `sources`, `metrics`, `exposures`, `macros`, and `docs` have the following base properties:

- `name`: Resource name.
- `unique_id`: `<resource_type>.<package>.<resource_name>`, same as dictionary key
- `package_name`: Name of package that defines this resource.
- `root_path`: Absolute file path of this resource's package. (**Note:** This was removed for most node types in dbt Core v1.4 / manifest v8 to reduce duplicative information across nodes, but it is still present for seeds.)
- `path`: Relative file path of this resource's definition within its "resource path" (`model-paths`, `seed-paths`, etc.).
- `original_file_path`: Relative file path of this resource's definition, including its resource path.

Each has several additional properties related to its resource type.

### dbt JSON Schema
You can refer to [dbt JSON Schema](https://schemas.getdbt.com/) for info on describing and consuming dbt generated artifacts. 

**Note**: The `manifest.json` version number is related to (but not _equal_ to) your dbt version, so you _must_ use the correct `manifest.json` version for your dbt version. To find the correct `manifest.json` version, select the dbt version on the top navigation (such as `v1.5`). 

Fetched from the [dbt docs](https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/reference/artifacts/manifest-json.md) on 2025-06-09.
