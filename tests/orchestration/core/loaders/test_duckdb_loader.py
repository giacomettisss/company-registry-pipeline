import duckdb

from orchestration.core.extractors.base import ExtractionResult
from orchestration.core.loaders.duckdb_loader import DuckDBLoader


def test_duckdb_loader_creates_table(tmp_path):
    db_path = tmp_path / "test.duckdb"
    extraction_result = ExtractionResult(
        source_name="sample",
        target_table="raw_sample",
        columns=["code", "description"],
        rows=[("001", "First")],
    )

    load_result = DuckDBLoader(db_path).load(extraction_result)

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute("select code, description from raw_sample").fetchall()

    assert load_result.row_count == 1
    assert rows == [("001", "First")]
