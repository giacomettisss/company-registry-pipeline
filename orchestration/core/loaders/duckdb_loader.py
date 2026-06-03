from dataclasses import dataclass
from pathlib import Path
import re

import duckdb

from orchestration.core.extractors.base import ExtractionResult


VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class LoadResult:
    target_table: str
    row_count: int


class DuckDBLoader:
    def __init__(self, warehouse_path: Path):
        self.warehouse_path = warehouse_path

    def load(self, result: ExtractionResult) -> LoadResult:
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

        return LoadResult(target_table=table_name, row_count=result.row_count)

    def _validate_identifier(self, identifier: str) -> str:
        if not VALID_IDENTIFIER.match(identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier
