# Running the First Flow

Prefect uses the term `flow` for the orchestrated workflow. This guide uses Windows `cmd.exe` commands only.

## 1. Open the Project

```cmd
cd company-registry-pipeline
```

## 2. Activate the Virtual Environment

If the virtual environment already exists:

```cmd
.venv\Scripts\activate
```

If it does not exist yet:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the Company Registry Flow

The first command avoids noisy local telemetry messages when Prefect starts its temporary local server.

Close any database client connected to `.\data\warehouse\data_platform.duckdb` before running the flow. DuckDB uses a local file and can block writes when another process keeps the database open.

```cmd
set PREFECT_SERVER_ANALYTICS_ENABLED=false
python -m orchestration.cli run company_registry
```

To run only one source from the pipeline:

```cmd
python -m orchestration.cli run company_registry --source cnaes
```

The CLI resolves `company_registry` by convention using `configs\pipelines\company_registry.yml` and `pipelines\company_registry\flow.py::run_flow`.

Expected ending:

```text
Finished in state Completed()
```

This command is the local development entrypoint. In a production-style Prefect setup, the flow would be registered as a deployment and executed by a worker from a work pool. Local deployment and worker instructions are tracked as an optional enhancement after the end-to-end pipeline is complete.

## 4. Open the DuckDB Database

The Python package `duckdb` is enough for the pipeline to write the database, but it does not necessarily install a `duckdb` command in Windows `cmd.exe`.

The database file is created at:

```text
.\data\warehouse\data_platform.duckdb
```

Recommended options to inspect it:

- Database client: use DBeaver, VS Code, or another database connector with DuckDB support. Connect to `.\data\warehouse\data_platform.duckdb`.
- DuckDB CLI fallback: install the standalone DuckDB CLI and open the file with `duckdb data\warehouse\data_platform.duckdb`.
- Python fallback: use the inline Python commands below only when a database UI and DuckDB CLI are not available.

In a database client or DuckDB CLI, run:

```sql
show tables;
select count(1) from raw_company_registry_cnaes;
select cnae_code, cnae_description
from raw_company_registry_cnaes
limit 5;
```

Python fallback validation:

```cmd
python -c "import duckdb; con=duckdb.connect('data/warehouse/data_platform.duckdb'); print(con.execute('select count(1) from raw_company_registry_cnaes').fetchone()[0])"
```

Expected output:

```text
1359
```

Python fallback row preview:

```cmd
python -c "import duckdb; con=duckdb.connect('data/warehouse/data_platform.duckdb'); print(con.execute('select cnae_code, cnae_description from raw_company_registry_cnaes limit 5').fetchall())"
```
