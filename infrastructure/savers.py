"""Implementações de salvamento de arquivos em múltiplos formatos."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import]

from application.interfaces import IFileSaver
from domain.entities import ConversionFormat, CsvConfig

try:
    import pyarrow as pa  # type: ignore[import]
    import pyarrow.orc as orc  # type: ignore[import]
except ImportError:
    pa = None
    orc = None


class PandasFileSaver(IFileSaver):
    """Implementação do salvador de arquivos usando Pandas e PyArrow."""

    def __init__(self, chunk_size: int = 100_000) -> None:
        self.chunk_size = chunk_size

    def save(self, data: pd.DataFrame, path: str, format_type: ConversionFormat) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        methods = {
            ConversionFormat.PARQUET: lambda: data.to_parquet(path, index=False, compression="snappy"),
            ConversionFormat.FEATHER: lambda: data.to_feather(path),
            ConversionFormat.HDF5: lambda: data.to_hdf(path, key="dados", mode="w", format="table", complevel=9, complib="blosc"),
            ConversionFormat.JSON: lambda: data.to_json(path, orient="records", lines=True, force_ascii=False),
            ConversionFormat.PICKLE: lambda: data.to_pickle(path),
            ConversionFormat.ORC: lambda: self._save_orc(data, path),
        }

        if format_type in methods:
            methods[format_type]()
        else:
            raise ValueError(f"Formato {format_type} não suportado para salvamento simples.")

    def save_chunks(
        self, 
        source_path: str, 
        target_path: str, 
        format_type: ConversionFormat,
        config: CsvConfig,
        on_progress: Callable[[int, int], None]
    ) -> None:
        params = {
            "chunksize": self.chunk_size,
            "encoding": config.encoding,
            "sep": config.delimiter,
            "quotechar": config.quote_char,
            "doublequote": config.doublequote,
            "low_memory": False
        }
        
        # Iterar para processar chunks
        reader = pd.read_csv(source_path, **params)
        
        first = True
        for i, chunk in enumerate(reader, 1):
            if format_type == ConversionFormat.PARQUET:
                # No caso de Parquet em chunks, o ideal é salvar arquivos separados ou usar fastparquet/pyarrow engine
                ext = Path(target_path).suffix
                chunk_path = str(Path(target_path).parent / f"{Path(target_path).stem}_pedaco{i}{ext}")
                chunk.to_parquet(chunk_path, index=False, compression="snappy")
            
            elif format_type == ConversionFormat.HDF5:
                mode = "w" if first else "a"
                chunk.to_hdf(target_path, key="dados", mode=mode, format="table", append=True, complevel=9, complib="blosc")
            
            elif format_type == ConversionFormat.JSON:
                mode = "w" if first else "a"
                with open(target_path, mode, encoding="utf-8") as f:
                    chunk.to_json(f, orient="records", lines=True, force_ascii=False)
            
            first = False
            on_progress(i, -1)

    def _save_orc(self, data: pd.DataFrame, path: str) -> None:
        if pa is None or orc is None:
            raise ImportError("pyarrow é necessário para salvar em formato ORC")
        with open(path, "wb") as f:
            orc.write_table(pa.Table.from_pandas(data), f)
