with source as (
    select
        company_root_cnpj,
        legal_name,
        legal_nature_code,
        responsible_qualification_code,
        share_capital,
        company_size_code,
        responsible_federative_entity
    from {{ source('company_registry_raw', 'raw_company_registry_companies') }}
),

standardized as (
    select
        lpad(nullif(trim(cast(company_root_cnpj as varchar)), ''), 8, '0') as company_root_cnpj,
        nullif(trim(cast(legal_name as varchar)), '') as legal_name,
        lpad(nullif(trim(cast(legal_nature_code as varchar)), ''), 4, '0') as legal_nature_code,
        lpad(nullif(trim(cast(responsible_qualification_code as varchar)), ''), 2, '0') as responsible_qualification_code,
        try_cast(replace(nullif(trim(cast(share_capital as varchar)), ''), ',', '.') as decimal(18, 2)) as share_capital,
        lpad(nullif(trim(cast(company_size_code as varchar)), ''), 2, '0') as company_size_code,
        nullif(trim(cast(responsible_federative_entity as varchar)), '') as responsible_federative_entity
    from source
)

select
    company_root_cnpj,
    legal_name,
    legal_nature_code,
    responsible_qualification_code,
    share_capital,
    company_size_code,
    responsible_federative_entity
from standardized
where company_root_cnpj is not null
