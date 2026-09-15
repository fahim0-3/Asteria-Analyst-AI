# Dataframe DSL

The model emits data, never source code. Approved operations are represented by Pydantic enums and fields: dimensions, metrics with `sum|mean|median|min|max|count|nunique`, filters with eight explicit comparators, sorting, and a bounded limit. The executor checks every column against the loaded frame and maps operations to known pandas methods. Wildcards are valid only for count.

There is no `eval`, `exec`, dynamic import, shell call, arbitrary lambda from the model, filesystem primitive, or network primitive. New capabilities should be introduced as typed operators with schema, semantic validator, executor, cost bound, unit tests, and documentation together.

