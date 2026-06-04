from prefect import get_run_logger, task

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
    """Extract one configured source and load it into its raw warehouse table.

    The task centralizes extractor selection, raw loading, and source-level
    logs so every pipeline gets the same ingestion behavior and observability.
    """

    logger = get_run_logger()
    logger.info(
        "Starting source ingestion: source=%s extractor=%s target_table=%s load_strategy=%s row_limit=%s",
        source_config.name,
        source_config.extractor,
        source_config.load.target_table,
        source_config.load.strategy,
        sample_row_limit,
    )

    try:
        source = SourceConfig(
            name=source_config.name,
            uri=source_config.uri,
            target_table=source_config.load.target_table,
            options=source_config.options,
        )

        extractor = ExtractorFactory.create(source_config.extractor)
        logger.info(
            "Extractor resolved: source=%s extractor_class=%s",
            source_config.name,
            extractor.__class__.__name__,
        )

        extraction_result = extractor.extract(source, row_limit=sample_row_limit)
        logger.info(
            "Extraction completed: source=%s rows=%s columns=%s",
            extraction_result.source_name,
            extraction_result.row_count,
            len(extraction_result.columns),
        )

        loader = DuckDBLoader(platform_config.warehouse_path)
        load_result = loader.load(extraction_result, strategy=source_config.load.strategy)
        logger.info(
            "Load completed: source=%s target_table=%s load_strategy=%s rows=%s",
            source_config.name,
            load_result.target_table,
            load_result.strategy,
            load_result.row_count,
        )

        return {
            "source_name": source_config.name,
            "target_table": load_result.target_table,
            "load_strategy": load_result.strategy,
            "row_count": load_result.row_count,
        }
    except Exception:
        logger.exception(
            "Source ingestion failed: source=%s extractor=%s target_table=%s load_strategy=%s",
            source_config.name,
            source_config.extractor,
            source_config.load.target_table,
            source_config.load.strategy,
        )
        raise
