from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    name: str
    uri: str
    target_table: str
    options: dict[str, Any]


@dataclass(frozen=True)
class ExtractionResult:
    source_name: str
    target_table: str
    columns: list[str]
    rows: list[tuple[str | None, ...]]

    @property
    def row_count(self) -> int:
        return len(self.rows)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source: SourceConfig, row_limit: int) -> ExtractionResult:
        raise NotImplementedError
