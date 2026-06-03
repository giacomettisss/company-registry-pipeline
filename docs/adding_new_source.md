# Adding a New Source

This guide explains how to add a new source to an existing pipeline.

In Prefect terminology, this project uses **flows** and **tasks**. A new source inside an existing domain usually does not need a new flow. The flow already reads every source declared in the pipeline YAML.

For example, adding `Simples.zip` to the `company_registry` pipeline should only require changing:

```text
configs/pipelines/company_registry.yml
```

## 1. Identify The Source Contract

Before editing the YAML, define:

- source name;
- source URI;
- extractor type;
- raw target table;
- load strategy;
- CSV parsing options;
- expected column names.

For a ZIP file containing a CSV-like file, use:

```yaml
extractor: http_zip_csv
```

## 2. Add The Source To The Pipeline YAML

Add a new item under `sources`.

Example for `Simples.zip`:

```yaml
  - name: simples
    extractor: http_zip_csv
    uri: https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/2026-05-10/Simples.zip
    load:
      target_table: raw_company_registry_simples
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
        - company_root_cnpj
        - simples_option
        - simples_option_date
        - simples_exclusion_date
        - mei_option
        - mei_option_date
        - mei_exclusion_date
```

Use `overwrite` for the current local implementation. The YAML contract already reserves `append_only` and `upsert` for production-oriented evolution.

## 3. Run The Existing Flow

Use the generic CLI from the project root:

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

To test only the new source:

```cmd
python -m orchestration.cli run company_registry --source simples
```

The CLI resolves:

```text
configs/pipelines/company_registry.yml
pipelines/company_registry/flow.py::run_flow
```

The flow then ingests every source declared in the YAML.

## 4. Validate The Raw Table

Open the DuckDB file with a database client such as DBeaver or VS Code:

```text
data/warehouse/data_platform.duckdb
```

Run:

```sql
select count(*) from raw_company_registry_simples;

select *
from raw_company_registry_simples
limit 10;
```

If a database client is not available, use the project fallback:

```cmd
.\.venv\Scripts\python.exe -m duckdb data\warehouse\data_platform.duckdb
```

## 5. When To Create A New Flow

Create a new flow only when adding a new pipeline domain, not when adding another source to an existing pipeline.

Examples:

- add `simples` to `company_registry`: edit `configs/pipelines/company_registry.yml`;
- add `transactions`: create `configs/pipelines/transactions.yml` and `pipelines/transactions/flow.py`;
- add `credit_risk`: create `configs/pipelines/credit_risk.yml` and `pipelines/credit_risk/flow.py`.

Every pipeline flow must expose the same entrypoint:

```python
def run_flow(
    pipeline_config_path: str,
    platform_config_path: str = "configs/platforms/local.yml",
    source_name: str | None = None,
):
    ...
```

This keeps the shared CLI generic and avoids editing shared orchestration code for every new pipeline.

## 6. Next Step

After the raw table is loaded, add the dbt staging model:

```text
docs/adding_staging_model.md
```
