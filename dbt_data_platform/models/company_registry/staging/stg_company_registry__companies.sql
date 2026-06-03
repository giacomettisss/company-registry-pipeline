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
        {{ standardize_code('company_root_cnpj', 8) }} as company_root_cnpj,
        {{ clean_text('legal_name') }} as legal_name,
        {{ standardize_code('legal_nature_code', 4) }} as legal_nature_code,
        {{ standardize_code('responsible_qualification_code', 2) }} as responsible_qualification_code,
        try_cast(replace({{ clean_text('share_capital') }}, ',', '.') as decimal(18, 2)) as share_capital,
        {{ standardize_code('company_size_code', 2) }} as company_size_code,
        {{ clean_text('responsible_federative_entity') }} as responsible_federative_entity
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
