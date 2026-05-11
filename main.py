"""Ponto de entrada principal da aplicação."""

import sys
from pathlib import Path

import psutil  # type: ignore[import]

root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from application.use_cases import ConvertFilesUseCase, ValidateFilesUseCase
from config import (
    ALTURA_JANELA,
    ALTURA_LISTA,
    LARGURA_JANELA,
    LIMITE_RAM_BAIXO,
    MAX_ARQUIVOS,
    MAX_TAMANHO_ARQUIVO,
    PASTA_CONVERTIDOS,
)
from domain.entities import FormatMetadata
from infrastructure.adapters import LocalFileSystem, PandasCsvReader
from infrastructure.detector import DetectorCSV
from infrastructure.savers import PandasFileSaver
from presentation.app import AplicacaoConversor


def bootstrap() -> None:
    """Configura e inicia a aplicação com Injeção de Dependência."""
    
    fs = LocalFileSystem()
    detector = DetectorCSV()
    reader = PandasCsvReader()
    saver = PandasFileSaver()
    
    low_ram = psutil.virtual_memory().available < LIMITE_RAM_BAIXO

    validate_uc = ValidateFilesUseCase(fs, MAX_ARQUIVOS, MAX_TAMANHO_ARQUIVO)
    convert_uc = ConvertFilesUseCase(fs, detector, reader, saver, PASTA_CONVERTIDOS, low_ram)

    formatos = [
        FormatMetadata("Parquet", "parquet", "Compactado para Big Data", True),
        FormatMetadata("Feather", "feather", "Leitura rápida", False),
        FormatMetadata("ORC", "orc", "Compatível Hive/Spark", False),
        FormatMetadata("HDF5", "h5", "Formato binário estruturado", True),
        FormatMetadata("Pickle", "pkl", "Serialização Python", False),
        FormatMetadata("JSON", "json", "Formato universal", True),
    ]

    config_ui = {
        "largura": LARGURA_JANELA,
        "altura": ALTURA_JANELA,
        "altura_lista": ALTURA_LISTA
    }

    app = AplicacaoConversor(validate_uc, convert_uc, formatos, config_ui)
    app.mainloop()


if __name__ == "__main__":
    try:
        bootstrap()
    except ImportError as e:
        if "customtkinter" in str(e):
            print("ERRO: Dependências não instaladas! Execute: pip install -r requirements.txt")
        else:
            raise e
