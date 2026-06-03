with company_profile as (
    select
        company_root_cnpj,
        legal_name,
        legal_nature_code,
        responsible_qualification_code,
        share_capital,
        company_size_code,
        responsible_federative_entity,
        simples_option,
        is_simples,
        simples_option_date,
        simples_exclusion_date,
        mei_option,
        is_mei,
        mei_option_date,
        mei_exclusion_date
    from {{ ref('int_company_registry__company_profile') }}
),

establishment_activity as (
    select
        full_cnpj,
        company_root_cnpj,
        branch_order,
        branch_type_code,
        is_headquarters,
        is_branch,
        trade_name,
        registration_status_code,
        is_active,
        registration_status_date,
        activity_start_date,
        primary_cnae_code,
        state,
        municipality_code
    from {{ ref('int_company_registry__establishment_activity') }}
),

partner_metrics as (
    select
        company_root_cnpj,
        partner_count,
        legal_entity_partner_count,
        individual_partner_count,
        foreign_partner_count,
        first_partnership_start_date,
        latest_partnership_start_date
    from {{ ref('int_company_registry__partner_metrics') }}
)

select
    establishment_activity.full_cnpj,
    establishment_activity.company_root_cnpj,
    company_profile.legal_name,
    company_profile.legal_nature_code,
    company_profile.responsible_qualification_code,
    company_profile.share_capital,
    company_profile.company_size_code,
    company_profile.responsible_federative_entity,
    company_profile.simples_option,
    company_profile.is_simples,
    company_profile.simples_option_date,
    company_profile.simples_exclusion_date,
    company_profile.mei_option,
    company_profile.is_mei,
    company_profile.mei_option_date,
    company_profile.mei_exclusion_date,
    coalesce(partner_metrics.partner_count, 0) as partner_count,
    coalesce(partner_metrics.legal_entity_partner_count, 0) as legal_entity_partner_count,
    coalesce(partner_metrics.individual_partner_count, 0) as individual_partner_count,
    coalesce(partner_metrics.foreign_partner_count, 0) as foreign_partner_count,
    partner_metrics.first_partnership_start_date,
    partner_metrics.latest_partnership_start_date,
    establishment_activity.branch_order,
    establishment_activity.branch_type_code,
    establishment_activity.is_headquarters,
    establishment_activity.is_branch,
    establishment_activity.trade_name,
    establishment_activity.registration_status_code,
    establishment_activity.is_active,
    establishment_activity.registration_status_date,
    establishment_activity.activity_start_date,
    establishment_activity.primary_cnae_code,
    establishment_activity.state,
    establishment_activity.municipality_code
from establishment_activity
left join company_profile
    on establishment_activity.company_root_cnpj = company_profile.company_root_cnpj
left join partner_metrics
    on establishment_activity.company_root_cnpj = partner_metrics.company_root_cnpj
where establishment_activity.is_active
