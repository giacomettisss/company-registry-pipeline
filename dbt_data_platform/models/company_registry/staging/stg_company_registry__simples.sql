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