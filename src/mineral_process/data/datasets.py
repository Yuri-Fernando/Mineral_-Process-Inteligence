"""Download public datasets and preserve an auditable provenance manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class DatasetFile:
    dataset: str
    source_url: str
    path: str
    sha256: str
    size_bytes: int
    downloaded_at: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> DatasetFile:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mineral-Process-Intelligence/0.1"}
    )
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target)
    return DatasetFile(
        dataset=destination.parent.name,
        source_url=url,
        path=destination.as_posix(),
        sha256=sha256_file(destination),
        size_bytes=destination.stat().st_size,
        downloaded_at=datetime.now(timezone.utc).isoformat(),
    )


def download_geomet(root: Path = Path("data/raw/geomet")) -> list[DatasetFile]:
    base = "https://zenodo.org/records/7051975/files"
    return [
        _download(f"{base}/{name}?download=1", root / name)
        for name in ("drillholes.csv", "comminution.csv", "flotation.csv")
    ]


def download_polymetallic(root: Path = Path("data/raw/polymetallic")) -> list[DatasetFile]:
    url = "https://zenodo.org/records/22773521/files/Base%20de%20datos.xlsx?download=1"
    return [_download(url, root / "Base de datos.xlsx")]


def download_iron_flotation(root: Path = Path("data/raw/iron_flotation")) -> list[DatasetFile]:
    """Use Kaggle's public dataset endpoint; credentials may still be required upstream."""
    url = (
        "https://www.kaggle.com/api/v1/datasets/download/edumagalhaes/"
        "quality-prediction-in-a-mining-process"
    )
    archive = root / "quality-prediction-in-a-mining-process.zip"
    record = _download(url, archive)
    with zipfile.ZipFile(archive) as bundle:
        safe_members = [
            m
            for m in bundle.infolist()
            if not Path(m.filename).is_absolute() and ".." not in Path(m.filename).parts
        ]
        bundle.extractall(root, members=safe_members)
    return [record]


def write_manifest(
    records: list[DatasetFile], path: Path = Path("data/raw/provenance.json")
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "files": [asdict(record) for record in records]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def download_all() -> tuple[list[DatasetFile], dict[str, str]]:
    records: list[DatasetFile] = []
    failures: dict[str, str] = {}
    for name, downloader in (
        ("geomet", download_geomet),
        ("polymetallic", download_polymetallic),
        ("iron_flotation", download_iron_flotation),
    ):
        try:
            records.extend(downloader())
        except Exception as exc:  # preserve partial success and exact upstream error
            failures[name] = f"{type(exc).__name__}: {exc}"
    write_manifest(records)
    Path("data/raw/download_failures.json").write_text(
        json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return records, failures
