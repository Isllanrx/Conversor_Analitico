"""Module for automatic CSV file characteristics detection."""

import gzip
import logging
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from application.interfaces import ICsvDetector
from domain.entities import CsvConfig

logger = logging.getLogger(__name__)

try:
    import chardet  # type: ignore[import]
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


class DetectorCSV(ICsvDetector):
    """Implementation of CSV detector with optimized file reading."""

    DELIMITERS: tuple[str, ...] = (",", ";", "\t", "|")

    def detect(self, path: str) -> CsvConfig:
        """Detects CSV configuration by reading the file efficiently."""
        logger.info(f"Detecting configuration for: {path}")
        
        encoding = self._detect_encoding(path)
        compression_type = self._detect_compression_type(path)
        
        # Read a small sample once for delimiter and other checks
        sample = self._get_sample(path, encoding, compression_type)
        
        delimiter = self._detect_delimiter(sample)
        quote_char, escape_char, doublequote = self._detect_quotes(sample)
        line_terminator = self._detect_line_terminators(path) # Binary check is faster

        return CsvConfig(
            encoding=encoding,
            delimiter=delimiter,
            quote_char=quote_char,
            escape_char=escape_char,
            doublequote=doublequote,
            line_terminator=line_terminator,
            compression=compression_type
        )

    def _detect_compression_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix == ".gz": return "gz"
        if suffix == ".zip": return "zip"
        return "none"

    def _get_sample(self, path: str, encoding: str, compression: str, size: int = 5000) -> str:
        """Reads a text sample from the file regardless of compression."""
        try:
            if compression == "gz":
                with gzip.open(path, "rt", encoding=encoding, errors="ignore") as f:
                    return f.read(size)
            elif compression == "zip":
                with ZipFile(path, "r") as zf:
                    with zf.open(zf.namelist()[0]) as f:
                        return f.read(size).decode(encoding, errors="ignore")
            else:
                with open(path, encoding=encoding, errors="ignore") as f:
                    return f.read(size)
        except Exception as e:
            logger.error(f"Error reading sample from {path}: {e}")
            return ""

    def _detect_encoding(self, path: str, sample_size: int = 10000) -> str:
        try:
            with open(path, "rb") as f:
                raw_data = f.read(sample_size)

            if CHARDET_AVAILABLE:
                res = chardet.detect(raw_data)
                encoding = res.get("encoding", "utf-8")
                if res.get("confidence", 0) < 0.7:
                    encoding = self._fallback_encoding(raw_data)
            else:
                encoding = self._fallback_encoding(raw_data)

            encoding_map = {
                "iso-8859-1": "ISO-8859-1",
                "windows-1252": "cp1252",
                "utf-8": "utf-8",
                "utf-16": "utf-16",
            }
            return encoding_map.get(encoding.lower(), encoding)
        except Exception:
            return "utf-8"

    def _fallback_encoding(self, raw_data: bytes) -> str:
        if raw_data.startswith(b"\xff\xfe"): return "utf-16"
        if raw_data.startswith(b"\xfe\xff"): return "utf-16-be"
        try:
            raw_data.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "ISO-8859-1"

    def _detect_delimiter(self, sample: str) -> str:
        if not sample:
            return ","
        counts = {d: sample.count(d) for d in self.DELIMITERS}
        return max(counts.items(), key=lambda x: x[1])[0] if any(counts.values()) else ","

    def _detect_quotes(self, sample: str) -> tuple[str | None, str | None, bool]:
        if '"' in sample:
            return ('"', None, True)
        if "'" in sample:
            return ("'", None, False)
        return (None, None, True)

    def _detect_line_terminators(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                chunk = f.read(1000)
            return "\r\n" if b"\r\n" in chunk else "\n"
        except Exception:
            return "\n"
