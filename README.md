# Data Pipeline Platform

Extensible data pipeline repository. Each pipeline is represented as a domain module with its own runtime configuration, orchestration code, dbt models, and documentation.

## Target Stack

- Prefect for orchestration.
- dbt Core for transformation and data quality.
- DuckDB for local execution.
- BigQuery as the target cloud design described in the documentation.

## Repository Layout

```text
.
+-- configs/pipelines/              # Pipeline-level YAML configs
+-- data/                           # Local DuckDB warehouse files ignored by Git
+-- pipelines/                      # Prefect extraction and loading code by domain
+-- dbt_data_platform/              # dbt project with domain-based model folders
+-- scripts/                        # Local helper scripts
+-- docs/                           # Architecture and FinOps documentation
```

## Pipeline Contract

Each pipeline follows this layout:

```text
configs/pipelines/<domain>.yml
pipelines/<domain>/
dbt_data_platform/models/<domain>/
docs/<domain>/
```

The pipeline name and paths are defined by the domain configuration file, not by global environment variables.

## Current Scope

The repository currently contains only the base project structure and architecture notes. Executable pipeline code, dependency manifests, pipeline configuration files, dbt sources, and dbt models should be added in dedicated implementation commits.

## Ingestion Decision

This project does not keep local `raw/` or `samples/` file folders as part of the pipeline contract. For large sources, such as 100GB files, downloading and storing a full file only to load it again into the warehouse would add unnecessary I/O, storage cost, and operational complexity.

The intended pattern is:

```text
external source or API
  -> Prefect extraction with row limits/chunking
  -> raw tables in DuckDB
  -> dbt staging models
  -> dbt intermediate and marts
```

In this design, `raw` is a warehouse layer, not a local file folder. The sample size for local execution is controlled by pipeline configuration, for example `sample_row_limit: 10000`.

## dbt Seeds

Seeds are not used in the current scope because source and reference data are loaded by pipeline extraction tasks. The project can add `seeds/` later if a domain needs small, manual, versioned CSV lookup tables.

## Execution

Execution commands will be documented when the first pipeline implementation is added.
