with source as (
    select
        cnae_code,
        cnae_description
    from {{ source('company_registry_raw', 'raw_company_registry_cnaes') }}
),

standardized as (
    select
        lpad(trim(cast(cnae_code as varchar)), 7, '0') as cnae_code,
        nullif(trim(cast(cnae_description as varchar)), '') as cnae_description
    from source
)

select
    cnae_code,
    cnae_description
from standardized
where cnae_code is not null
