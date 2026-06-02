# Architecture

This repository is organized as an extensible local data platform for independent data pipelines.

Each pipeline is a domain module that follows the same contract:

- `configs/pipelines/<domain>.yml` for runtime configuration.
- `pipelines/<domain>/` for Prefect extraction and loading code.
- `dbt_data_platform/models/<domain>/` for dbt transformations.
- `docs/<domain>/` for domain-specific design decisions.

Adding a pipeline should mean adding a new domain module and config file. Shared code should not require edits for every new pipeline.

The local execution path is:

1. Prefect reads external sources or APIs using the pipeline configuration.
2. Prefect loads a bounded local sample into raw DuckDB tables.
3. dbt builds staging, intermediate, and mart models from those raw tables.
4. dbt tests validate quality and business rules.

In a cloud deployment, DuckDB is replaced by BigQuery datasets and Prefect can run on managed infrastructure or a scheduled worker.
