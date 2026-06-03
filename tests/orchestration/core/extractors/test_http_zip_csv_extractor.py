from io import BytesIO
from zipfile import ZipFile

from orchestration.core.extractors.base import SourceConfig
from orchestration.core.extractors.http_zip_csv_extractor import HttpZipCsvExtractor


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self) -> None:
        return None


def build_zip(content: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("sample.csv", content)
    return buffer.getvalue()


def test_http_zip_csv_extractor_respects_row_limit(monkeypatch):
    zip_content = build_zip("code;description\n001;First\n002;Second\n")

    def fake_get(uri: str, timeout: int) -> FakeResponse:
        return FakeResponse(zip_content)

    monkeypatch.setattr("orchestration.core.extractors.http_zip_csv_extractor.requests.get", fake_get)

    source = SourceConfig(
        name="sample",
        uri="https://example.test/sample.zip",
        target_table="raw_sample",
        options={"delimiter": ";", "encoding": "utf-8"},
    )

    result = HttpZipCsvExtractor().extract(source, row_limit=1)

    assert result.columns == ["code", "description"]
    assert result.rows == [("001", "First")]
    assert result.target_table == "raw_sample"
