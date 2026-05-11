import logging
import sys
from pathlib import Path

def setup_logging(level: int = logging.INFO) -> None:
    """Configura o sistema de logging global."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Poderia adicionar um FileHandler aqui se necessário
        ]
    )

    # Silenciar logs de terceiros se necessário
    # logging.getLogger("matplotlib").setLevel(logging.WARNING)
