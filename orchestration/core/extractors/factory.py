from orchestration.core.extractors.base import BaseExtractor
from orchestration.core.extractors.http_zip_csv_extractor import HttpZipCsvExtractor


class ExtractorFactory:
    _extractors: dict[str, type[BaseExtractor]] = {
        "http_zip_csv": HttpZipCsvExtractor,
    }

    @classmethod
    def create(cls, extractor_type: str) -> BaseExtractor:
        try:
            extractor_class = cls._extractors[extractor_type]
        except KeyError as error:
            raise ValueError(f"Unsupported extractor type: {extractor_type}") from error
        return extractor_class()
