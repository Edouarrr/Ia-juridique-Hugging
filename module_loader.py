import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict

logger = logging.getLogger(__name__)


def get_available_modules(group_by_type: bool = False) -> Dict[str, ModuleType]:
    """Scan the ``modules`` folder and load modules exposing ``run``.

    Parameters
    ----------
    group_by_type : bool, optional
        If True, modules are grouped by their ``TYPE`` attribute when present.

    Returns
    -------
    Dict[str, ModuleType]
        Mapping of module name to module object. When ``group_by_type`` is
        True the dictionary contains nested mappings keyed by type.
    """
    modules_dir = Path(__file__).parent / "modules"
    if not modules_dir.exists():
        logger.warning("Module directory not found: %s", modules_dir)
        return {}

    loaded: Dict[str, ModuleType] = {}
    grouped: Dict[str, Dict[str, ModuleType]] = {}

    for py_file in modules_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(f"modules.{name}", py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)  # type: ignore
                if callable(getattr(mod, "run", None)):
                    loaded[name] = mod
                    if group_by_type:
                        m_type = getattr(mod, "TYPE", name.split("_")[0])
                        grouped.setdefault(m_type, {})[name] = mod
        except Exception as exc:
            logger.warning("Failed to load module %s: %s", name, exc)

    return grouped if group_by_type else loaded
