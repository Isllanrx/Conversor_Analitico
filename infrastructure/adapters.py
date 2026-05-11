"""Concrete implementations of infrastructure interfaces."""

import os
import logging
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import]

from application.interfaces import ICsvReader, IFileSystem
from domain.entities import CsvConfig

logger = logging.getLogger(__name__)

class LocalFileSystem(IFileSystem):
    """Implementation for local file system operations."""

    def get_size(self, path: str) -> int:
        return os.path.getsize(self.get_absolute_path(path))

    def exists(self, path: str) -> bool:
        return Path(path).resolve().exists()

    def make_dir(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def get_absolute_path(self, path: str) -> str:
        obj = Path(path)
        if not obj.is_absolute():
            obj = obj.resolve()
        return str(obj.absolute())


class PandasCsvReader(ICsvReader):
    """Implementation of CSV reading using Pandas."""

    def read(self, path: str, config: CsvConfig) -> Any:
        """Reads a CSV file into a Pandas DataFrame."""
        logger.info(f"Reading CSV: {path} with encoding {config.encoding}")
        
        params: dict[str, Any] = {
            "low_memory": False,
            "encoding": config.encoding,
            "sep": config.delimiter,
            "quotechar": config.quote_char,
            "doublequote": config.doublequote,
        }

        if not config.doublequote and config.escape_char:
            params["escapechar"] = config.escape_char

        if config.compression == "gz":
            params["compression"] = "gzip"
        elif config.compression == "zip":
            import io
            from zipfile import ZipFile
            with ZipFile(path, "r") as zf:
                name = zf.namelist()[0]
                with zf.open(name) as f:
                    # Optimized reading of zip content
                    return pd.read_csv(f, **params)

        return pd.read_csv(path, **params)
