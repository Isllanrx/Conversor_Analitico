"""Ponto de entrada principal da aplicação com Lazy Loading para performance."""

import sys
from pathlib import Path

# Adicionar o diretório atual ao sys.path para garantir imports absolutos
root_dir = Path(__file__).parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def bootstrap() -> None:
    """Configura e inicia a aplicação com Injeção de Dependência e Lazy Loading."""
    
    # 0. Setup Logging
    from infrastructure.logging_config import setup_logging
    from config import LOG_LEVEL
    setup_logging(LOG_LEVEL)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Iniciando bootstrap da aplicação...")

    # 1. Imports pesados (Lazy Loading)
    from config import (
        UI_CONFIG,
        LOW_RAM_THRESHOLD,
        MAX_FILES,
        MAX_FILE_SIZE,
        CONVERTED_DIR,
    )
    from domain.entities import FormatMetadata
    from application.use_cases import ConvertFilesUseCase, ValidateFilesUseCase
    from infrastructure.adapters import LocalFileSystem, PandasCsvReader
    from infrastructure.detector import DetectorCSV
    from infrastructure.savers import PandasFileSaver
    from presentation.app import AplicacaoConversor

    # 2. Infraestrutura
    fs = LocalFileSystem()
    detector = DetectorCSV()
    reader = PandasCsvReader()
    saver = PandasFileSaver()
    
    # Detecção de RAM resiliente
    try:
        import psutil  # type: ignore[import]
        low_ram = psutil.virtual_memory().available < LOW_RAM_THRESHOLD
        if low_ram:
            logger.warning(f"Sistema com RAM baixa detectada. Modo Low RAM ativado.")
    except ImportError:
        logger.warning("psutil não instalado. Detecção de RAM desativada.")
        low_ram = False

    # 3. Casos de Uso
    validate_uc = ValidateFilesUseCase(fs, MAX_FILES, MAX_FILE_SIZE)
    convert_uc = ConvertFilesUseCase(fs, detector, reader, saver, CONVERTED_DIR, low_ram)

    # 4. Metadados de Formatos
    formatos = [
        FormatMetadata("Parquet", "parquet", "Compactado para Big Data (Recomendado)", True),
        FormatMetadata("Feather", "feather", "Leitura ultra-rápida (V2)", False),
        FormatMetadata("ORC", "orc", "Compatível Hive/Spark", False),
        FormatMetadata("HDF5", "h5", "Formato binário para grandes volumes", True),
        FormatMetadata("Pickle", "pkl", "Serialização nativa Python", False),
        FormatMetadata("JSON", "json", "Formato universal (Lines)", True),
    ]

    # 5. Inicialização da UI
    logger.info("Lançando interface gráfica...")
    app = AplicacaoConversor(validate_uc, convert_uc, formatos, UI_CONFIG)
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
