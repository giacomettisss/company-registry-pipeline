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

The project should use focused, coherent modules with explicit contracts. Pipeline-specific code should describe what needs to run, while shared orchestration code should handle reusable execution concepts.

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

## Product And Engineering Experience

This project is not only a working company registry pipeline. It is a scalable pipeline platform foundation designed around two explicit experience goals:

- make pipeline usage intuitive and easier to operate for the ETL developer who needs to run, validate, and add data sources;
- make platform evolution clean for the engineer who needs to add new extractors, loaders, orchestration behavior, or future pipelines.

That separation matters because a data platform has two audiences. The pipeline user should not need to understand internal Python classes to run a source. The platform engineer should not need to copy and paste flow logic every time the business adds another dataset.

### ETL Developer Experience

The ETL developer interacts with a streamlined, stable surface area: the CLI, pipeline YAML, and dbt models.

```cmd
python -m orchestration.cli run company_registry
python -m orchestration.cli run company_registry --source cnaes
```

The CLI makes the common workflow easy:

- run a full pipeline by name;
- run a single source with `--source` for a fast development loop;
- avoid memorizing module paths, Prefect internals, or loader implementation details;
- keep the same command shape as new pipelines are added.
- read source-level ingestion logs that show the extractor, target table, load strategy, row limit, and loaded row count.

The YAML file acts as a readable contract. It says what should be ingested: source name, URI, extractor key, parsing options, target raw table, and load strategy. It does not force the pipeline user to know how HTTP downloads, ZIP parsing, CSV normalization, or DuckDB writes are implemented.

In practice, adding another source to an existing pipeline should feel like this:

```text
declare source in YAML
  -> run only that source with the CLI
  -> inspect the raw table
  -> add or adjust the dbt staging model
  -> run dbt tests
```

This is the usability side of the design. The project should be easier to operate, easier to demonstrate, and easier to onboard because the user-facing workflow is intentionally streamlined.

### Platform Engineer Experience

The platform engineer works with explicit extension points instead of scattered procedural code.

The implementation follows practical software engineering principles:

- source behavior is declared in YAML;
- extractor selection is handled by `ExtractorFactory`;
- extractors follow the `BaseExtractor` contract;
- loading is isolated in loader classes such as `DuckDBLoader`;
- reusable Prefect tasks keep domain flows thin;
- source-level logging stays centralized in the reusable ingestion task;
- dbt owns transformation, tests, snapshots, and marts.

This keeps the code aligned with single responsibility and open/closed principles:

- adding a source usually changes configuration and dbt models, not shared orchestration internals;
- adding a source format means creating a focused extractor class behind the existing contract;
- adding a warehouse later should mean adding a loader implementation behind the same load contract;
- adding a pipeline means adding a config and a flow module that follow the convention;
- shared tasks and CLI code remain stable unless there is a real reusable platform need.

The goal is clean code without overengineering: focused contracts, coherent classes, strategy-style implementations, factories only where configuration needs to select behavior, and reusable tasks where Prefect orchestration would otherwise be repeated.

## Code Documentation

The codebase uses pragmatic Python docstrings on public contracts, classes, and functions. The goal is not to document obvious implementation details, but to make extension points easier to understand for developers working on the platform.

Docstrings should explain:

- what role a class or function plays in the pipeline platform;
- which contract an implementation follows;
- what a reusable component returns or coordinates;
- why a helper exists when the behavior is not obvious from the name alone.

Docstrings should stay concise. Clear names and cohesive functions remain the primary form of code clarity, while docstrings provide enough context for onboarding, IDE hints, and future generated documentation with tools such as Sphinx or pdoc.

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

Prefect is responsible for moving data from `source` to `raw` and orchestrating the dbt commands. dbt is responsible for everything after `raw`: `staging`, `intermediate`, tests, snapshots, and `marts`.

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

The current local implementation supports `overwrite`, which keeps the first end-to-end flow easy to validate. The contract already reserves `append_only` and `upsert` as production-oriented strategies:

- `overwrite`: replaces the raw table for bounded local samples or full-refresh scenarios.
- `append_only`: appends each ingestion run with load metadata for traceability and historical replay.
- `upsert`: merges records by `unique_key` when the source exposes stable business keys and updates existing entities.

This keeps the project honest: the current behavior is explicit, and future production behavior can be added behind the same source configuration contract.

## Development Guidance

The codebase should be clear, modular, and open for extension. A few loose functions are acceptable for narrow helpers, but reusable concepts should be represented by coherent classes or contracts instead of scattered procedural code.

Good abstractions for this project are intentionally focused:

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

The repository currently includes an end-to-end local company registry pipeline:

- local platform configuration;
- company registry pipeline configuration for CNAEs, companies, establishments, partners, and Simples Nacional;
- HTTP ZIP CSV extractor;
- DuckDB raw table loader;
- shared Prefect ingestion task;
- shared Prefect dbt command task;
- domain flow composition;
- generic local CLI resolved by convention;
- local dbt DuckDB profile;
- dbt sources for raw company registry tables;
- staging models for every ingested source;
- intermediate models for company profile, establishment activity, partner metrics, and active company base;
- mart models with company, establishment, and CNAE dimensions;
- incremental active companies fact table;
- SCD Type 2 snapshot for share capital;
- reusable dbt standardization macros;
- standard dbt tests and one custom business rule test;
- focused unit tests for reusable ingestion components.

## dbt Seeds

Seeds are not used in the current scope because source and reference data are loaded by pipeline extraction tasks. The project can add `seeds/` later if a domain needs compact, manual, versioned CSV lookup tables.

## Local CLI

The project includes a straightforward local CLI entrypoint for running the current company registry flow without requiring Prefect deployments or workers. A full pipeline run orchestrates source-to-raw ingestion, `dbt run`, `dbt snapshot`, and `dbt test`.

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

Run only one source from the pipeline:

```cmd
python -m orchestration.cli run company_registry --source cnaes
```

Source-specific runs are intended for fast ingestion development and validation. They do not run the full dbt transformation suite because a partial source refresh may not represent a complete raw dataset.

The CLI is intentionally convention-based so the user can run a pipeline by name instead of memorizing module paths or editing a central registry:

```text
configs/pipelines/<pipeline_name>.yml
pipelines/<pipeline_name>/flow.py::run_flow
```

This improves usability and extensibility at the same time:

- the user gets one stable command for every pipeline;
- a new source can be tested with `--source`;
- full pipeline runs include transformation and quality validation;
- a new pipeline does not require changing shared CLI code;
- the code remains open for extension through naming conventions and standard entrypoints.

Adding a new pipeline must provide its YAML configuration and expose the standard `run_flow` function in its flow module:

```python
def run_flow(
    pipeline_config_path: str,
    platform_config_path: str = "configs/platforms/local.yml",
    source_name: str | None = None,
):
    ...
```

For a step-by-step Windows `cmd.exe` guide, see [Running the First Flow](docs/running_first_flow.md).

For the source-to-raw design, see [Ingestion Architecture](docs/ingestion_architecture.md).

For project onboarding, production design, and BigQuery FinOps strategy, see [Platform From Onboarding To Production Design](docs/platform_from_onboarding_to_production_design.md).

For adding another source to an existing pipeline, see [Adding a New Source](docs/adding_new_source.md).

For adding a dbt staging model after raw ingestion, see [Adding a Staging Model](docs/adding_staging_model.md).

## Tests

Install development dependencies and run the focused unit test suite:

```cmd
pip install -r requirements-dev.txt
python -m pytest tests
```

The full CLI run already orchestrates `dbt run`, `dbt snapshot`, and `dbt test`. You can still run dbt directly when developing or debugging transformation models:

```cmd
dbt deps --project-dir dbt_data_platform --profiles-dir dbt_data_platform
dbt run --project-dir dbt_data_platform --profiles-dir dbt_data_platform
dbt snapshot --project-dir dbt_data_platform --profiles-dir dbt_data_platform
dbt test --project-dir dbt_data_platform --profiles-dir dbt_data_platform
```

`dbt deps` is listed for direct dbt debugging even though the current project does not require external dbt packages.

## End-to-End Local Validation

Run the complete local validation from the project root:

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
python -m pytest tests
```

This validates source-to-raw ingestion, dbt transformations, the SCD Type 2 snapshot, dbt data tests, the custom business rule test, and focused Python unit tests.
