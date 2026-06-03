import pytest

from orchestration.core.config import PipelineConfig, PipelineSourceConfig, SourceLoadConfig
from orchestration.core.source_selection import select_sources


def test_select_sources_supports_all_one_and_missing_source():
    source_load = SourceLoadConfig(
        target_table="raw_sample",
        strategy="overwrite",
        unique_key=[],
        metadata_columns={},
    )
    cnaes = PipelineSourceConfig(
        name="cnaes",
        extractor="http_zip_csv",
        uri="https://example.test/cnaes.zip",
        load=source_load,
        options={},
    )
    simples = PipelineSourceConfig(
        name="simples",
        extractor="http_zip_csv",
        uri="https://example.test/simples.zip",
        load=source_load,
        options={},
    )
    pipeline_config = PipelineConfig(
        name="company_registry",
        sample_row_limit=10000,
        sources=[cnaes, simples],
    )

    assert select_sources(pipeline_config, None) == [cnaes, simples]
    assert select_sources(pipeline_config, "simples") == [simples]

    with pytest.raises(ValueError, match="Available sources: cnaes, simples"):
        select_sources(pipeline_config, "partners")
