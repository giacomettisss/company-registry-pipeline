from orchestration.core.config import PipelineConfig, PipelineSourceConfig


def select_sources(
    pipeline_config: PipelineConfig,
    source_name: str | None,
) -> list[PipelineSourceConfig]:
    """Return all pipeline sources or one named source for partial local runs.

    This keeps source filtering reusable across CLI runs, Prefect flows, and
    future deployment parameters.
    """

    if source_name is None:
        return pipeline_config.sources

    matches = [source for source in pipeline_config.sources if source.name == source_name]
    if matches:
        return matches

    available_sources = ", ".join(source.name for source in pipeline_config.sources)
    raise ValueError(
        f"Source {source_name} was not found in pipeline {pipeline_config.name}. "
        f"Available sources: {available_sources}."
    )
