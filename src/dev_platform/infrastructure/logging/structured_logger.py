# src/dev_platform/infrastructure/logging/structured_logger.py
import logging
import json
import os
import sys
from datetime import datetime
from application.user.ports import Logger as LoggerPort

class StructuredLogger(LoggerPort):
    def __init__(self, name: str = "DEV Platform", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)
            
            # File handler for errors
            if not os.path.exists('logs'):
                os.makedirs('logs')
            file_handler = logging.FileHandler(f"logs/{datetime.now().strftime('%Y-%m-%d')}.log")
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        if kwargs:
            log_data = {"message": message, **kwargs}
            self.logger.log(level, json.dumps(log_data))
        else:
            self.logger.log(level, message)