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
