import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Formatting
log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name, log_file=None, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = RotatingFileHandler(
            os.path.join("logs", log_file), 
            maxBytes=10*1024*1024, # 10MB
            backupCount=5
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    return logger

# Pre-defined loggers
server_logger = get_logger("docsai.server", "server.log")
ingest_logger = get_logger("docsai.ingest", "ingest.log")
llm_logger = get_logger("docsai.llm", "server.log")
