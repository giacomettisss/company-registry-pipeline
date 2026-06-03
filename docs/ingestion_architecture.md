# Ingestion Architecture

This document explains how the project moves external source data into the raw warehouse layer.

The ingestion layer is intentionally small. It uses explicit contracts where the project already has interchangeable behavior, and keeps concrete implementations where only one implementation exists today.

## Flow

```text
configs/pipelines/<pipeline>.yml
  -> PipelineSourceConfig
  -> Prefect ingest_source task
  -> ExtractorFactory
  -> BaseExtractor implementation
  -> ExtractionResult
  -> DuckDBLoader
  -> raw warehouse table
```

The pipeline YAML describes what should be ingested. Shared orchestration code decides how to execute that declaration.

## Source Declaration

Each source declares:

- `name`: logical source name inside the pipeline.
- `extractor`: extractor implementation key, such as `http_zip_csv`.
- `uri`: external source location.
- `load.target_table`: raw warehouse table name.
- `load.strategy`: raw loading behavior.
- `options`: source-specific parsing options.

Example:

```yaml
- name: cnaes
  extractor: http_zip_csv
  uri: https://example.com/Cnaes.zip
  load:
    target_table: raw_company_registry_cnaes
    strategy: overwrite
    unique_key: []
    metadata_columns:
      loaded_at: _loaded_at
      source_reference_date: _source_reference_date
      pipeline_run_id: _pipeline_run_id
  options:
    delimiter: ";"
    encoding: latin1
    has_header: false
    columns:
      - cnae_code
      - cnae_description
```

This keeps source-specific details out of the Prefect flow and out of shared ingestion code.

## Extractor Contract

Extractors are interchangeable through `BaseExtractor`.

```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source: SourceConfig, row_limit: int) -> ExtractionResult:
        raise NotImplementedError
```

Every extractor receives a normalized `SourceConfig` and returns an `ExtractionResult`.

`ExtractionResult` is the handoff object between extraction and loading:

- `source_name`
- `target_table`
- `columns`
- `rows`
- `row_count`

The loader does not need to know whether the data came from a ZIP file, CSV file, API, or cloud storage. It only receives rows and a target table.

## Extractor Factory

`ExtractorFactory` maps the YAML `extractor` key to a concrete extractor class.

Current mapping:

```python
{
    "http_zip_csv": HttpZipCsvExtractor,
}
```

The factory exists because extractor selection is configuration-driven. A pipeline can add another source using the same implementation without changing the flow.

If the project needs a new source type, add a new extractor class and register it in the factory:

```text
orchestration/core/extractors/api_json_extractor.py
orchestration/core/extractors/factory.py
```

Example future mappings:

```python
{
    "http_zip_csv": HttpZipCsvExtractor,
    "http_csv": HttpCsvExtractor,
    "api_json": ApiJsonExtractor,
    "s3_csv": S3CsvExtractor,
}
```

This follows the open/closed principle pragmatically: pipeline configs can choose existing behavior, and new source types are added as new classes instead of changing every flow.

## Current Extractor

`HttpZipCsvExtractor` is responsible for one source pattern:

```text
HTTP URL
  -> ZIP file
  -> CSV-like file inside the ZIP
  -> normalized rows
```

It handles:

- HTTP download;
- ZIP file reading;
- CSV file selection inside the archive;
- delimiter and encoding options;
- optional header handling;
- row limiting for local sample execution;
- row width normalization.

It does not write to DuckDB. That is the loader responsibility.

## Loader Boundary

`DuckDBLoader` is the current concrete loader implementation.

It receives an `ExtractionResult` and writes it to DuckDB using the configured raw target table.

Current behavior:

```text
ExtractionResult
  -> validate table and column identifiers
  -> create or replace raw table
  -> insert extracted rows
```

The current local implementation supports `overwrite`. The loader validates `append_only` and `upsert` as reserved strategies, but those strategies are intentionally not implemented yet.

This keeps the contract visible without pretending the local challenge implementation is already a production ingestion engine.

## Why There Is No Loader Factory Yet

There is only one real warehouse implementation today: DuckDB.

Creating `BaseLoader` and `LoaderFactory` before a second concrete destination exists would add structure without removing current complexity. The project should add that abstraction when there is a real second loader, for example:

- `BigQueryLoader`
- `SnowflakeLoader`
- `PostgresLoader`

The expected future shape would be:

```text
orchestration/core/loaders/base.py
orchestration/core/loaders/duckdb_loader.py
orchestration/core/loaders/bigquery_loader.py
orchestration/core/loaders/factory.py
```

Until then, `DuckDBLoader` is the explicit local warehouse adapter.

## Prefect Task Boundary

The shared Prefect task `ingest_source` coordinates the reusable pieces:

1. Convert `PipelineSourceConfig` into `SourceConfig`.
2. Use `ExtractorFactory` to create the extractor.
3. Extract bounded rows from the source.
4. Create `DuckDBLoader` from the platform warehouse path.
5. Load the extraction result into the raw table.
6. Return source, table, strategy, and row count metadata.

Domain flows do not implement extraction or loading details. They select sources and call the shared ingestion task.

## Extensibility Rules

Use the smallest abstraction that protects the current design from repetition.

- Add a new source to an existing pipeline by editing `configs/pipelines/<pipeline>.yml`.
- Add a new source format by creating a new `BaseExtractor` implementation.
- Add a new warehouse destination only when there is a real second destination.
- Keep Prefect flows thin and domain-oriented.
- Keep raw loading behavior declared in source configuration.
- Keep transformation, snapshots, tests, and marts in dbt.

## Production Evolution

The local implementation is optimized for a bounded challenge run. Production evolution should focus on:

- chunked extraction instead of keeping all rows in memory;
- append-only raw loading with ingestion metadata;
- upsert loading for sources with stable unique keys;
- warehouse-specific loaders for cloud execution;
- current-state intermediate models before snapshots and marts;
- orchestration deployments and workers per environment.

