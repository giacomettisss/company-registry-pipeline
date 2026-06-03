{% snapshot snap_company_registry__share_capital %}

{{
    config(
        target_schema='main',
        unique_key='company_root_cnpj',
        strategy='check',
        check_cols=['share_capital'],
        hard_deletes='invalidate'
    )
}}

select
    company_root_cnpj,
    legal_name,
    legal_nature_code,
    share_capital,
    company_size_code,
    is_simples,
    is_mei
from {{ ref('int_company_registry__company_profile') }}

{% endsnapshot %}
