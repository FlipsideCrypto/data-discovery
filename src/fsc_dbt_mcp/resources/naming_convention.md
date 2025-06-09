Flipside dbt models use the naming convention `<schema>__<model>.sql` and runs a macro to split `.sql` filenames on a double-underscore to set the model's `schema` and `object name`.

For example:
- The file `core__fact_blocks.sql` refers to a dbt model `core__fact_blocks` which is deployed in the `core` schema and refers to a database object named `fact_blocks` (this may be a table or a view, depending on materialization).

Use this pattern to interpret database object names and provide schema context when returning model details.
