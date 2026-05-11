"""Entidades de domínio do Conversor Analítico."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ConversionFormat(Enum):
    """Formatos de conversão suportados pelo sistema."""
    PARQUET = "parquet"
    FEATHER = "feather"
    ORC = "orc"
    HDF5 = "h5"
    PICKLE = "pkl"
    JSON = "json"

@dataclass(frozen=True)
class FormatMetadata:
    """Metadados de um formato de conversão."""
    name: str
    extension: str
    description: str
    supports_chunks: bool

@dataclass
class ConversionTask:
    """Representa uma tarefa de conversão de um arquivo."""
    source_path: str
    target_path: str
    format_type: ConversionFormat

@dataclass(frozen=True)
class CsvConfig:
    """Configuração detectada de um arquivo CSV."""
    encoding: str
    delimiter: str
    quote_char: str | None = None
    escape_char: str | None = None
    doublequote: bool = True
    line_terminator: str = "\n"
    compression: str = "none"
