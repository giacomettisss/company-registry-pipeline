# Contributing

This project is an extensible data pipeline platform built with Prefect, dbt Core, and DuckDB for local execution. Contributions should keep the platform easier to use for ETL developers and easier to develop, extend, and operate for platform engineers.

## Core Principles

- Keep project-authored artifacts in English.
- Prefer clear, modular code over scattered procedural logic.
- Use focused classes and contracts when behavior is expected to vary.
- Keep Prefect flows focused on orchestration.
- Keep extraction and loading behavior in reusable orchestration components.
- Keep transformations, tests, snapshots, and marts in dbt.
- Avoid central registries that must be edited for every new pipeline.
- Prefer convention-based extension points when they are clear and safe.
- Keep abstractions practical: enough structure to scale, not a framework for its own sake.

## Local Setup

Create and activate a virtual environment:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements-dev.txt
```

Run the full local pipeline:

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

Run a single source for a faster ingestion loop:

```cmd
python -m orchestration.cli run company_registry --source cnaes
```

Source-specific runs are intended for ingestion development. Full pipeline runs orchestrate ingestion, `dbt run`, `dbt snapshot`, and `dbt test`.

## Commit Style

Use Conventional Commits:

```text
feat: add source-level ingestion logging
fix: normalize source load strategy names
docs: add platform onboarding guide
test: cover dbt command task
chore: update dependency manifest
```

Keep commits focused by responsibility. A good commit should be easy to describe in one sentence.

## Development Workflow

Before changing code, identify whether the work belongs to:

- pipeline configuration in `configs/pipelines/`;
- platform configuration in `configs/platforms/`;
- reusable contracts or implementations in `orchestration/core/`;
- reusable Prefect tasks in `orchestration/tasks/`;
- domain flow composition in `pipelines/<pipeline_name>/`;
- dbt models, tests, snapshots, or macros in `dbt_data_platform/`;
- documentation in `docs/`.

Prefer extending the existing pattern instead of introducing a parallel one.

## Adding A New Source

For a new source in an existing pipeline:

1. Add the source declaration to `configs/pipelines/<pipeline_name>.yml`.
2. Reuse an existing extractor key when possible.
3. Run the source with `--source`.
4. Inspect the raw table.
5. Add or update the dbt staging model.
6. Add focused dbt tests.
7. Update intermediate or mart models only when the source adds business value.

The usual change should be configuration plus dbt models, not duplicated orchestration logic.

## Adding A New Extractor

Create a new implementation of `BaseExtractor` when a new source access pattern is needed.

Good examples:

- `HttpCsvExtractor`
- `ApiJsonExtractor`
- `S3CsvExtractor`

Then register the extractor in `ExtractorFactory` with a clear configuration key.

The extractor should return `ExtractionResult` and should not write directly to the warehouse. Loading belongs to loader classes.

## Adding A New Pipeline

A new pipeline should follow the existing convention:

```text
configs/pipelines/<pipeline_name>.yml
pipelines/<pipeline_name>/flow.py::run_flow
dbt_data_platform/models/<pipeline_name>/
docs/<pipeline_name>/                  # optional for domain-specific decisions
```

The shared CLI should not need pipeline-specific edits. A new pipeline module should expose:

```python
def run_flow(
    pipeline_config_path: str,
    platform_config_path: str = "configs/platforms/local.yml",
    source_name: str | None = None,
):
    ...
```

## dbt Guidelines

Use the layered model structure:

```text
raw -> staging -> intermediate -> marts -> snapshots
```

- Staging models should standardize source-shaped data.
- Intermediate models should hold reusable business transformations.
- Marts should expose dimensions, facts, and analytical tables.
- Snapshots should read stable current-state models.
- Use incremental materialization where it is practical and meaningful.
- Prefer shared macros for repeated standardization logic.

Run dbt directly when developing transformations:

```cmd
dbt run --project-dir dbt_data_platform --profiles-dir dbt_data_platform
dbt snapshot --project-dir dbt_data_platform --profiles-dir dbt_data_platform
dbt test --project-dir dbt_data_platform --profiles-dir dbt_data_platform
```

## Observability

Reusable platform logs should improve both user experience and developer experience.

- Ingestion logs belong in shared Prefect tasks, not duplicated inside every flow.
- Logs should show source name, extractor, target table, load strategy, row limit, loaded row count, and failure context.
- Do not log row payloads, credentials, tokens, or full raw data.
- dbt already provides logs and artifacts for transformations, tests, snapshots, runtime, and failures.
- Future observability improvements should standardize source freshness, row-count checks, runtime metrics, and failure summaries.

## Code Documentation

Use pragmatic Python docstrings on public contracts, classes, and functions.

Docstrings should explain:

- the role of the component in the platform;
- the contract an implementation follows;
- the reason an extension point exists;
- what a reusable function or task coordinates.

Keep docstrings concise. Clear names and cohesive functions are still the primary documentation. Docstrings should help onboarding, IDE hints, and future generated documentation with tools such as Sphinx or pdoc.

## Validation

Run Python checks before committing code changes:

```cmd
.\.venv\Scripts\python.exe -m compileall orchestration pipelines
.\.venv\Scripts\python.exe -m pytest tests
```

For dbt changes, run the relevant model selection first, then run the full suite when the change affects shared models or marts.

Full local validation:

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
.\.venv\Scripts\python.exe -m pytest tests
```

Close database clients connected to `data\warehouse\data_platform.duckdb` before running ingestion or dbt commands. DuckDB is file-based and can block writes when another process holds the database open.
