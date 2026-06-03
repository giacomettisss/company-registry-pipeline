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
+-- configs/platforms/              # Environment-specific platform runtime configs
+-- configs/pipelines/              # Pipeline-level YAML configs
+-- data/                           # Local DuckDB warehouse files ignored by Git
+-- orchestration/                  # Shared CLI, reusable tasks, contracts, and implementations
+-- pipelines/                      # Domain flow composition
+-- dbt_data_platform/              # dbt project with domain-based model folders
+-- scripts/                        # Local helper scripts
+-- docs/                           # Architecture and FinOps documentation
```

## Pipeline Contract

Each pipeline follows this layout:

```text
configs/platforms/local.yml
configs/pipelines/<domain>.yml
pipelines/<domain>/
dbt_data_platform/models/<domain>/
docs/<domain>/
```

Shared platform settings are defined in environment-specific files under `configs/platforms/`. Pipeline-specific ingestion declarations live in `configs/pipelines/<domain>.yml`.

## Architecture

The project should use small, coherent modules with explicit contracts. Pipeline-specific code should describe what needs to run, while shared orchestration code should handle reusable execution concepts.

Preferred patterns:

- Use contract classes or abstract base classes when multiple implementations are expected.
- Use strategy-style implementations for interchangeable behaviors, such as extractors for HTTP CSV, HTTP ZIP CSV, APIs, cloud storage, or future source types.
- Use factories only where they simplify selecting an implementation from configuration.
- Use dependency injection lightly when it keeps components testable and decoupled.
- Keep Prefect flows focused on orchestration, not extraction or loading internals.
- Keep dbt responsible for transformation, tests, snapshots, and marts after raw data is available in the warehouse.

The intended shape is:

```text
configs/pipelines/<domain>.yml
  -> describes the pipeline

configs/platforms/<environment>.yml
  -> describes where the pipeline runs

orchestration/core/
  -> reusable contracts and implementations

orchestration/tasks/
  -> reusable Prefect tasks

orchestration/cli.py
  -> generic local CLI resolved by convention

pipelines/<domain>/
  -> domain flow composition

dbt_data_platform/
  -> transformation and quality layer
```

## Data Layers

The pipeline follows a clear layered flow:

```text
source -> raw -> staging -> intermediate -> marts
```

- `source`: external systems, files, APIs, or public datasets. This layer is outside our warehouse and is only described by pipeline configuration.
- `raw`: the first warehouse layer. Data is loaded with minimal changes so we keep a close representation of what arrived from the source.
- `staging`: dbt models that clean names, cast types, normalize nulls, and expose one reliable model per raw source.
- `intermediate`: reusable business transformations that combine or enrich staging models before final consumption.
- `marts`: final analytical models, such as dimensions and fact tables, designed for reporting, metrics, and downstream users.

Prefect is responsible for moving data from `source` to `raw`. dbt is responsible for everything after `raw`: `staging`, `intermediate`, tests, snapshots, and `marts`.

## Snapshot Strategy

Snapshots should read from a current-state model with a stable grain, not directly from an append-only raw history. The current SCD Type 2 snapshot reads `int_company_registry__company_profile`, which has one row per `company_root_cnpj` and tracks changes in `share_capital`.

In a production raw append-only design, staging should remain close to the raw source while standardizing names, types, and nulls. If staging starts exposing multiple versions per business key, a current-state intermediate model should deduplicate by business key and load metadata before snapshots or marts consume it.

## Load Strategy Contract

Each source declares how it should be loaded into the raw warehouse layer:

```yaml
load:
  target_table: raw_company_registry_cnaes
  strategy: overwrite
  unique_key: []
  metadata_columns:
    loaded_at: _loaded_at
    source_reference_date: _source_reference_date
    pipeline_run_id: _pipeline_run_id
```

The current local implementation supports `overwrite`, which keeps the first end-to-end flow simple. The contract already reserves `append_only` and `upsert` as production-oriented strategies:

- `overwrite`: replaces the raw table for bounded local samples or full-refresh scenarios.
- `append_only`: appends each ingestion run with load metadata for traceability and historical replay.
- `upsert`: merges records by `unique_key` when the source exposes stable business keys and updates existing entities.

This keeps the project honest: the current behavior is explicit, and future production behavior can be added behind the same source configuration contract.

## Development Guidance

The codebase should be simple, modular, and open for extension. A few loose functions are acceptable for small helpers, but reusable concepts should be represented by coherent classes or contracts instead of scattered procedural code.

Good abstractions for this project are intentionally small:

- one base contract;
- a few interchangeable implementations;
- a factory when configuration needs to choose the implementation;
- clear module boundaries;
- no framework-sized abstraction layer.

The goal is clean, extensible code that can support more pipelines over time without turning the challenge into overengineering.

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

## Current Scope

The repository currently includes a minimal reusable ingestion path validated with the company registry CNAE source:

- local platform config;
- company registry pipeline config with one CNAE source;
- HTTP ZIP CSV extractor;
- DuckDB raw table loader;
- shared Prefect ingestion task;
- domain flow composition;
- generic local CLI resolved by convention;
- local dbt DuckDB profile;
- dbt source declaration for the raw CNAE table;
- first CNAE staging model with basic dbt tests;
- minimal unit tests for reusable ingestion components.

Additional macros and full dbt test coverage will be added in dedicated implementation commits.

## dbt Seeds

Seeds are not used in the current scope because source and reference data are loaded by pipeline extraction tasks. The project can add `seeds/` later if a domain needs small, manual, versioned CSV lookup tables.

## Local CLI

The project includes a simple local CLI entrypoint for running the current company registry flow without requiring Prefect deployments or workers.

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

Run only one source from the pipeline:

```cmd
python -m orchestration.cli run company_registry --source cnaes
```

The CLI resolves pipelines by convention:

```text
configs/pipelines/<pipeline_name>.yml
pipelines/<pipeline_name>/flow.py::run_flow
```

Adding a new pipeline should not require editing the CLI. The new pipeline must provide its YAML configuration and expose the standard `run_flow` function in its flow module:

```python
def run_flow(
    pipeline_config_path: str,
    platform_config_path: str = "configs/platforms/local.yml",
    source_name: str | None = None,
):
    ...
```

For a step-by-step Windows `cmd.exe` guide, see [Running the First Flow](docs/running_first_flow.md).

For adding another source to an existing pipeline, see [Adding a New Source](docs/adding_new_source.md).

For adding a dbt staging model after raw ingestion, see [Adding a Staging Model](docs/adding_staging_model.md).

## Tests

Install development dependencies and run the focused unit test suite:

```cmd
pip install -r requirements-dev.txt
pytest tests
```

Run the first dbt staging model and its tests:

```cmd
dbt run --project-dir dbt_data_platform --profiles-dir dbt_data_platform --select stg_company_registry__cnaes
dbt test --project-dir dbt_data_platform --profiles-dir dbt_data_platform --select stg_company_registry__cnaes
```
