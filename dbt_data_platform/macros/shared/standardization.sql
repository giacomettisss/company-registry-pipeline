{% macro clean_text(column_name, letter_case='none') -%}
    {%- set expression -%}
        nullif(trim(cast({{ column_name }} as varchar)), '')
    {%- endset -%}

    {%- if letter_case == 'upper' -%}
        upper({{ expression }})
    {%- elif letter_case == 'lower' -%}
        lower({{ expression }})
    {%- else -%}
        {{ expression }}
    {%- endif -%}
{%- endmacro %}

{% macro standardize_code(column_name, size) -%}
    lpad({{ clean_text(column_name) }}, {{ size }}, '0')
{%- endmacro %}

{% macro parse_yyyymmdd_date(column_name) -%}
    try_strptime({{ clean_text(column_name) }}, '%Y%m%d')::date
{%- endmacro %}

{% macro yes_no_to_boolean(column_name) -%}
    case
        when {{ clean_text(column_name, 'upper') }} = 'S' then true
        else false
    end
{%- endmacro %}
