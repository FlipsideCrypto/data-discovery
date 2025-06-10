get_model_details provides structured metadata (Type, Description, Comment) about a specific dbt model, returning the column documentation PLUS type information, model structure, dependencies, and compiled SQL.  

IMPORTANT: Use uniqueId when available.  
 - Using uniqueId guarantees the correct model is retrieved  
 - Using only model_name may return incorrect results or fail entirely  
 - If you obtained models via get_models(), you should always use the uniqueId from those results  

`uniqueId`: The unique identifier of the model (format: "model.project_name.model_name"). STRONGLY RECOMMENDED when available.  
`model_name`: The name of the dbt model. Only use this when uniqueId is unavailable. See `resource:naming_conventions` for how to interpret dbt model file names.  

 1. PREFERRED METHOD - Using uniqueId (always use this when available): get_model_details(uniqueId="model.my_project.customer_orders")
 2. FALLBACK METHOD - Using only model_name (only when uniqueId is unknown): get_model_details(model_name="customer_orders")
