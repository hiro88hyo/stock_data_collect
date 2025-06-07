"""Logging configuration for Cloud Logging compatibility."""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class CloudLoggingFormatter(logging.Formatter):
    """Custom formatter for Google Cloud Logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for Cloud Logging."""
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "labels": {
                "component": "stock-data-collector",
                "module": record.module,
                "function": record.funcName
            }
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs", 
                          "pathname", "process", "processName", "relativeCreated",
                          "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                if "labels" not in log_obj:
                    log_obj["labels"] = {}
                log_obj["labels"][key] = str(value)
        
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    # Create logger
    logger = logging.getLogger("stock_data_collector")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Use JSON formatter for production, simple formatter for development
    if sys.stdout.isatty():
        # Development environment (terminal)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        # Production environment (Cloud Logging)
        formatter = CloudLoggingFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Create default logger instance
logger = setup_logging()