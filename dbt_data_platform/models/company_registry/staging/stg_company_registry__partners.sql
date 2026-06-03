with source as (
    select
        company_root_cnpj,
        partner_identifier_code,
        partner_name,
        partner_document,
        partner_qualification_code,
        partnership_start_date,
        country_code,
        legal_representative_document,
        legal_representative_name,
        legal_representative_qualification_code,
        partner_age_range_code
    from {{ source('company_registry_raw', 'raw_company_registry_partners') }}
),

standardized as (
    select
        lpad(nullif(trim(cast(company_root_cnpj as varchar)), ''), 8, '0') as company_root_cnpj,
        nullif(trim(cast(partner_identifier_code as varchar)), '') as partner_identifier_code,
        nullif(trim(cast(partner_name as varchar)), '') as partner_name,
        nullif(trim(cast(partner_document as varchar)), '') as partner_document,
        lpad(nullif(trim(cast(partner_qualification_code as varchar)), ''), 2, '0') as partner_qualification_code,
        try_strptime(nullif(trim(cast(partnership_start_date as varchar)), ''), '%Y%m%d')::date as partnership_start_date,
        lpad(nullif(trim(cast(country_code as varchar)), ''), 3, '0') as country_code,
        nullif(trim(cast(legal_representative_document as varchar)), '') as legal_representative_document,
        nullif(trim(cast(legal_representative_name as varchar)), '') as legal_representative_name,
        lpad(nullif(trim(cast(legal_representative_qualification_code as varchar)), ''), 2, '0') as legal_representative_qualification_code,
        nullif(trim(cast(partner_age_range_code as varchar)), '') as partner_age_range_code
    from source
)

select
    company_root_cnpj,
    partner_identifier_code,
    partner_name,
    partner_document,
    partner_qualification_code,
    partnership_start_date,
    country_code,
    legal_representative_document,
    legal_representative_name,
    legal_representative_qualification_code,
    partner_age_range_code
from standardized
where company_root_cnpj is not null
