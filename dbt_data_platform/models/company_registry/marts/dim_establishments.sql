with establishment_activity as (
    select
        full_cnpj,
        company_root_cnpj,
        branch_order,
        check_digits,
        branch_type_code,
        is_headquarters,
        is_branch,
        trade_name,
        registration_status_code,
        is_active,
        registration_status_date,
        registration_status_reason_code,
        foreign_city_name,
        country_code,
        activity_start_date,
        primary_cnae_code,
        secondary_cnae_codes,
        street_type,
        street_name,
        address_number,
        address_complement,
        district,
        postal_code,
        state,
        municipality_code,
        area_code_1,
        phone_1,
        area_code_2,
        phone_2,
        fax_area_code,
        fax_number,
        email,
        special_status,
        special_status_date
    from {{ ref('int_company_registry__establishment_activity') }}
),

cnaes as (
    select
        cnae_code,
        cnae_description
    from {{ ref('dim_cnaes') }}
)

select
    establishment_activity.full_cnpj,
    establishment_activity.company_root_cnpj,
    establishment_activity.branch_order,
    establishment_activity.check_digits,
    establishment_activity.branch_type_code,
    case establishment_activity.branch_type_code
        when '1' then 'headquarters'
        when '2' then 'branch'
        else 'unknown'
    end as branch_type_label,
    establishment_activity.is_headquarters,
    establishment_activity.is_branch,
    establishment_activity.trade_name,
    establishment_activity.registration_status_code,
    case establishment_activity.registration_status_code
        when '01' then 'null'
        when '02' then 'active'
        when '03' then 'suspended'
        when '04' then 'unsuitable'
        when '08' then 'closed'
        else 'unknown'
    end as registration_status_label,
    establishment_activity.is_active,
    establishment_activity.registration_status_date,
    establishment_activity.registration_status_reason_code,
    establishment_activity.foreign_city_name,
    establishment_activity.country_code,
    establishment_activity.activity_start_date,
    establishment_activity.primary_cnae_code,
    cnaes.cnae_description as primary_cnae_description,
    establishment_activity.secondary_cnae_codes,
    establishment_activity.street_type,
    establishment_activity.street_name,
    establishment_activity.address_number,
    establishment_activity.address_complement,
    establishment_activity.district,
    establishment_activity.postal_code,
    establishment_activity.state,
    establishment_activity.municipality_code,
    establishment_activity.area_code_1,
    establishment_activity.phone_1,
    establishment_activity.area_code_2,
    establishment_activity.phone_2,
    case
        when establishment_activity.phone_1 is not null
            or establishment_activity.phone_2 is not null
            then true
        else false
    end as has_phone,
    establishment_activity.fax_area_code,
    establishment_activity.fax_number,
    establishment_activity.email,
    case when establishment_activity.email is not null then true else false end as has_email,
    establishment_activity.special_status,
    establishment_activity.special_status_date
from establishment_activity
left join cnaes
    on establishment_activity.primary_cnae_code = cnaes.cnae_code
