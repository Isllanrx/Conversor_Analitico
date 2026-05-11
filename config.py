import logging
from pathlib import Path

# Configuração de Logging
LOG_LEVEL = logging.INFO

# Constantes de diretório
ROOT_DIR: Path = Path(__file__).parent.absolute().resolve()
CONVERTED_DIR: str = str(ROOT_DIR / 'Converted_CSV')

# Configurações de CSV
ENCODINGS: tuple[str, ...] = ('utf-8', 'ISO-8859-1', 'cp1252')
CHUNK_SIZE: int = 100_000
MAX_FILES: int = 100
MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB
MAX_RETRIES: int = 3
LOW_RAM_THRESHOLD: int = 3 * 1024 * 1024 * 1024  # 3GB
CHUNK_SUPPORTED_FORMATS: set[str] = {'parquet', 'h5', 'json'}

# Configurações de UI
UI_CONFIG = {
    "WINDOW_WIDTH": 800,
    "WINDOW_HEIGHT": 600,
    "LIST_HEIGHT": 150,
    "TOOLTIP_DELAY": 500,
    "TOOLTIP_BG": '#f0f0f0',
    "TOOLTIP_OFFSET": (25, 25)
}

# URLs e Créditos
LINKEDIN_URL = "https://www.linkedin.com/in/isllantoso/"
DEV_NAME = "Isllan Toso"
