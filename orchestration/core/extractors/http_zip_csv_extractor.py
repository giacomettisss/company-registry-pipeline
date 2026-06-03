from csv import reader
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import requests

from orchestration.core.extractors.base import BaseExtractor, ExtractionResult, SourceConfig


class HttpZipCsvExtractor(BaseExtractor):
    def extract(self, source: SourceConfig, row_limit: int) -> ExtractionResult:
        response = requests.get(source.uri, timeout=120)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as archive:
            csv_name = self._find_csv_name(archive)
            with archive.open(csv_name) as csv_file:
                text_file = TextIOWrapper(csv_file, encoding=source.options.get("encoding", "utf-8"))
                return self._read_csv(source, text_file, row_limit)

    def _find_csv_name(self, archive: ZipFile) -> str:
        fallback_name = None
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            if name.lower().endswith(".csv"):
                return name
            fallback_name = fallback_name or name

        if fallback_name:
            return fallback_name

        raise FileNotFoundError("No regular file found inside ZIP archive.")

    def _read_csv(self, source: SourceConfig, text_file: TextIOWrapper, row_limit: int) -> ExtractionResult:
        delimiter = source.options.get("delimiter", ",")
        has_header = bool(source.options.get("has_header", True))
        csv_reader = reader(text_file, delimiter=delimiter)

        if has_header:
            columns = next(csv_reader)
        else:
            columns = source.options.get("columns", [])

        if not columns:
            raise ValueError(f"Missing columns for source {source.name}.")

        rows = []
        for row in csv_reader:
            rows.append(self._normalize_row(row, len(columns)))
            if len(rows) >= row_limit:
                break

        return ExtractionResult(
            source_name=source.name,
            target_table=source.target_table,
            columns=columns,
            rows=rows,
        )

    def _normalize_row(self, row: list[str], expected_size: int) -> tuple[str | None, ...]:
        normalized = row[:expected_size]
        if len(normalized) < expected_size:
            normalized.extend([None] * (expected_size - len(normalized)))
        return tuple(normalized)
