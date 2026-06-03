from prefect import task

from orchestration.core.config import PipelineSourceConfig, PlatformConfig
from orchestration.core.extractors.base import SourceConfig
from orchestration.core.extractors.factory import ExtractorFactory
from orchestration.core.loaders.duckdb_loader import DuckDBLoader


@task
def ingest_source(
    source_config: PipelineSourceConfig,
    platform_config: PlatformConfig,
    sample_row_limit: int,
) -> dict[str, str | int]:
    source = SourceConfig(
        name=source_config.name,
        uri=source_config.uri,
        target_table=source_config.load.target_table,
        options=source_config.options,
    )

    extractor = ExtractorFactory.create(source_config.extractor)
    extraction_result = extractor.extract(source, row_limit=sample_row_limit)

    loader = DuckDBLoader(platform_config.warehouse_path)
    load_result = loader.load(extraction_result, strategy=source_config.load.strategy)

    return {
        "source_name": source_config.name,
        "target_table": load_result.target_table,
        "load_strategy": load_result.strategy,
        "row_count": load_result.row_count,
    }
