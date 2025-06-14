import importlib
import pkgutil
import pytest

import modules

MODULE_NAMES = [name for _, name, _ in pkgutil.iter_modules(modules.__path__)]


@pytest.mark.parametrize("module_name", MODULE_NAMES)
def test_module_imports(module_name):
    try:
        importlib.import_module(f"modules.{module_name}")
    except ModuleNotFoundError as exc:
        pytest.skip(f"Missing dependency for {module_name}: {exc}")
