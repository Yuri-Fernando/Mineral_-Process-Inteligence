"""Case-study loaders with explicit separation and normalized numeric parsing."""

from pathlib import Path

import pandas as pd


def _normalize_numeric(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.select_dtypes(include="object").columns:
        converted = pd.to_numeric(
            result[column].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
        if converted.notna().mean() > 0.8:
            result[column] = converted
    return result


def load_geomet(root: Path = Path("data/raw/geomet")) -> dict[str, pd.DataFrame]:
    expected = ("drillholes", "comminution", "flotation")
    missing = [name for name in expected if not (root / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"GeoMet files missing: {missing}; run `mpi download-data`")
    return {name: _normalize_numeric(pd.read_csv(root / f"{name}.csv")) for name in expected}


def load_iron_flotation(
    root: Path = Path("data/raw/iron_flotation"), nrows: int | None = None
) -> pd.DataFrame:
    candidates = list(root.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("iron flotation CSV missing; run `mpi download-data`")
    frame = pd.read_csv(candidates[0], decimal=",", nrows=nrows)
    return _normalize_numeric(frame)


def load_polymetallic(root: Path = Path("data/raw/polymetallic")) -> dict[str, pd.DataFrame]:
    path = root / "Base de datos.xlsx"
    if not path.exists():
        raise FileNotFoundError("polymetallic workbook missing; run `mpi download-data`")
    sheets = pd.read_excel(path, sheet_name=None)
    return {name: _normalize_numeric(frame) for name, frame in sheets.items()}
