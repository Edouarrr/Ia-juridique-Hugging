import logging
from functools import wraps
from types import ModuleType


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Set up and return a logger with basic configuration."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def log_execution(func):
    """Decorator that logs function entry and exit."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug("Entering %s", func.__name__)
        result = func(*args, **kwargs)
        logger.debug("Exiting %s", func.__name__)
        return result

    wrapper._log_decorated = True
    return wrapper


def decorate_public_functions(module: ModuleType) -> None:
    """Apply ``log_execution`` to all public callables of ``module``."""
    for attr_name, attr_value in vars(module).items():
        if callable(attr_value) and not attr_name.startswith("_") and not isinstance(attr_value, type):
            if not getattr(attr_value, "_log_decorated", False):
                setattr(module, attr_name, log_execution(attr_value))
