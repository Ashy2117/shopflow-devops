import importlib.util
from pathlib import Path

def test_catalog_has_products():
    path = Path(__file__).parents[1] / "services" / "catalog" / "app.py"
    spec = importlib.util.spec_from_file_location("catalog_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.products()
    assert result["count"] >= 1
    assert result["items"][0]["id"].startswith("sku-")
