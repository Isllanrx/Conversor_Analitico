"""Application use cases."""

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

logger = logging.getLogger(__name__)

class ValidateFilesUseCase:
    """Use case for validating files before processing."""

    def __init__(self, file_system: IFileSystem, max_files: int, max_size: int) -> None:
        self.file_system = file_system
        self.max_files = max_files
        self.max_size = max_size

    def execute(self, file_paths: list[str]) -> str | None:
        if len(file_paths) > self.max_files:
            return f"Limit of {self.max_files} files exceeded."

        try:
            total_size = sum(self.file_system.get_size(p) for p in file_paths)
            if total_size > self.max_size:
                return f"Files are too large (limit: {self.max_size // (1024*1024)}MB)."
        except (FileNotFoundError, OSError) as e:
            logger.error(f"Error checking files: {e}")
            return f"Error accessing files: {e}"

        return None


class ConvertFilesUseCase:
    """Use case for orchestrating file conversion."""

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
                file_name = Path(source_abs).name
                observer.update(i - 1, total, f"Processing: {file_name}")
                
                logger.info(f"Starting conversion of {file_name}")
                
                config = self.detector.detect(source_abs)
                target_name = f"{Path(source_abs).stem}.{format_meta.extension}"
                target_path = str(Path(self.output_dir) / target_name)
                target_abs = self.file_system.get_absolute_path(target_path)

                if self.low_ram_mode and format_meta.supports_chunks:
                    logger.info(f"Using Chunk Mode for {file_name}")
                    self._process_in_chunks(source_abs, target_abs, format_meta, config)
                else:
                    logger.info(f"Using Full Mode for {file_name}")
                    self._process_full(source_abs, target_abs, format_meta, config)

                observer.update(i, total, f"Finished: {file_name}")
                gc.collect()

            except Exception as e:
                logger.exception(f"Error converting {source}")
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
            lambda curr, tot: None # Could be expanded to show chunk progress
        )
