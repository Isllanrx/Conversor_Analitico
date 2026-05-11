"""Ponto de entrada principal da aplicação com Lazy Loading para performance."""

import sys
from pathlib import Path

# Adicionar o diretório atual ao sys.path para garantir imports absolutos
root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def bootstrap() -> None:
    """Configura e inicia a aplicação com Injeção de Dependência e Lazy Loading."""
    
    # Imports pesados movidos para dentro do bootstrap para acelerar o arranque do processo
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
    from application.use_cases import ConvertFilesUseCase, ValidateFilesUseCase
    from infrastructure.adapters import LocalFileSystem, PandasCsvReader
    from infrastructure.detector import DetectorCSV
    from infrastructure.savers import PandasFileSaver
    from presentation.app import AplicacaoConversor

    # 1. Infraestrutura
    fs = LocalFileSystem()
    detector = DetectorCSV()
    reader = PandasCsvReader()
    saver = PandasFileSaver()
    
    # Detecção de RAM resiliente
    try:
        import psutil  # type: ignore[import]
        low_ram = psutil.virtual_memory().available < LIMITE_RAM_BAIXO
    except ImportError:
        low_ram = False

    # 2. Casos de Uso
    validate_uc = ValidateFilesUseCase(fs, MAX_ARQUIVOS, MAX_TAMANHO_ARQUIVO)
    convert_uc = ConvertFilesUseCase(fs, detector, reader, saver, PASTA_CONVERTIDOS, low_ram)

    # 3. Metadados de Formatos
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

    # 4. Inicialização da UI
    app = AplicacaoConversor(validate_uc, convert_uc, formatos, config_ui)
    app.mainloop()

if __name__ == "__main__":
    try:
        bootstrap()
    except ImportError as e:
        lib = str(e).split("'")[-2] if "'" in str(e) else "dependência"
        print(f"\nERRO: A biblioteca '{lib}' não foi encontrada.")
        print("Por favor, execute: uv pip install -r requirements.txt")
    except Exception as e:
        print(f"\nERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
        sys.exit(1)
