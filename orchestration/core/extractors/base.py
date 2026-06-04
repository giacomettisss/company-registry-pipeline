from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    """Runtime source contract passed to extractor implementations.

    The object is created from pipeline YAML and keeps extractors decoupled from
    the original configuration file structure.
    """

    name: str
    uri: str
    target_table: str
    options: dict[str, Any]


@dataclass(frozen=True)
class ExtractionResult:
    """Tabular data extracted from a source and ready for raw loading.

    Extractors return this shape so loaders can write rows without knowing the
    source format, transport protocol, or parsing details.
    """

    source_name: str
    target_table: str
    columns: list[str]
    rows: list[tuple[str | None, ...]]

    @property
    def row_count(self) -> int:
        """Return the number of rows extracted for this source."""

        return len(self.rows)


class BaseExtractor(ABC):
    """Base contract for interchangeable source extraction strategies.

    New extractors should implement this contract so they can be selected from
    YAML through `ExtractorFactory` and reused by any pipeline flow.
    """

    @abstractmethod
    def extract(self, source: SourceConfig, row_limit: int) -> ExtractionResult:
        """Extract bounded rows from a configured source.

        Implementations should return normalized tabular data and leave raw
        warehouse writing to the loader layer.
        """

        raise NotImplementedError
