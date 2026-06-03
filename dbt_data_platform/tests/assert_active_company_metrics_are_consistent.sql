with active_companies as (
    select
        company_root_cnpj,
        active_company_count,
        active_establishment_count,
        active_headquarters_count,
        active_branch_count,
        share_capital_amount,
        partner_count,
        legal_entity_partner_count,
        individual_partner_count,
        foreign_partner_count
    from {{ ref('fct_active_companies') }}
)

select *
from active_companies
where active_company_count <> 1
    or active_establishment_count < 1
    or active_establishment_count <> active_headquarters_count + active_branch_count
    or active_headquarters_count > active_establishment_count
    or active_branch_count > active_establishment_count
    or share_capital_amount < 0
    or partner_count <> legal_entity_partner_count + individual_partner_count + foreign_partner_count
