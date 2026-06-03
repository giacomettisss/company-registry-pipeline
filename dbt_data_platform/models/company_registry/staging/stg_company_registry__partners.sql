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
        {{ standardize_code('company_root_cnpj', 8) }} as company_root_cnpj,
        {{ clean_text('partner_identifier_code') }} as partner_identifier_code,
        {{ clean_text('partner_name') }} as partner_name,
        {{ clean_text('partner_document') }} as partner_document,
        {{ standardize_code('partner_qualification_code', 2) }} as partner_qualification_code,
        {{ parse_yyyymmdd_date('partnership_start_date') }} as partnership_start_date,
        {{ standardize_code('country_code', 3) }} as country_code,
        {{ clean_text('legal_representative_document') }} as legal_representative_document,
        {{ clean_text('legal_representative_name') }} as legal_representative_name,
        {{ standardize_code('legal_representative_qualification_code', 2) }} as legal_representative_qualification_code,
        {{ clean_text('partner_age_range_code') }} as partner_age_range_code
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
