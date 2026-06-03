with partners as (
    select
        company_root_cnpj,
        partner_identifier_code,
        partnership_start_date
    from {{ ref('stg_company_registry__partners') }}
)

select
    company_root_cnpj,
    count(*) as partner_count,
    sum(case when partner_identifier_code = '1' then 1 else 0 end) as legal_entity_partner_count,
    sum(case when partner_identifier_code = '2' then 1 else 0 end) as individual_partner_count,
    sum(case when partner_identifier_code = '3' then 1 else 0 end) as foreign_partner_count,
    min(partnership_start_date) as first_partnership_start_date,
    max(partnership_start_date) as latest_partnership_start_date
from partners
where company_root_cnpj is not null
group by company_root_cnpj
