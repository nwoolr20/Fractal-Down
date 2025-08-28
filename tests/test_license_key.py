import importlib


def test_generate_and_verify_license(tmp_path, monkeypatch):
    license_path = tmp_path / "licenses.json"
    monkeypatch.setenv("FRACTAL_DOWN_LICENSE_FILE", str(license_path))
    lk = importlib.reload(importlib.import_module("fractal_down.license_key"))

    record = lk.generate_license("contract-123")
    assert record.contract == "contract-123"
    assert lk.verify_license(record.key)
    assert not lk.verify_license("invalid-key")

    data = license_path.read_text()
    assert record.key in data


def test_license_has_feature_with_next(tmp_path, monkeypatch):
    """Test that license_has_feature works correctly with next() implementation."""
    license_path = tmp_path / "licenses.json"
    monkeypatch.setenv("FRACTAL_DOWN_LICENSE_FILE", str(license_path))
    lk = importlib.reload(importlib.import_module("fractal_down.license_key"))

    # Generate license with features
    record = lk.generate_license("contract-456", features=["gpu", "distributed"])
    
    # Test that features are correctly detected
    assert lk.license_has_feature(record.key, "gpu")
    assert lk.license_has_feature(record.key, "distributed")
    assert not lk.license_has_feature(record.key, "visualization")
    
    # Test with invalid key
    assert not lk.license_has_feature("invalid-key", "gpu")
    
    # Test with empty features
    record_empty = lk.generate_license("contract-789", features=[])
    assert not lk.license_has_feature(record_empty.key, "gpu")
