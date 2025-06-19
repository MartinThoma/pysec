import importlib
import os
import pkgutil

from pysec.osbase import BaseSecurityChecker


def _find_checker_class() -> type[BaseSecurityChecker] | None:
    """Search for a checker class matching the current OS."""
    package_path = os.path.dirname(__file__)  # noqa: PTH120
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        full_module_name = f"{__name__}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except ImportError:
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseSecurityChecker)
                and attr is not BaseSecurityChecker
            ) and attr.is_current_os():
                return attr
    return None


def get_checker() -> BaseSecurityChecker | None:
    """Return an instance of the appropriate security checker."""
    checker_cls = _find_checker_class()
    return checker_cls() if checker_cls else None
