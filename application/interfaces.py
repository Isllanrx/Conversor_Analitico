"""Interfaces (Portas) da camada de aplicação."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Protocol

from ..domain.entities import ConversionFormat, CsvConfig


class IFileSystem(ABC):
    """Interface para operações de sistema de arquivos."""
    
    @abstractmethod
    def get_size(self, path: str) -> int:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def make_dir(self, path: str) -> None:
        pass

    @abstractmethod
    def get_absolute_path(self, path: str) -> str:
        pass


class ICsvDetector(ABC):
    """Interface para detecção de configurações de CSV."""
    
    @abstractmethod
    def detect(self, path: str) -> CsvConfig:
        pass


class IFileSaver(ABC):
    """Interface para salvar arquivos em diferentes formatos."""

    @abstractmethod
    def save(self, data: Any, path: str, format_type: ConversionFormat) -> None:
        pass

    @abstractmethod
    def save_chunks(
        self, 
        source_path: str, 
        target_path: str, 
        format_type: ConversionFormat,
        config: CsvConfig,
        on_progress: Callable[[int, int], None]
    ) -> None:
        pass


class ICsvReader(ABC):
    """Interface para leitura de arquivos CSV."""

    @abstractmethod
    def read(self, path: str, config: CsvConfig) -> Any:
        pass


class IProgressObserver(Protocol):
    """Protocolo para observadores de progresso."""
    def update(self, current: int, total: int, message: str = "") -> None:
        ...
