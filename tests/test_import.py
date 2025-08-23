def test_import():
    import spyglass
    assert hasattr(spyglass, "__version__")
