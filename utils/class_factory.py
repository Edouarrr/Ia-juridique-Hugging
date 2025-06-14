"""Utility functions for creating placeholder classes."""

from __future__ import annotations

from typing import Optional, Callable
import logging


def create_placeholder_class(
    name: str,
    error_msg: str,
    logger: Optional[logging.Logger] = None,
    warn_on_attr: bool = False,
) -> type:
    """Return a simple placeholder class for failed imports.

    Parameters
    ----------
    name: str
        The name of the placeholder class.
    error_msg: str
        Error message describing why the real class is unavailable.
    logger: Optional[logging.Logger]
        Optional logger used to emit warnings during instantiation or
        attribute access.
    warn_on_attr: bool
        If True, calls to undefined attributes emit warnings and return a
        dummy callable.
    """

    def __init__(self, *args, **kwargs):
        self.connected = False
        self.error = error_msg
        self.available = False
        if logger is not None:
            logger.warning("Utilisation du placeholder pour %s", name)

    attrs = {"__init__": __init__, "available": False, "error": error_msg}

    if warn_on_attr:
        def __getattr__(self, attr: str) -> Callable:
            if logger is not None:
                logger.warning(
                    "Tentative d'accès à %s sur %s non disponible", attr, name
                )
            return lambda *args, **kwargs: None

        attrs["__getattr__"] = __getattr__

    return type(name, (), attrs)

__all__ = ["create_placeholder_class"]
