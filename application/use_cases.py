"""Casos de uso da aplicação."""

import gc
import logging
from pathlib import Path
from typing import Any

from domain.entities import ConversionFormat, CsvConfig, FormatMetadata
from application.interfaces import (
    ICsvDetector,
    ICsvReader,
    IFileSaver,
    IFileSystem,
    IProgressObserver,
)


class ValidateFilesUseCase:
    """Caso de uso para validação de arquivos antes do processamento."""

    def __init__(self, file_system: IFileSystem, max_files: int, max_size: int) -> None:
        self.file_system = file_system
        self.max_files = max_files
        self.max_size = max_size

    def execute(self, file_paths: list[str]) -> str | None:
        if len(file_paths) > self.max_files:
            return f"Limite de {self.max_files} arquivos excedido."

        try:
            total_size = sum(self.file_system.get_size(p) for p in file_paths)
            if total_size > self.max_size:
                return "Arquivos muito grandes."
        except (FileNotFoundError, OSError) as erro:
            logging.error(f"Erro ao verificar arquivos: {erro}")
            return f"Erro ao acessar arquivos: {erro}"

        return None


class ConvertFilesUseCase:
    """Caso de uso para orquestrar a conversão de arquivos."""

    def __init__(
        self,
        file_system: IFileSystem,
        detector: ICsvDetector,
        reader: ICsvReader,
        saver: IFileSaver,
        output_dir: str,
        low_ram_mode: bool
    ) -> None:
        self.file_system = file_system
        self.detector = detector
        self.reader = reader
        self.saver = saver
        self.output_dir = output_dir
        self.low_ram_mode = low_ram_mode

    def execute(
        self, 
        file_paths: list[str], 
        format_meta: FormatMetadata, 
        observer: IProgressObserver
    ) -> None:
        self.file_system.make_dir(self.output_dir)
        total = len(file_paths)

        for i, source in enumerate(file_paths, 1):
            try:
                source_abs = self.file_system.get_absolute_path(source)
                observer.update(i - 1, total, f"Processando: {Path(source_abs).name}")
                
                config = self.detector.detect(source_abs)
                target_name = f"{Path(source_abs).stem}.{format_meta.extension}"
                target_path = str(Path(self.output_dir) / target_name)
                target_abs = self.file_system.get_absolute_path(target_path)

                if self.low_ram_mode and format_meta.supports_chunks:
                    self._process_in_chunks(source_abs, target_abs, format_meta, config)
                else:
                    self._process_full(source_abs, target_abs, format_meta, config)

                observer.update(i, total, f"Concluído: {Path(source_abs).name}")
                gc.collect()

            except Exception as e:
                logging.error(f"Erro ao converter {source}: {e}")
                raise

    def _process_full(self, source: str, target: str, format_meta: FormatMetadata, config: CsvConfig) -> None:
        df = self.reader.read(source, config)
        if df is not None:
            self.saver.save(df, target, ConversionFormat(format_meta.extension))

    def _process_in_chunks(self, source: str, target: str, format_meta: FormatMetadata, config: CsvConfig) -> None:
        self.saver.save_chunks(
            source, 
            target, 
            ConversionFormat(format_meta.extension), 
            config,
            lambda curr, tot: None
        )
