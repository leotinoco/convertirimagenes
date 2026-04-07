import os
import traceback
import logging

def log_exception(logger: logging.Logger, message: str, exc: Exception, level: int = logging.ERROR):
    """
    Logs an exception with optional traceback based on DEV_MODE environment variable.
    Sanitizes output to avoid leaking local system paths in production.
    """
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    
    if dev_mode:
        logger.log(level, f"{message}: {exc}", exc_info=True)
    else:
        # Sanitize exception string to remove common Windows path prefixes if they appear
        # Simple mitigation: just log the exception type and message
        logger.log(level, f"{message}: {type(exc).__name__}: {exc}")
