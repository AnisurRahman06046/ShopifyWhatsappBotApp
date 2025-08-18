# app/core/model_loader.py
import importlib
from pathlib import Path


def auto_import_models(
    base_path: Path, base_module: str, match_suffix="_models.py"
) -> None:
    for module_file in base_path.rglob("*.py"):
        if module_file.name.startswith("__") or not module_file.name.endswith(
            match_suffix
        ):
            continue

        # Build full module string with base_module prefix
        module_str = f"{base_module}." + ".".join(
            module_file.relative_to(base_path).with_suffix("").parts
        )

        # Debug print (optional):
        # print("Importing:", module_str)

        importlib.import_module(module_str)
