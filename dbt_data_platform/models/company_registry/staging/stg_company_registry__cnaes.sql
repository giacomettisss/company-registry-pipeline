with source as (
    select
        cnae_code,
        cnae_description
    from {{ source('company_registry_raw', 'raw_company_registry_cnaes') }}
),

standardized as (
    select
        {{ standardize_code('cnae_code', 7) }} as cnae_code,
        {{ clean_text('cnae_description') }} as cnae_description
    from source
)

select
    cnae_code,
    cnae_description
from standardized
where cnae_code is not null
