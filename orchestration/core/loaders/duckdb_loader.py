from dataclasses import dataclass
from pathlib import Path
import re

import duckdb

from orchestration.core.extractors.base import ExtractionResult


VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class LoadResult:
    """Metadata returned after writing extracted rows to a raw table.

    Prefect tasks return this information so pipeline runs can report what was
    loaded without exposing warehouse-specific implementation details.
    """

    target_table: str
    strategy: str
    row_count: int


class DuckDBLoader:
    """Local warehouse loader that writes extraction results into DuckDB raw tables.

    The loader is the local implementation of the source-to-raw contract and
    can later be complemented by cloud loaders such as BigQuery.
    """

    def __init__(self, warehouse_path: Path):
        """Create a loader for the configured local DuckDB warehouse path."""

        self.warehouse_path = warehouse_path

    def load(self, result: ExtractionResult, strategy: str = "overwrite") -> LoadResult:
        """Load an extraction result using a supported raw load strategy.

        Only `overwrite` is implemented for the local challenge flow; other
        validated strategies are reserved for production evolution.
        """

        strategy = self._validate_load_strategy(strategy)

        if strategy == "overwrite":
            return self._load_overwrite(result, strategy)

        raise NotImplementedError(f"Load strategy is not implemented yet: {strategy}")

    def _load_overwrite(self, result: ExtractionResult, strategy: str) -> LoadResult:
        """Replace a raw table with the current extraction result.

        This is suitable for bounded local samples and explicit full-refresh
        scenarios, while production raw history should evolve to append-only.
        """

        table_name = self._validate_identifier(result.target_table)
        columns = [self._validate_identifier(column) for column in result.columns]
        self.warehouse_path.parent.mkdir(parents=True, exist_ok=True)

        with duckdb.connect(str(self.warehouse_path)) as connection:
            column_sql = ", ".join(f"{column} varchar" for column in columns)
            connection.execute(f"create or replace table {table_name} ({column_sql})")

            if result.rows:
                placeholders = ", ".join("?" for _ in columns)
                connection.executemany(
                    f"insert into {table_name} values ({placeholders})",
                    result.rows,
                )

        return LoadResult(target_table=table_name, strategy=strategy, row_count=result.row_count)

    def _validate_load_strategy(self, strategy: str) -> str:
        """Normalize and validate the raw load strategy name.

        The accepted names match the YAML load contract so unsupported
        strategies fail before any warehouse write starts.
        """

        normalized = strategy.replace("-", "_").lower()
        supported_strategies = {"overwrite", "append_only", "upsert"}

        if normalized not in supported_strategies:
            raise ValueError(f"Unsupported load strategy: {strategy}")

        return normalized

    def _validate_identifier(self, identifier: str) -> str:
        """Validate a SQL identifier before composing DuckDB statements.

        Table and column names come from configuration or source metadata, so
        they are checked before being interpolated into SQL.
        """

        if not VALID_IDENTIFIER.match(identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier
