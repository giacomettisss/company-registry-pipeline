with company_profile as (
    select
        company_root_cnpj,
        legal_name,
        legal_nature_code,
        responsible_qualification_code,
        share_capital,
        company_size_code,
        responsible_federative_entity,
        is_simples,
        simples_option_date,
        simples_exclusion_date,
        is_mei,
        mei_option_date,
        mei_exclusion_date
    from {{ ref('int_company_registry__company_profile') }}
)

select
    company_root_cnpj,
    legal_name,
    legal_nature_code,
    responsible_qualification_code,
    share_capital,
    case
        when share_capital < 10000 then 'up_to_10k'
        when share_capital < 100000 then '10k_to_100k'
        when share_capital < 1000000 then '100k_to_1m'
        else 'over_1m'
    end as share_capital_range,
    company_size_code,
    case company_size_code
        when '00' then 'not_informed'
        when '01' then 'micro_company'
        when '03' then 'small_company'
        when '05' then 'other'
        else 'unknown'
    end as company_size_label,
    responsible_federative_entity,
    is_simples,
    simples_option_date,
    simples_exclusion_date,
    is_mei,
    mei_option_date,
    mei_exclusion_date
from company_profile
