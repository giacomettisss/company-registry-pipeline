with cnaes as (
    select
        cnae_code,
        cnae_description
    from {{ ref('stg_company_registry__cnaes') }}
)

select
    cnae_code,
    cnae_description,
    substring(cnae_code, 1, 2) as cnae_division_code,
    substring(cnae_code, 1, 3) as cnae_group_code,
    substring(cnae_code, 1, 5) as cnae_class_code,
    substring(cnae_code, 1, 7) as cnae_subclass_code,
    cnae_code || ' - ' || cnae_description as cnae_subclass_label
from cnaes
