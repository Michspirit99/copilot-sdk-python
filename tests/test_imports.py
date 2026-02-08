from __future__ import annotations

import importlib.util
from pathlib import Path


def _import_module_from_path(py_file: Path) -> None:
    module_name = f"samples_{py_file.stem}"
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def test_samples_import_cleanly() -> None:
    """Import each sample script to catch missing deps / syntax errors.

    These scripts should be safe to import because they guard runtime work
    with `if __name__ == "__main__":`.
    """
    repo_root = Path(__file__).resolve().parents[1]
    samples_dir = repo_root / "samples"

    py_files = sorted(p for p in samples_dir.glob("*.py") if not p.name.startswith("_"))
    assert py_files, "No sample files found"

    for py_file in py_files:
        _import_module_from_path(py_file)
