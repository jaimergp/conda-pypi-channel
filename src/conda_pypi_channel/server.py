import hashlib
import json
import os
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from uuid import uuid4
from urllib.request import urlretrieve
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .convert import CustomFilenameWheel2CondaConverter
from .repodata import generate_repodata

app = FastAPI(
    title="conda-pypi-channel",
    description="A simple FastAPI app to serve ephemeral conda channels built from wheel metadata.",
    version=__version__,
)

CHANNEL_BASE_DIR = Path(".").resolve()
PAYLOAD_PATH = Path(os.environ.get("ARGPARSE_PAYLOAD_FOR_CONDA_PYPI_CHANNEL", "payload.json"))
if PAYLOAD_PATH.is_file():
    PAYLOAD = json.loads(PAYLOAD_PATH.read_text())
else:
    PAYLOAD = {
        # DEBUGGING ONLY
        "packages": [":pypi:niquests"],
        "target_platform": "osx-arm64",
        "python_version": "3.12",
    }

REPODATA_CACHE = {}
ARTIFACTS_CACHE_DIR = Path(".cache").resolve()
ARTIFACTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_sum(path: str | os.PathLike, algo: Literal["md5", "sha256"]) -> str:
    path = Path(path)

    # FUTURE: Python 3.11+, replace with hashlib.file_digest
    hasher = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(partial(fh.read, 8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@app.get("/conda-pypi-channel/{platform}/repodata.json")
async def get_repodata(platform: str):
    """
    Builds the repodata.json file for a specific platform (e.g., 'noarch', 'linux-64'),
    given some PyPI package names
    """
    repodata = {
        "info": {"subdir": platform},
        "packages": {},
        "packages.conda": {},
        "removed": [],
        "repodata_version": 1,
    }
    if platform != "noarch":
        return repodata

    pypi_specs = [pkg[6:] for pkg in PAYLOAD.get("packages") if pkg.startswith(":pypi:")]
    key = (*pypi_specs, PAYLOAD["target_platform"], PAYLOAD["python_version"])
    global REPODATA_CACHE
    repodatas = REPODATA_CACHE.get(key)
    if not repodatas:
        REPODATA_CACHE[key] = repodatas = await generate_repodata(
            *pypi_specs,
            target_platform=PAYLOAD["target_platform"],
            python_version=PAYLOAD["python_version"],
        )

    return JSONResponse(
        content=repodatas[platform],
        # Mark as expired to skip cache
        headers={
            # "cache_control": "public, max-age=0",
            "expires": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S %Z"),
            "etag": f'"{uuid4().hex}"',
            "last-modified": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S %Z"),
        },
    )


@app.get("/conda-pypi-channel/{platform}/{package_path:path}")
async def get_package(platform: str, package_path: str):
    """
    Convert wheel on the fly and return as a .conda package.
    """
    packages_key = "packages.conda" if package_path.endswith(".conda") else "packages"
    conda_download_path = ARTIFACTS_CACHE_DIR / package_path
    if not conda_download_path.is_file():
        for cache in REPODATA_CACHE.values():
            if record := cache.get(platform, {}).get(packages_key, {}).get(package_path):
                whl_path = ARTIFACTS_CACHE_DIR / record["url"].split("/")[-1]
                urlretrieve(record["url"], whl_path)
                if compute_sum(whl_path, "sha256") != record["legacy_sha256"]:
                    continue
                w2c = CustomFilenameWheel2CondaConverter(whl_path, ARTIFACTS_CACHE_DIR)
                w2c.custom_conda_pkg_file = package_path
                w2c.convert()
                break
        else:
            raise HTTPException(404, detail="Package not found")
    return FileResponse(
        conda_download_path,
        media_type="application/octet-stream",
        filename=package_path,
    )


@app.get("/conda-pypi-channel")
@app.get("/")
async def root():
    """
    A simple health check endpoint.
    """
    return {"status": "ok", "message": "conda-pypi-channel server is running."}
