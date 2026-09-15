# Profiling

Profiles include shape, duplicates, inferred dtype, null count/percentage, distinct count, samples, ID/constant/high-cardinality flags, bounded categorical frequencies, numeric summaries, IQR outlier counts, correlations for manageable numeric schemas, and warnings. Values are converted to JSON-safe primitives. Inference is explicitly advisory; persisted user overrides do not rewrite original data. Production profiling should add encoding detection, sampling for very large files, semantic type inference, drift comparisons, and background execution.

