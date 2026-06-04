from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TransformationConfig:
    """Transformation runtime settings for the configured platform environment.

    Today this points to dbt Core directories, but the shape keeps the platform
    config ready for future transformation runners.
    """

    type: str
    target: str
    project_dir: Path
    profiles_dir: Path


@dataclass(frozen=True)
class PlatformConfig:
    """Environment-level runtime settings shared by pipeline runs.

    Platform config describes where the pipeline runs, while pipeline YAML
    describes what domain sources should be processed.
    """

    environment: str
    warehouse_type: str
    warehouse_path: Path
    transformation: TransformationConfig


@dataclass(frozen=True)
class SourceLoadConfig:
    """Raw loading contract declared by each pipeline source.

    The contract keeps target table, strategy, keys, and metadata columns close
    to the source declaration instead of hardcoding them in orchestration code.
    """

    target_table: str
    strategy: str
    unique_key: list[str]
    metadata_columns: dict[str, str]


@dataclass(frozen=True)
class PipelineSourceConfig:
    """Source declaration from a pipeline YAML file.

    It connects the user-facing source definition to the extractor and loader
    contracts used by the shared ingestion task.
    """

    name: str
    extractor: str
    uri: str
    load: SourceLoadConfig
    options: dict[str, Any]


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline-level configuration used by orchestration flows.

    The object gives flows a typed view of the pipeline name, row limit, and
    source list without leaking raw YAML dictionaries.
    """

    name: str
    sample_row_limit: int
    sources: list[PipelineSourceConfig]


class ConfigLoader:
    """Load platform and pipeline YAML files into typed runtime contracts.

    Keeping YAML parsing in one class makes flows easier to read and gives the
    platform one place to evolve validation rules.
    """

    def __init__(self, project_root: Path):
        """Create a loader that resolves relative paths from the project root."""

        self.project_root = project_root

    def load_platform(self, config_path: str | Path) -> PlatformConfig:
        """Load environment-level platform settings from YAML.

        Relative paths are resolved from the project root so local commands can
        run from the repository without extra path setup.
        """

        data = self._load_yaml(config_path)
        warehouse = data["warehouse"]
        transformation = data["transformation"]

        return PlatformConfig(
            environment=data.get("environment", "local"),
            warehouse_type=warehouse["type"],
            warehouse_path=self._resolve_path(warehouse["path"]),
            transformation=TransformationConfig(
                type=transformation["type"],
                target=transformation.get("target", "local"),
                project_dir=self._resolve_path(transformation["project_dir"]),
                profiles_dir=self._resolve_path(transformation["profiles_dir"]),
            ),
        )

    def load_pipeline(self, config_path: str | Path) -> PipelineConfig:
        """Load pipeline source declarations from YAML.

        The resulting object is the contract consumed by Prefect flows and
        reusable ingestion tasks.
        """

        data = self._load_yaml(config_path)
        pipeline = data["pipeline"]

        return PipelineConfig(
            name=pipeline["name"],
            sample_row_limit=int(pipeline["sample_row_limit"]),
            sources=[
                PipelineSourceConfig(
                    name=source["name"],
                    extractor=source["extractor"],
                    uri=source["uri"],
                    load=self._load_source_load_config(source),
                    options=source.get("options", {}),
                )
                for source in data["sources"]
            ],
        )

    def _load_source_load_config(self, source: dict[str, Any]) -> SourceLoadConfig:
        """Load the raw table contract for a source declaration.

        A legacy `target_table` fallback is kept so older source declarations
        can still be read while the explicit `load` block is preferred.
        """

        load = source.get("load")
        if load is None:
            return SourceLoadConfig(
                target_table=source["target_table"],
                strategy="overwrite",
                unique_key=[],
                metadata_columns={},
            )

        return SourceLoadConfig(
            target_table=load["target_table"],
            strategy=self._normalize_load_strategy(load.get("strategy", "overwrite")),
            unique_key=list(load.get("unique_key", [])),
            metadata_columns=dict(load.get("metadata_columns", {})),
        )

    def _normalize_load_strategy(self, strategy: str) -> str:
        """Normalize load strategy names accepted by YAML configuration.

        This lets YAML use either `append-only` or `append_only` while the
        Python code receives one consistent strategy name.
        """

        normalized = strategy.replace("-", "_").lower()
        supported_strategies = {"overwrite", "append_only", "upsert"}

        if normalized not in supported_strategies:
            raise ValueError(f"Unsupported load strategy: {strategy}")

        return normalized

    def _load_yaml(self, config_path: str | Path) -> dict[str, Any]:
        """Read a YAML file after resolving it against the project root."""

        path = self._resolve_path(config_path)
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve relative configuration paths from the project root."""

        path = Path(path)
        if path.is_absolute():
            return path
        return self.project_root / path
