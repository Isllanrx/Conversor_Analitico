"""Implementations for saving files in multiple formats."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import]

from application.interfaces import IFileSaver
from domain.entities import ConversionFormat, CsvConfig

logger = logging.getLogger(__name__)

try:
    import pyarrow as pa  # type: ignore[import]
    import pyarrow.orc as orc  # type: ignore[import]
except ImportError:
    pa = None
    orc = None


class PandasFileSaver(IFileSaver):
    """Implementation of File Saver using Pandas and PyArrow."""

    def __init__(self, chunk_size: int = 100_000) -> None:
        self.chunk_size = chunk_size

    def save(self, data: pd.DataFrame, path: str, format_type: ConversionFormat) -> None:
        """Saves a full DataFrame to the specified format."""
        logger.info(f"Saving full file to {path} as {format_type.value}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        methods = {
            ConversionFormat.PARQUET: lambda: data.to_parquet(path, index=False, compression="snappy"),
            ConversionFormat.FEATHER: lambda: data.to_feather(path),
            ConversionFormat.HDF5: lambda: data.to_hdf(path, key="data", mode="w", format="table", complevel=9, complib="blosc"),
            ConversionFormat.JSON: lambda: data.to_json(path, orient="records", lines=True, force_ascii=False),
            ConversionFormat.PICKLE: lambda: data.to_pickle(path),
            ConversionFormat.ORC: lambda: self._save_orc(data, path),
        }

        if format_type in methods:
            methods[format_type]()
        else:
            raise ValueError(f"Format {format_type} not supported for simple saving.")

    def save_chunks(
        self, 
        source_path: str, 
        target_path: str, 
        format_type: ConversionFormat,
        config: CsvConfig,
        on_progress: Callable[[int, int], None]
    ) -> None:
        """Saves a CSV in chunks to the specified format to save memory."""
        logger.info(f"Saving in chunks to {target_path} as {format_type.value}")
        params = {
            "chunksize": self.chunk_size,
            "encoding": config.encoding,
            "sep": config.delimiter,
            "quotechar": config.quote_char,
            "doublequote": config.doublequote,
            "low_memory": False
        }
        
        reader = pd.read_csv(source_path, **params)
        
        first = True
        for i, chunk in enumerate(reader, 1):
            if format_type == ConversionFormat.PARQUET:
                # For Parquet, we save sub-files to avoid complexity of appending
                ext = Path(target_path).suffix
                chunk_path = str(Path(target_path).parent / f"{Path(target_path).stem}_part{i}{ext}")
                chunk.to_parquet(chunk_path, index=False, compression="snappy")
            
            elif format_type == ConversionFormat.HDF5:
                mode = "w" if first else "a"
                chunk.to_hdf(target_path, key="data", mode=mode, format="table", append=True, complevel=9, complib="blosc")
            
            elif format_type == ConversionFormat.JSON:
                mode = "w" if first else "a"
                with open(target_path, mode, encoding="utf-8") as f:
                    chunk.to_json(f, orient="records", lines=True, force_ascii=False)
            
            first = False
            on_progress(i, -1)

    def _save_orc(self, data: pd.DataFrame, path: str) -> None:
        if pa is None or orc is None:
            raise ImportError("pyarrow is required for ORC format")
        with open(path, "wb") as f:
            orc.write_table(pa.Table.from_pandas(data), f)
