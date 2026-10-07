"""Execute every tutorial notebook and persist its outputs in place."""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "output" / "jupyter-notebook"


def execute_notebook(path: Path, *, kernel_name: str, timeout: int) -> tuple[int, int]:
    """Execute one notebook from the repository root and return cell/output counts."""
    notebook = nbformat.read(path, as_version=4)
    notebook.setdefault("metadata", {}).setdefault("kernelspec", {})["name"] = kernel_name
    notebook["metadata"]["kernelspec"]["display_name"] = (
        "Python 3.12 (Mineral Process Intelligence)"
    )
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name=kernel_name,
        resources={"metadata": {"path": str(ROOT)}},
        allow_errors=False,
    )
    client.execute()
    nbformat.write(notebook, path)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    output_count = sum(len(cell.get("outputs", [])) for cell in code_cells)
    return len(code_cells), output_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", default="mineral-process-py312")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    notebooks = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    if not notebooks:
        raise SystemExit(f"No notebooks found under {NOTEBOOK_DIR}")

    for path in notebooks:
        cells, outputs = execute_notebook(path, kernel_name=args.kernel, timeout=args.timeout)
        print(f"executed {path.relative_to(ROOT)}: {cells} code cells, {outputs} outputs")


if __name__ == "__main__":
    main()
