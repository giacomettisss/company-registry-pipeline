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
        {{ standardize_code('company_root_cnpj', 8) }} as company_root_cnpj,
        {{ clean_text('simples_option') }} as simples_option,
        {{ parse_yyyymmdd_date('simples_option_date') }} as simples_option_date,
        {{ parse_yyyymmdd_date('simples_exclusion_date') }} as simples_exclusion_date,
        {{ clean_text('mei_option') }} as mei_option,
        {{ parse_yyyymmdd_date('mei_option_date') }} as mei_option_date,
        {{ parse_yyyymmdd_date('mei_exclusion_date') }} as mei_exclusion_date
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
