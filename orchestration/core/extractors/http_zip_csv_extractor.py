from csv import reader
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import requests

from orchestration.core.extractors.base import BaseExtractor, ExtractionResult, SourceConfig


class HttpZipCsvExtractor(BaseExtractor):
    """Extractor for HTTP ZIP sources that contain CSV-like files.

    It supports the public company registry files used by this challenge and
    can be reused by future sources with the same transport and file pattern.
    """

    def extract(self, source: SourceConfig, row_limit: int) -> ExtractionResult:
        """Download a ZIP file, read its CSV content, and return bounded rows.

        Parsing behavior such as encoding, delimiter, header handling, and
        fallback columns is controlled by the source options declared in YAML.
        """

        response = requests.get(source.uri, timeout=120)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as archive:
            csv_name = self._find_csv_name(archive)
            with archive.open(csv_name) as csv_file:
                text_file = TextIOWrapper(csv_file, encoding=source.options.get("encoding", "utf-8"))
                return self._read_csv(source, text_file, row_limit)

    def _find_csv_name(self, archive: ZipFile) -> str:
        """Return the first CSV file in the archive, or the first regular file.

        The fallback keeps the extractor tolerant of source files that do not
        use a `.csv` extension but still contain delimited text.
        """

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
        """Parse CSV rows according to source options and the configured row limit.

        The method preserves source-shaped string values and delegates type
        standardization to dbt staging models.
        """

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
        """Trim or pad a row so it matches the configured column count.

        This prevents irregular source rows from breaking the raw table insert
        while keeping missing trailing values explicit as `None`.
        """

        normalized = row[:expected_size]
        if len(normalized) < expected_size:
            normalized.extend([None] * (expected_size - len(normalized)))
        return tuple(normalized)
