"""Módulo para detecção automática de características de arquivos CSV."""

import gzip
import logging
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from ..application.interfaces import ICsvDetector
from ..domain.entities import CsvConfig

try:
    import chardet  # type: ignore[import]
    CHARDET_DISPONIVEL = True
except ImportError:
    CHARDET_DISPONIVEL = False


class DetectorCSV(ICsvDetector):
    """Implementação do detector de CSV."""

    DELIMITADORES: tuple[str, ...] = (",", ";", "\t", "|")

    def detect(self, path: str) -> CsvConfig:
        encoding = self._detectar_encoding(path)
        tipo_compact = self._detectar_compactacao_tipo(path)
        
        delimitador = self._detectar_delimitador(path, encoding, tipo_compact)
        quote_char, escape_char, doublequote = self._detectar_aspas(path, encoding)
        line_terminator = self._detectar_quebras_linha(path)

        return CsvConfig(
            encoding=encoding,
            delimiter=delimitador,
            quote_char=quote_char,
            escape_char=escape_char,
            doublequote=doublequote,
            line_terminator=line_terminator,
            compression=tipo_compact
        )

    def _detectar_compactacao_tipo(self, caminho: str) -> str:
        suffix = Path(caminho).suffix.lower()
        if suffix == ".gz": return "gz"
        if suffix == ".zip": return "zip"
        return "none"

    def _detectar_encoding(self, caminho: str, amostra_bytes: int = 10000) -> str:
        try:
            with open(caminho, "rb") as f:
                amostra = f.read(amostra_bytes)

            if CHARDET_DISPONIVEL:
                res = chardet.detect(amostra)
                encoding = res.get("encoding", "utf-8")
                if res.get("confidence", 0) < 0.7:
                    encoding = self._fallback_encoding(amostra)
            else:
                encoding = self._fallback_encoding(amostra)

            encoding_map = {
                "iso-8859-1": "ISO-8859-1",
                "windows-1252": "cp1252",
                "utf-8": "utf-8",
                "utf-16": "utf-16",
            }
            return encoding_map.get(encoding.lower(), encoding)
        except Exception:
            return "utf-8"

    def _fallback_encoding(self, amostra: bytes) -> str:
        if amostra.startswith(b"\xff\xfe"): return "utf-16"
        if amostra.startswith(b"\xfe\xff"): return "utf-16-be"
        try:
            amostra.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "ISO-8859-1"

    def _detectar_delimitador(self, caminho: str, encoding: str, tipo_compact: str) -> str:
        try:
            if tipo_compact == "gz":
                with gzip.open(caminho, "rt", encoding=encoding, errors="ignore") as f:
                    amostra = "".join([f.readline() for _ in range(5)])
            elif tipo_compact == "zip":
                with ZipFile(caminho, "r") as zf:
                    with zf.open(zf.namelist()[0]) as f:
                        amostra = f.read(2000).decode(encoding, errors="ignore")
            else:
                with open(caminho, encoding=encoding, errors="ignore") as f:
                    amostra = "".join([f.readline() for _ in range(5)])

            contadores = {d: amostra.count(d) for d in self.DELIMITADORES}
            return max(contadores.items(), key=lambda x: x[1])[0] if any(contadores.values()) else ","
        except Exception:
            return ","

    def _detectar_aspas(self, caminho: str, encoding: str) -> tuple[str | None, str | None, bool]:
        try:
            with open(caminho, encoding=encoding, errors="ignore") as f:
                amostra = f.read(2000)
            
            if '"' in amostra:
                return ('"', None, True)
            if "'" in amostra:
                return ("'", None, False)
            return (None, None, True)
        except Exception:
            return (None, None, True)

    def _detectar_quebras_linha(self, caminho: str) -> str:
        try:
            with open(caminho, "rb") as f:
                amostra = f.read(1000)
            return "\r\n" if b"\r\n" in amostra else "\n"
        except Exception:
            return "\n"
