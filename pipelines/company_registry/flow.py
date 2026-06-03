from pathlib import Path

from prefect import flow

from orchestration.core.config import ConfigLoader
from orchestration.tasks.ingestion import ingest_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLATFORM_CONFIG_PATH = "configs/platforms/local.yml"


@flow(name="company-registry-ingestion")
def company_registry_ingestion_flow(
    pipeline_config_path: str,
    platform_config_path: str = DEFAULT_PLATFORM_CONFIG_PATH,
) -> list[dict[str, str | int]]:
    config_loader = ConfigLoader(PROJECT_ROOT)
    platform_config = config_loader.load_platform(platform_config_path)
    pipeline_config = config_loader.load_pipeline(pipeline_config_path)

    results = []
    for source_config in pipeline_config.sources:
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
) -> list[dict[str, str | int]]:
    return company_registry_ingestion_flow(
        pipeline_config_path=pipeline_config_path,
        platform_config_path=platform_config_path,
    )
