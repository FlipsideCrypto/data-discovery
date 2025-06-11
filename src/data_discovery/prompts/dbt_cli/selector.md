A selector needs be used when we need to select specific nodes or are asking to do actions on specific nodes. The `_run_dbt_command` appends `-s` to the start of the `selector` for you.
A node can be a model, a test, a seed or a snapshot
- to select all models, just do not provide a selector.
- to select a particular model, use `model_name`
- to select a particular model and all the downstream ones (children), use `model_name+`
- to select a particular model and all the upstream ones (parents), use `+model_name`
- to select a particular model and all downstream and upstream ones, use `+model_name+`
- to select by tag, use `tag:staging`
- to select by directory, use `models/staging/`
- to select the union of different selectors, separate them with a space like `model1 model2`
- to select the intersection of different selectors, separate them with a comma like `model1,tag:staging`
