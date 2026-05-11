"""Domain entities for the Analytical Converter."""

from dataclasses import dataclass
from enum import Enum


class ConversionFormat(Enum):
    """Supported conversion formats."""
    PARQUET = "parquet"
    FEATHER = "feather"
    ORC = "orc"
    HDF5 = "h5"
    PICKLE = "pkl"
    JSON = "json"

@dataclass(frozen=True)
class FormatMetadata:
    """Metadata for a conversion format."""
    name: str
    extension: str
    description: str
    supports_chunks: bool

@dataclass
class ConversionTask:
    """Represents a file conversion task."""
    source_path: str
    target_path: str
    format_type: ConversionFormat

@dataclass(frozen=True)
class CsvConfig:
    """Detected configuration of a CSV file."""
    encoding: str
    delimiter: str
    quote_char: str | None = None
    escape_char: str | None = None
    doublequote: bool = True
    line_terminator: str = "\n"
    compression: str = "none"
