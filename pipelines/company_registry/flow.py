from pathlib import Path

from prefect import flow

from orchestration.core.config import ConfigLoader
from orchestration.core.source_selection import select_sources
from orchestration.tasks.ingestion import ingest_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLATFORM_CONFIG_PATH = "configs/platforms/local.yml"


@flow(name="company-registry-ingestion")
def company_registry_ingestion_flow(
    pipeline_config_path: str,
    platform_config_path: str = DEFAULT_PLATFORM_CONFIG_PATH,
    source_name: str | None = None,
) -> list[dict[str, str | int]]:
    """Run source-to-raw ingestion for the company registry pipeline.

    The flow composes shared platform pieces and keeps domain code focused on
    which sources should run, not how extraction and loading are implemented.
    """

    config_loader = ConfigLoader(PROJECT_ROOT)
    platform_config = config_loader.load_platform(platform_config_path)
    pipeline_config = config_loader.load_pipeline(pipeline_config_path)
    source_configs = select_sources(pipeline_config, source_name)

    results = []
    for source_config in source_configs:
        results.append(
            ingest_source(
                source_config=source_config,
                platform_config=platform_config,
                sample_row_limit=pipeline_config.sample_row_limit,
            )
        )

    return results


def run_flow(
    pipeline_config_path: str,
    platform_config_path: str = DEFAULT_PLATFORM_CONFIG_PATH,
    source_name: str | None = None,
) -> list[dict[str, str | int]]:
    """Standard pipeline entrypoint used by the shared CLI convention.

    New pipeline modules should expose the same function shape so the generic
    CLI can run them without pipeline-specific registration.
    """

    return company_registry_ingestion_flow(
        pipeline_config_path=pipeline_config_path,
        platform_config_path=platform_config_path,
        source_name=source_name,
    )
