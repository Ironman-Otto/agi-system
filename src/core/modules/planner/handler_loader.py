import importlib
import pkgutil

def load_message_handlers() -> None:
    # handler_loader.py lives in package: src.core.modules.nlp
    # so handlers package should be: src.core.modules.nlp.message_handlers
    handlers_pkg_name = f"{__package__}.message_handlers"

    handlers_pkg = importlib.import_module(handlers_pkg_name)

    for _, module_name, _ in pkgutil.iter_modules(handlers_pkg.__path__):
        importlib.import_module(f"{handlers_pkg_name}.{module_name}")
        