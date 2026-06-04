# Platform From Onboarding To Production Design

Project link: https://github.com/giacomettisss/company-registry-pipeline

This document explains the implemented project and how it should evolve from the local DuckDB challenge environment into a production cloud design using BigQuery.

The goal is not to document BigQuery in isolation. The goal is to onboard a new contributor into the project, explain the local implementation, and show the production-oriented decisions for cost, performance, partitioning, clustering, and maintainability.

## 1. Project Overview

This repository implements an extensible data pipeline platform. The current domain is the Brazilian company registry pipeline, but the repository is intentionally structured so new pipelines can be added without rewriting shared orchestration code.

The local implementation uses:

- Prefect for orchestration.
- Python classes and contracts for reusable ingestion.
- DuckDB as the local warehouse.
- dbt Core for staging, intermediate models, marts, tests, macros, and snapshots.

The cloud target design uses:

- Prefect workers running in a managed environment.
- BigQuery as the analytical warehouse.
- dbt Core targeting BigQuery.
- Optional object storage only when operationally justified for retry, audit, or BigQuery load job staging.

The main product decision behind the project is experience design for both pipeline users and platform maintainers. A successful data platform should not only run data from source to mart. It should make the common path obvious for the person creating a pipeline and keep the internal architecture clean enough for engineers to evolve it safely.

### 1.1 ETL Developer Experience

The ETL developer is the person adding sources, running local validations, checking raw tables, and creating dbt models. For that user, the project keeps the operating model intuitive and easier to use:

- one generic CLI command to run any pipeline by name;
- one optional `--source` flag to run a single source during development or troubleshooting;
- one YAML file per pipeline to declare source behavior;
- dbt commands for transformation, tests, snapshots, and marts;
- a local DuckDB warehouse that can be inspected with database tooling.

This means the ETL developer does not need to know which Python class downloads a ZIP file, which loader writes to DuckDB, or how Prefect imports a flow module. The YAML answers what should run. The shared orchestration layer answers how the reusable mechanics work.

The practical development loop is intentionally short:

```text
declare or update a source in YAML
  -> run that source with the CLI
  -> inspect the raw table
  -> add or update staging
  -> run dbt models and tests
```

This is a deliberate usability choice. It reduces onboarding time, lowers the chance of copy-and-paste orchestration code, and makes the project easier to demonstrate in a technical interview or to hand over to another data engineer.

### 1.2 Platform Engineer Experience

The platform engineer is the person evolving the framework itself: adding extractor types, loader implementations, environment support, Prefect deployment patterns, or future pipeline conventions. For that user, the codebase provides explicit extension points instead of a large procedural flow.

The internal architecture follows clean code principles in a pragmatic way:

- `BaseExtractor` defines the extractor contract;
- concrete extractor classes implement one source access pattern at a time;
- `ExtractorFactory` selects the implementation from configuration;
- loader classes isolate warehouse-specific write behavior;
- reusable Prefect tasks keep domain flows focused on composition;
- dbt remains responsible for transformation, quality rules, snapshots, and marts.

This design applies single responsibility and open/closed principles without turning the challenge into a large framework. A new source format should be added by implementing a focused class. A new warehouse should be added behind a loader implementation. A new pipeline should follow the folder and entrypoint convention instead of requiring edits to shared CLI code.

The codebase also uses pragmatic Python docstrings on public contracts, classes, and functions. They are intentionally concise: they describe the role of an extension point, the contract an implementation follows, or the responsibility of a reusable component. This improves the platform engineer experience today through IDE hints and faster onboarding, and it keeps the project ready for future generated documentation with tools such as Sphinx or pdoc.

The result is a more scalable platform foundation: easy enough to deliver and validate in a short challenge, but structured enough that another engineer could continue extending it without rewriting the foundation.

The project follows this data flow:

```text
source -> raw -> staging -> intermediate -> marts
```

Responsibilities by layer:

- `source`: external public files, APIs, or partner systems.
- `raw`: first warehouse layer, preserving source-like records with ingestion metadata.
- `staging`: standardized source-shaped models with clean names, normalized types, and null handling.
- `intermediate`: reusable business transformations and current-state models.
- `marts`: final dimensions, facts, snapshots, and analytical tables.

In the local challenge, the warehouse is DuckDB. In cloud production, the same logical layers should be implemented in BigQuery datasets.

## 2. Local Onboarding

Start from the repository root:

```cmd
cd company-registry-pipeline
```

Create and activate a virtual environment:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements-dev.txt
```

Run the full local pipeline. This command runs source-to-raw ingestion and then orchestrates `dbt run`, `dbt snapshot`, and `dbt test` from the same Prefect flow:

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

Run only one source:

```cmd
python -m orchestration.cli run company_registry --source cnaes
```

Source-specific runs are for fast ingestion checks. They do not run the full dbt transformation suite because a partial source refresh may not represent a complete raw dataset.

When developing or debugging transformations directly, run dbt models:

```cmd
dbt run --project-dir dbt_data_platform --profiles-dir dbt_data_platform
```

Run the SCD Type 2 snapshot:

```cmd
dbt snapshot --project-dir dbt_data_platform --profiles-dir dbt_data_platform
```

Run dbt tests:

```cmd
dbt test --project-dir dbt_data_platform --profiles-dir dbt_data_platform
```

The local DuckDB file is created at:

```text
data/warehouse/data_platform.duckdb
```

Use DBeaver, another database client with DuckDB support, or the DuckDB CLI fallback to inspect the local warehouse. Do not open the `.duckdb` file directly as a regular text file in VS Code; VS Code only works for this use case when configured with a DuckDB-capable database extension.

## 3. Repository Structure

Important folders:

```text
configs/platforms/
configs/pipelines/
orchestration/core/
orchestration/tasks/
pipelines/
dbt_data_platform/
docs/
tests/
```

Key responsibilities:

- `configs/platforms/local.yml`: local platform configuration, including warehouse and transformation settings.
- `configs/pipelines/company_registry.yml`: source declarations for the company registry pipeline.
- `orchestration/core/`: reusable contracts, extractors, loaders, config parsing, and source selection.
- `orchestration/tasks/`: reusable Prefect tasks.
- `pipelines/company_registry/flow.py`: domain flow composition.
- `dbt_data_platform/models/company_registry/`: dbt models for the current domain.
- `dbt_data_platform/snapshots/`: SCD Type 2 snapshot definitions.
- `dbt_data_platform/macros/`: reusable dbt macros.
- `dbt_data_platform/tests/`: singular business tests.

The shared CLI resolves pipelines by convention:

```text
configs/pipelines/<pipeline_name>.yml
pipelines/<pipeline_name>/flow.py::run_flow
```

This convention is part of the user experience, not only an implementation detail. The operator runs `python -m orchestration.cli run company_registry` without knowing the internal module path, extractor class, or loader implementation. The optional `--source` flag makes partial runs easy during development, data quality investigation, and source-specific reruns.

The same convention protects the platform engineering experience. New pipelines follow a folder, YAML, and `run_flow` entrypoint contract. They do not require a central registry update or new CLI branch every time a domain is added. That keeps the shared CLI stable while the number of pipelines grows.

## 4. Ingestion Design

The source-to-raw ingestion flow is:

```text
pipeline YAML
  -> PipelineSourceConfig
  -> Prefect ingest_source task
  -> ExtractorFactory
  -> BaseExtractor implementation
  -> ExtractionResult
  -> warehouse loader
  -> raw table
```

The current extractor contract is `BaseExtractor`. The implemented extractor is `HttpZipCsvExtractor`, which handles HTTP ZIP files containing CSV-like files.

This design keeps the YAML intuitive while preserving clean internal architecture. For the ETL developer, `extractor: http_zip_csv` is a readable declaration. For the platform engineer, that key maps to a focused implementation behind `BaseExtractor` and `ExtractorFactory`. The same pattern can support future classes such as `HttpCsvExtractor`, `ApiJsonExtractor`, or `S3CsvExtractor` without changing every flow.

The current loader is `DuckDBLoader`. It supports local `overwrite` loading. The source YAML already declares a production-oriented load strategy contract:

```yaml
load:
  target_table: raw_company_registry_companies
  strategy: overwrite
  unique_key:
    - company_root_cnpj
  metadata_columns:
    loaded_at: _loaded_at
    source_reference_date: _source_reference_date
    pipeline_run_id: _pipeline_run_id
```

For production BigQuery, the loader should evolve into a concrete `BigQueryLoader` behind the same contract. The production strategies should be:

- `append_only`: append each source run to raw tables with ingestion metadata.
- `upsert`: merge by stable business keys when the source supports reliable keys.
- `overwrite`: reserved for bounded reference data or explicit full refresh scenarios.

Raw append-only is the preferred default for large production datasets because it preserves lineage and replay capability. The current local `overwrite` implementation is acceptable for a bounded technical challenge sample.

The reusable Prefect task is the bridge between usability and maintainability. It converts YAML source declarations into extractor and loader calls, so ETL developers get an intuitive declaration model and platform engineers keep ingestion behavior centralized in one reusable task. The same task also emits source-level logs for extractor selection, row limits, target tables, load strategies, loaded rows, and failures. This improves the ETL developer run experience and gives platform engineers one reusable observability point for every pipeline. For transformations, dbt already provides useful logs and artifacts for model execution, tests, snapshots, runtime, and failures. Future production evolution can add standardized platform logs around dbt orchestration, source freshness, row-count checks, runtime metrics, and failure summaries. Domain flows stay readable and new sources reuse the same task instead of copying ingestion logic or observability code.

## 5. dbt Modeling Design

The dbt project has the following layers:

```text
raw source tables
  -> staging views
  -> intermediate tables
  -> marts tables
  -> snapshots
```

Current implemented models include:

- staging models for CNAEs, companies, establishments, partners, and Simples Nacional;
- intermediate models for company profile, establishment activity, partner metrics, and active company base;
- dimensions for CNAEs, companies, and establishments;
- an incremental fact table for active company metrics;
- an SCD Type 2 snapshot tracking share capital changes;
- standardization macros for text, codes, dates, and yes/no flags;
- standard and custom dbt tests.

The production BigQuery design should keep the same logical layers, but materialization decisions should be adjusted for scale:

- staging for high-volume sources should usually be materialized as tables or incremental models, not views over very large append-only raw tables;
- intermediate current-state models should deduplicate raw history before marts and snapshots consume it;
- marts should be tables or incremental tables because they serve analytical consumers;
- snapshots should read stable current-state models rather than raw append-only history.

## 6. Cloud Target Architecture

The production cloud architecture should look like this:

```text
External Receita Federal source
  -> Prefect deployment
  -> extractor implementation
  -> BigQuery raw dataset
  -> dbt BigQuery target
  -> staging dataset
  -> intermediate dataset
  -> mart dataset
  -> BI or downstream consumers
```

Recommended BigQuery datasets:

```text
company_registry_raw
company_registry_staging
company_registry_intermediate
company_registry_marts
company_registry_snapshots
```

Recommended environments:

```text
local -> DuckDB
dev   -> BigQuery development project/datasets
prod  -> BigQuery production project/datasets
```

Environment-specific details should stay in platform configuration and dbt profiles. Pipeline-specific source declarations should remain in pipeline YAML.

## 7. BigQuery FinOps Principles

BigQuery cost and performance optimization should focus on reducing unnecessary data processing before trying to tune compute capacity.

Important principles:

- Query only necessary columns.
- Filter on partition columns whenever possible.
- Cluster large tables by commonly filtered or grouped columns.
- Avoid date-sharded tables; prefer partitioned tables.
- Materialize expensive repeated transformations.
- Aggregate before joining large tables when possible.
- Keep high-volume raw tables append-only with metadata.
- Use incremental dbt models for large marts.
- Monitor bytes processed, slot-ms, query plans, and table growth.

In BigQuery, "slots read" is not the precise term. BigQuery reads table data and uses slots as compute units to execute query stages. Better partitioning and clustering reduce bytes scanned and usually reduce slot-ms because less data reaches the execution stages.

## 8. Partitioning Strategy

Partitioning should be chosen based on common query filters and data lifecycle, not only because a table is large.

Recommended partitioning:

| Layer | Table pattern | Partitioning | Reason |
| --- | --- | --- | --- |
| Raw high-volume sources | `raw_company_registry_companies`, `raw_company_registry_establishments`, `raw_company_registry_partners`, `raw_company_registry_simples` | `source_reference_date` or `_loaded_at` | Supports append-only loads, replay by source release, and partition pruning for batch-scoped processing. |
| Raw low-volume reference data | `raw_company_registry_cnaes` | No partition or `source_reference_date` only if loaded historically | CNAE is reference data with limited volume; partition overhead may not be worth it. |
| Staging high-volume models | `stg_company_registry__companies`, `stg_company_registry__establishments`, `stg_company_registry__partners` | Same load/reference date used in raw if materialized | Keeps dbt transformations scoped to the current batch or release. |
| Current-state intermediate models | `int_company_registry__company_profile`, `int_company_registry__partner_metrics` | Usually no date partition, or partition by `source_reference_date` if versioned | Current-state models are keyed by business entity. Clustering is often more important than partitioning. |
| Fact table | `fct_active_companies` | `source_reference_date` when added to the fact | Analytical queries often compare metrics by source release or processing batch. |
| Snapshot | `snap_company_registry__share_capital` | `date(dbt_valid_from)` | Supports historical SCD queries and keeps new snapshot versions in recent partitions. |
| Dimensions | `dim_cnaes`, `dim_companies`, `dim_establishments` | No partition for current dimensions with limited volume; use `source_reference_date` only if versioned | Dimensions are usually consumed by key lookup and joins. |

For this project, the most important production addition is to carry `source_reference_date`, `_loaded_at`, and `_pipeline_run_id` through raw and selected downstream models. Those columns make partitioning, lineage, and replay possible.

Conceptual cost impact:

- If a raw table stores 24 monthly source releases and a dbt job filters one monthly partition, BigQuery can skip the other 23 partitions.
- If a table stores 1 TB per month and a query filters one month, partition pruning can reduce the eligible scan from 24 TB to about 1 TB before clustering or column projection.
- If the query also selects only 10 of 50 columns, columnar storage further reduces bytes processed.
- If the filtered partition is clustered by query predicates such as `state` and `primary_cnae_code`, BigQuery can prune storage blocks inside that partition.

These are conceptual reductions, not guaranteed fixed percentages. Actual reduction depends on data distribution, query predicates, selected columns, and clustering quality.

## 9. Clustering Strategy

Clustering should match common filters, joins, and groupings. BigQuery supports up to four clustering columns, and column order matters.

Recommended clustering:

| Model | Clustering columns | Reason |
| --- | --- | --- |
| `raw_company_registry_companies` | `company_root_cnpj`, `legal_nature_code`, `company_size_code` | Company lookup and joins start with root CNPJ; legal nature and company size are common analytical filters. |
| `raw_company_registry_establishments` | `company_root_cnpj`, `full_cnpj`, `state`, `primary_cnae_code` | Supports entity joins, establishment lookup, and activity/location analysis. |
| `raw_company_registry_partners` | `company_root_cnpj`, `partner_identifier_code` | Partner metrics aggregate by company and often segment by partner type. |
| `raw_company_registry_simples` | `company_root_cnpj`, `simples_option`, `mei_option` | Company profile enrichment joins by root CNPJ and filters by tax regime flags. |
| `dim_companies` | `company_root_cnpj`, `company_size_code`, `legal_nature_code` | Supports joins and common company segmentation. |
| `dim_establishments` | `full_cnpj`, `company_root_cnpj`, `state`, `primary_cnae_code` | Supports establishment lookup and geographic/economic filtering. |
| `dim_cnaes` | `cnae_code` | Small dimension; clustering is optional but harmless if the table grows. |
| `fct_active_companies` | `state`, `primary_cnae_code`, `company_size_code`, `company_root_cnpj` | Optimized for analytical queries like active companies by state, CNAE, size, and company drill-down. |
| `snap_company_registry__share_capital` | `company_root_cnpj`, `dbt_valid_to` | Supports current and historical lookup by company. |

The fact table uses `state` and `primary_cnae_code` first because the expected analytical queries are grouped by geography and economic activity. If production usage becomes more lookup-heavy than aggregate-heavy, `company_root_cnpj` can move earlier in the clustering order.

## 10. Example BigQuery dbt Configs

Example future dbt configuration for the active company fact:

```sql
{{
    config(
        materialized='incremental',
        unique_key='company_root_cnpj',
        partition_by={
            "field": "source_reference_date",
            "data_type": "date",
            "granularity": "day"
        },
        cluster_by=[
            "state",
            "primary_cnae_code",
            "company_size_code",
            "company_root_cnpj"
        ],
        incremental_strategy='merge'
    )
}}
```

Example future raw table configuration if raw loading is managed by dbt external staging or a BigQuery loader:

```sql
partition by source_reference_date
cluster by company_root_cnpj, state, primary_cnae_code
```

The local DuckDB implementation does not need these configs because local data volume is intentionally bounded. The model is designed so these columns and strategies can be introduced when the target warehouse is BigQuery.

## 11. Expected Query Patterns

The partitioning and clustering choices should serve real query patterns:

```sql
-- Active companies by state and CNAE
select
    state,
    primary_cnae_code,
    sum(active_company_count) as active_companies
from company_registry_marts.fct_active_companies
where source_reference_date = date '2026-05-10'
    and state = 'SP'
group by state, primary_cnae_code;
```

This query benefits from:

- partition pruning on `source_reference_date`;
- block pruning on `state` and `primary_cnae_code`;
- column projection because only a few columns are selected.

```sql
-- Company drill-down
select *
from company_registry_marts.dim_companies
where company_root_cnpj = '00000000';
```

This query benefits from clustering by `company_root_cnpj`.

```sql
-- Share capital history
select
    company_root_cnpj,
    share_capital,
    dbt_valid_from,
    dbt_valid_to
from company_registry_snapshots.snap_company_registry__share_capital
where company_root_cnpj = '00000000'
order by dbt_valid_from;
```

This query benefits from clustering by `company_root_cnpj` and from snapshot metadata.

## 12. Cost and Performance Impact

The main cost driver in BigQuery on-demand pricing is bytes processed by queries. In capacity pricing, inefficient queries still matter because they consume slot capacity and can delay other workloads.

This design reduces cost and improves performance through:

- partition pruning: scan only relevant source releases or validity windows;
- clustering block pruning: scan fewer storage blocks inside selected partitions;
- column projection: scan only referenced columns;
- staged transformations: avoid repeatedly parsing and cleaning raw strings;
- incremental marts: avoid rebuilding large facts from scratch;
- current-state intermediate models: avoid joining raw append-only history directly in every mart;
- dbt tests: catch data quality failures before expensive downstream analysis.

Conceptual example:

```text
Unoptimized query:
  scans all releases, all columns, all states, all CNAEs

Optimized query:
  scans one source_reference_date partition
  scans only selected columns
  prunes clustered blocks for state and primary_cnae_code
```

If production holds 24 source releases, partition filtering alone can reduce the eligible scan to roughly 1/24 of the raw history for release-scoped queries. Clustering and projection then reduce the actual processed bytes further. This directly lowers on-demand query cost and usually lowers slot-ms in capacity-based execution.

## 13. Monitoring and Guardrails

Recommended FinOps guardrails:

- Require partition filters on large partitioned tables where appropriate.
- Use dry runs or query estimates before expensive ad hoc queries.
- Set `maximum_bytes_billed` for exploratory queries.
- Monitor `INFORMATION_SCHEMA.JOBS` for bytes processed, slot-ms, failed jobs, and expensive users/queries.
- Monitor table and partition sizes.
- Use scheduled dbt test jobs before publishing marts.
- Separate dev and prod BigQuery projects or datasets.
- Apply dataset/table expiration policies for temporary or scratch data.
- Use labels on jobs and tables, for example `pipeline`, `domain`, `environment`, and `owner`.

Recommended operational metrics:

- ingestion row count by source and run;
- raw table bytes by partition;
- dbt model runtime;
- dbt test failures;
- BigQuery bytes processed by model;
- BigQuery slot-ms by model;
- number of invalid or late source records;
- freshness by source reference date.

## 14. Production Deployment Notes

The local CLI is enough for the challenge, but production should use Prefect deployments and workers.

Recommended production setup:

- one work pool per environment or workload class;
- deployment parameters for pipeline name, platform config, source filters, and run date;
- secrets managed outside the repository;
- dbt profile configured through environment variables or secret blocks;
- separate service accounts for ingestion and transformation;
- monitoring and alerting for failed flows and dbt tests.

The shared CLI and flow convention should remain useful locally. Production deployments should call the same flow entrypoint:

```python
run_flow(
    pipeline_config_path="configs/pipelines/company_registry.yml",
    platform_config_path="configs/platforms/prod.yml",
)
```

## 15. How To Add New Work

Add a new source to an existing pipeline:

1. Edit `configs/pipelines/company_registry.yml`.
2. Add the source declaration.
3. Run only that source locally with `--source`.
4. Validate the raw table.
5. Add a staging model.
6. Add tests.
7. Update intermediate or mart models only if the source adds business value.

Add a new source format:

1. Create a new `BaseExtractor` implementation.
2. Register it in `ExtractorFactory`.
3. Add focused unit tests.
4. Use the new extractor key in pipeline YAML.

Add a new pipeline:

1. Create `configs/pipelines/<pipeline_name>.yml`.
2. Create `pipelines/<pipeline_name>/flow.py`.
3. Expose `run_flow`.
4. Create `dbt_data_platform/models/<pipeline_name>/`.
5. Keep shared orchestration code unchanged unless there is a true reusable need.

## 16. Open Production Gaps

The local implementation intentionally keeps the challenge scope bounded. Before production, the project should add:

- `BigQueryLoader` and a loader contract once BigQuery is the real second destination;
- chunked extraction so large files are not kept fully in memory;
- append-only raw loading with metadata;
- upsert support for sources with reliable keys;
- optional ReceitaWS API enrichment through an `ApiJsonExtractor` when CNPJ-level API attributes become required;
- source freshness checks;
- dbt BigQuery profiles for dev and prod;
- Prefect deployments and workers;
- CI jobs for Python tests and dbt validation;
- full E2E run documentation.

## 17. References

Official Google Cloud references used for this design:

- BigQuery partitioned tables: https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery clustered tables: https://cloud.google.com/bigquery/docs/clustered-tables
- BigQuery slots: https://cloud.google.com/bigquery/docs/slots
- BigQuery query performance best practices: https://cloud.google.com/bigquery/docs/best-practices-performance-compute
- BigQuery pricing: https://cloud.google.com/bigquery/pricing
