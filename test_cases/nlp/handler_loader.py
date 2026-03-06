import importlib
import pkgutil
import message_handlers  # this is the package directory: message_handlers/


def load_message_handlers() -> None:
    """
    Imports every module in message_handlers/ so their decorators run and register.
    """
    for _, module_name, _ in pkgutil.iter_modules(message_handlers.__path__):
        importlib.import_module(f"message_handlers.{module_name}")