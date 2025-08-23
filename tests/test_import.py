import importlib


def test_import() -> None:
    spyglass = importlib.import_module("spyglass")
    assert hasattr(spyglass, "__version__")
