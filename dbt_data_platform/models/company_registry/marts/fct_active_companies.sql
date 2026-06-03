{{
    config(
        materialized='incremental',
        unique_key='company_root_cnpj',
        on_schema_change='sync_all_columns'
    )
}}

with active_company_base as (
    select
        full_cnpj,
        company_root_cnpj,
        legal_name,
        legal_nature_code,
        responsible_qualification_code,
        share_capital,
        company_size_code,
        responsible_federative_entity,
        is_simples,
        is_mei,
        partner_count,
        legal_entity_partner_count,
        individual_partner_count,
        foreign_partner_count,
        first_partnership_start_date,
        latest_partnership_start_date,
        branch_type_code,
        is_headquarters,
        is_branch,
        registration_status_date,
        activity_start_date,
        primary_cnae_code,
        state,
        municipality_code
    from {{ ref('int_company_registry__active_company_base') }}
),

representative_establishments as (
    select
        full_cnpj,
        company_root_cnpj,
        branch_type_code,
        primary_cnae_code,
        state,
        municipality_code,
        row_number() over (
            partition by company_root_cnpj
            order by
                case when is_headquarters then 0 else 1 end,
                full_cnpj
        ) as establishment_rank
    from active_company_base
),

company_metrics as (
    select
        company_root_cnpj,
        max(legal_name) as legal_name,
        max(legal_nature_code) as legal_nature_code,
        max(responsible_qualification_code) as responsible_qualification_code,
        max(coalesce(share_capital, 0)) as share_capital_amount,
        max(company_size_code) as company_size_code,
        max(responsible_federative_entity) as responsible_federative_entity,
        max(case when is_simples then 1 else 0 end) = 1 as is_simples,
        max(case when is_mei then 1 else 0 end) = 1 as is_mei,
        count(distinct full_cnpj) as active_establishment_count,
        count(distinct case when is_headquarters then full_cnpj end) as active_headquarters_count,
        count(distinct case when is_branch then full_cnpj end) as active_branch_count,
        max(coalesce(partner_count, 0)) as partner_count,
        max(coalesce(legal_entity_partner_count, 0)) as legal_entity_partner_count,
        max(coalesce(individual_partner_count, 0)) as individual_partner_count,
        max(coalesce(foreign_partner_count, 0)) as foreign_partner_count,
        min(first_partnership_start_date) as first_partnership_start_date,
        max(latest_partnership_start_date) as latest_partnership_start_date,
        min(activity_start_date) as first_activity_start_date,
        max(registration_status_date) as latest_registration_status_date
    from active_company_base
    group by company_root_cnpj
)

select
    company_metrics.company_root_cnpj,
    representative_establishments.full_cnpj as representative_full_cnpj,
    representative_establishments.primary_cnae_code,
    representative_establishments.state,
    representative_establishments.municipality_code,
    representative_establishments.branch_type_code as representative_branch_type_code,
    company_metrics.legal_name,
    company_metrics.legal_nature_code,
    company_metrics.responsible_qualification_code,
    company_metrics.company_size_code,
    company_metrics.responsible_federative_entity,
    company_metrics.is_simples,
    company_metrics.is_mei,
    1 as active_company_count,
    company_metrics.active_establishment_count,
    company_metrics.active_headquarters_count,
    company_metrics.active_branch_count,
    company_metrics.share_capital_amount,
    company_metrics.partner_count,
    company_metrics.legal_entity_partner_count,
    company_metrics.individual_partner_count,
    company_metrics.foreign_partner_count,
    company_metrics.first_partnership_start_date,
    company_metrics.latest_partnership_start_date,
    company_metrics.first_activity_start_date,
    company_metrics.latest_registration_status_date
from company_metrics
left join representative_establishments
    on company_metrics.company_root_cnpj = representative_establishments.company_root_cnpj
    and representative_establishments.establishment_rank = 1
