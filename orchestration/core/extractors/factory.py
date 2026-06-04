from orchestration.core.extractors.base import BaseExtractor
from orchestration.core.extractors.http_zip_csv_extractor import HttpZipCsvExtractor


class ExtractorFactory:
    """Resolve extractor implementations from pipeline configuration keys.

    The factory keeps YAML declarative for ETL developers while giving platform
    engineers one explicit place to register new extraction strategies.
    """

    _extractors: dict[str, type[BaseExtractor]] = {
        "http_zip_csv": HttpZipCsvExtractor,
    }

    @classmethod
    def create(cls, extractor_type: str) -> BaseExtractor:
        """Create an extractor instance for a configured extractor type.

        Raises a clear error when a pipeline references an unsupported
        extractor key.
        """

        try:
            extractor_class = cls._extractors[extractor_type]
        except KeyError as error:
            raise ValueError(f"Unsupported extractor type: {extractor_type}") from error
        return extractor_class()
