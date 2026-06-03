from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TransformationConfig:
    type: str
    project_dir: Path
    profiles_dir: Path


@dataclass(frozen=True)
class PlatformConfig:
    environment: str
    warehouse_type: str
    warehouse_path: Path
    transformation: TransformationConfig


@dataclass(frozen=True)
class PipelineSourceConfig:
    name: str
    extractor: str
    uri: str
    target_table: str
    options: dict[str, Any]


@dataclass(frozen=True)
class PipelineConfig:
    name: str
    sample_row_limit: int
    sources: list[PipelineSourceConfig]


class ConfigLoader:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def load_platform(self, config_path: str | Path) -> PlatformConfig:
        data = self._load_yaml(config_path)
        warehouse = data["warehouse"]
        transformation = data["transformation"]

        return PlatformConfig(
            environment=data.get("environment", "local"),
            warehouse_type=warehouse["type"],
            warehouse_path=self._resolve_path(warehouse["path"]),
            transformation=TransformationConfig(
                type=transformation["type"],
                project_dir=self._resolve_path(transformation["project_dir"]),
                profiles_dir=self._resolve_path(transformation["profiles_dir"]),
            ),
        )

    def load_pipeline(self, config_path: str | Path) -> PipelineConfig:
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
                    target_table=source["target_table"],
                    options=source.get("options", {}),
                )
                for source in data["sources"]
            ],
        )

    def _load_yaml(self, config_path: str | Path) -> dict[str, Any]:
        path = self._resolve_path(config_path)
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _resolve_path(self, path: str | Path) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        return self.project_root / path
