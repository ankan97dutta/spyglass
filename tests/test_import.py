import importlib


def test_import() -> None:
    profilis = importlib.import_module("profilis")
    assert hasattr(profilis, "__version__")
