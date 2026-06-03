with companies as (
    select
        company_root_cnpj,
        legal_name,
        legal_nature_code,
        responsible_qualification_code,
        share_capital,
        company_size_code,
        responsible_federative_entity
    from {{ ref('stg_company_registry__companies') }}
),

simples as (
    select
        company_root_cnpj,
        max(simples_option) as simples_option,
        min(simples_option_date) as simples_option_date,
        max(simples_exclusion_date) as simples_exclusion_date,
        max(mei_option) as mei_option,
        min(mei_option_date) as mei_option_date,
        max(mei_exclusion_date) as mei_exclusion_date
    from {{ ref('stg_company_registry__simples') }}
    group by company_root_cnpj
)

select
    companies.company_root_cnpj,
    companies.legal_name,
    companies.legal_nature_code,
    companies.responsible_qualification_code,
    companies.share_capital,
    companies.company_size_code,
    companies.responsible_federative_entity,
    simples.simples_option,
    {{ yes_no_to_boolean('simples.simples_option') }} as is_simples,
    simples.simples_option_date,
    simples.simples_exclusion_date,
    simples.mei_option,
    {{ yes_no_to_boolean('simples.mei_option') }} as is_mei,
    simples.mei_option_date,
    simples.mei_exclusion_date
from companies
left join simples
    on companies.company_root_cnpj = simples.company_root_cnpj
