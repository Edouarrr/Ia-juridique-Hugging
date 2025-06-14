"""Initialisation des modules de l'application."""

from __future__ import annotations

import importlib
import logging
import sys
from typing import Any, Dict

from utils.logging import decorate_public_functions, setup_logger

logger = setup_logger(__name__)

__all__ = [
    "ComparisonModule",
    "TimelineModule",
    "ExtractionModule",
    "StrategyModule",
    "ReportModule",
    "get_modules_status",
]

AVAILABLE_MODULES = {
    "comparison": "ComparisonModule",
    "timeline": "TimelineModule",
    "extraction": "ExtractionModule",
    "strategy": "StrategyModule",
    "report": "ReportModule",
}

try:
    from .module_registry import REGISTERED_MODULES
except Exception:  # pragma: no cover - registry may not exist yet
    REGISTERED_MODULES = []

_import_status = {"loaded": [], "failed": {}}

for module_name, class_name in AVAILABLE_MODULES.items():
    try:
        module = importlib.import_module(f".{module_name}", package=__package__)
        decorate_public_functions(module)
        # Extraire la classe et l'ajouter au namespace
        if hasattr(module, class_name):
            globals()[class_name] = getattr(module, class_name)
            _import_status["loaded"].append(class_name)
            logger.info("✅ Module chargé : %s", class_name)
        else:
            raise AttributeError(f"Classe {class_name} manquante")
    except Exception as e:  # noqa: BLE001 - logging visible errors is enough
        error_msg = str(e)
        _import_status["failed"][class_name] = error_msg
        logger.warning("⚠️  %s - %s", class_name, error_msg)
        globals()[class_name] = type(class_name, (), {"available": False, "error": error_msg})

for mod in REGISTERED_MODULES:
    try:
        importlib.import_module(f".{mod}", package=__package__)
        logger.info("✅ Module utilitaire chargé : %s", mod)
    except Exception as e:  # pragma: no cover - best effort
        logger.warning("⚠️  Impossible de charger %s: %s", mod, e)


def get_modules_status() -> Dict[str, Any]:
    return {
        "total_modules": len(AVAILABLE_MODULES),
        "loaded_count": len(_import_status["loaded"]),
        "failed_count": len(_import_status["failed"]),
        "loaded": _import_status["loaded"],
        "failed": _import_status["failed"],
        "available_modules": AVAILABLE_MODULES,
        "registered_helpers": REGISTERED_MODULES,
    }


def test_modules() -> Dict[str, Any]:
    status = get_modules_status()
    print("\n📊 Statut des Modules :")
    print(f"Total : {status['total_modules']}")
    print(f"Chargés : {status['loaded_count']} ✅")
    print(f"Échoués : {status['failed_count']} ❌")
    if status["registered_helpers"]:
        print("\nModules utilitaires :")
        for mod in status["registered_helpers"]:
            print(f"  - {mod}")
    return status

decorate_public_functions(sys.modules[__name__])
if __name__ == "__main__":  # pragma: no cover - manual test
    test_modules()

# Test automatique si exécuté directement
decorate_public_functions(sys.modules[__name__])

if __name__ == "__main__":
    test_modules()
