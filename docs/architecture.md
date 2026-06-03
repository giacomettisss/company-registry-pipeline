# Architecture

This repository is organized as an extensible local data platform for independent data pipelines.

Each pipeline is a domain module that follows the same contract:

- `configs/platforms/<environment>.yml` for shared runtime configuration by environment.
- `configs/pipelines/<domain>.yml` for runtime configuration.
- `orchestration/core/` for reusable contracts, extractors, loaders, and shared implementation details.
- `orchestration/tasks/` for reusable Prefect tasks.
- `orchestration/cli.py` for the generic local CLI.
- `pipelines/<domain>/` for domain flow composition.
- `dbt_data_platform/models/<domain>/` for dbt transformations.
- `docs/<domain>/` for domain-specific design decisions.

Adding a pipeline should mean adding a new domain module and config file. Shared code should not require edits for every new pipeline.

The local execution path is:

1. Prefect reads external sources or APIs using the pipeline configuration.
2. Reusable extractors read source-specific formats.
3. Reusable loaders write bounded local samples into raw DuckDB tables using the source load strategy contract.
4. Reusable Prefect tasks compose extraction and loading.
5. Domain flows orchestrate shared tasks for each pipeline.
6. dbt builds staging, intermediate, and mart models from those raw tables.
7. dbt tests validate quality and business rules.

Raw loading is declared per source:

```yaml
load:
  target_table: raw_<domain>_<source>
  strategy: overwrite
  unique_key: []
  metadata_columns:
    loaded_at: _loaded_at
    source_reference_date: _source_reference_date
    pipeline_run_id: _pipeline_run_id
```

The local implementation currently executes `overwrite`. The same contract is intended to support `append_only` and `upsert` later, without changing pipeline flow code or shared CLI behavior.

The local CLI resolves pipelines by convention:

```text
python -m orchestration.cli run <pipeline_name>
python -m orchestration.cli run <pipeline_name> --source <source_name>

configs/pipelines/<pipeline_name>.yml
pipelines/<pipeline_name>/flow.py::run_flow
```

In a cloud deployment, DuckDB is replaced by BigQuery datasets and Prefect can run on managed infrastructure or a scheduled worker.
