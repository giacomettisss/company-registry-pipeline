# Adding a Staging Model

This guide explains how to add a dbt staging model after a source has already been loaded into a raw warehouse table.

For example, after ingesting `Simples.zip`, the raw table should exist as:

```text
raw_company_registry_simples
```

The next step is to expose a standardized staging model:

```text
stg_company_registry__simples
```

## 1. Declare The Raw Table As A dbt Source

Edit:

```text
dbt_data_platform/models/company_registry/sources.yml
```

Add the raw table under `company_registry_raw`:

```yaml
      - name: raw_company_registry_simples
        description: Raw Simples Nacional records from the Receita Federal public company registry dataset.
        columns:
          - name: company_root_cnpj
            description: Company root CNPJ.
          - name: simples_option
            description: Indicates whether the company has opted into Simples Nacional.
          - name: simples_option_date
            description: Simples Nacional option date in the raw source.
          - name: simples_exclusion_date
            description: Simples Nacional exclusion date in the raw source.
          - name: mei_option
            description: Indicates whether the company has opted into MEI.
          - name: mei_option_date
            description: MEI option date in the raw source.
          - name: mei_exclusion_date
            description: MEI exclusion date in the raw source.
```

## 2. Create The Staging SQL Model

Create:

```text
dbt_data_platform/models/company_registry/staging/stg_company_registry__simples.sql
```

Recommended shape:

```sql
with source as (
    select
        company_root_cnpj,
        simples_option,
        simples_option_date,
        simples_exclusion_date,
        mei_option,
        mei_option_date,
        mei_exclusion_date
    from {{ source('company_registry_raw', 'raw_company_registry_simples') }}
),

standardized as (
    select
        lpad(trim(cast(company_root_cnpj as varchar)), 8, '0') as company_root_cnpj,
        nullif(trim(cast(simples_option as varchar)), '') as simples_option,
        nullif(trim(cast(simples_option_date as varchar)), '') as simples_option_date,
        nullif(trim(cast(simples_exclusion_date as varchar)), '') as simples_exclusion_date,
        nullif(trim(cast(mei_option as varchar)), '') as mei_option,
        nullif(trim(cast(mei_option_date as varchar)), '') as mei_option_date,
        nullif(trim(cast(mei_exclusion_date as varchar)), '') as mei_exclusion_date
    from source
)

select
    company_root_cnpj,
    simples_option,
    simples_option_date,
    simples_exclusion_date,
    mei_option,
    mei_option_date,
    mei_exclusion_date
from standardized
where company_root_cnpj is not null
```

Keep staging focused on basic standardization only: names, trimming, null handling, light type normalization, and stable keys. Business rules should move to intermediate or mart models.

## 3. Document And Test The Staging Model

Edit:

```text
dbt_data_platform/models/company_registry/staging/_staging.yml
```

Add:

```yaml
  - name: stg_company_registry__simples
    description: Standardized Simples Nacional company registry records.
    columns:
      - name: company_root_cnpj
        description: Company root CNPJ standardized to 8 digits.
        tests:
          - not_null
      - name: simples_option
        description: Indicates whether the company has opted into Simples Nacional.
        tests:
          - accepted_values:
              values: ['S', 'N']
      - name: mei_option
        description: Indicates whether the company has opted into MEI.
        tests:
          - accepted_values:
              values: ['S', 'N']
```

Adjust accepted values if the raw dataset uses different codes.

## 4. Run dbt

From the project root:

```cmd
dbt run --project-dir dbt_data_platform --profiles-dir dbt_data_platform --select stg_company_registry__simples
dbt test --project-dir dbt_data_platform --profiles-dir dbt_data_platform --select stg_company_registry__simples
```

## 5. Validate In DuckDB

Use a database client or the DuckDB CLI to inspect:

```sql
select *
from stg_company_registry__simples
limit 10;
```
