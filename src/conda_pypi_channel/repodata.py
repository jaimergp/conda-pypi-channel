"""
Generates repodata.json from a set of PyPI requirements.
"""

import asyncio
from asyncio.queues import Queue
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import lru_cache
from datetime import datetime
from typing import Any, AsyncGenerator

import httpx
from async_lru import alru_cache
from packaging.metadata import Metadata
from packaging.requirements import Requirement
from packaging.tags import parse_tag
from packaging.version import Version

PYPI_INDEX_URL = "https://pypi.org/pypi/{package_name}/json"
MAX_RELEASES_PER_PACKAGE = 5


@lru_cache(maxsize=256)
async def _fetch_releases_for_package_name(package: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.get(PYPI_INDEX_URL.format(package_name=package))
    r.raise_for_status()
    return r.json()["releases"].items()


@alru_cache(maxsize=1024)
async def _fetch_metadata_for_wheel(url: str) -> Metadata:
    async with httpx.AsyncClient() as client:
        r = await client.get(url + ".metadata")
    r.raise_for_status()
    metadata = Metadata.from_email(r.text, validate=False)
    metadata.description = ""
    return metadata


@dataclass
class SystemLowerBounds:
    osx: str = "10.9"
    glibc: str = "2.17"
    win: str = ""


async def wheels_for_requirement(
    requirement: Requirement,
    target_platform: str,
    system_lower_bounds: SystemLowerBounds | None = None,
    python_version: str = "3.9",
) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
    if system_lower_bounds is None:
        system_lower_bounds = SystemLowerBounds()
    release_count = 0
    for version, releases in sorted(
        await _fetch_releases_for_package_name(requirement.name),
        key=lambda kv: Version(kv[0]),
        reverse=True,
    ):
        if release_count > MAX_RELEASES_PER_PACKAGE:
            break
        if requirement.specifier and not requirement.specifier.contains(version):
            continue
        bump_release_count = False
        for distribution in releases:
            if distribution["url"].endswith(".whl"):
                filename = distribution["filename"][: -len(".whl")]
                tags = "-".join(filename.split("-")[-3:])
                if _tags_match(tags, target_platform, system_lower_bounds, python_version):
                    yield version, distribution
                    bump_release_count = True
        if bump_release_count:
            release_count += 1
            if not requirement.specifier:
                # name-only request, assume latest wanted
                break


def distribution_to_record(distribution: dict[str, Any]) -> dict[str, Any]:
    python_requires = "python"
    if distribution["requires_python"]:
        python_requires += f" {distribution['requires_python']}"
    timestamp = int(
        datetime.fromisoformat(distribution["upload_time_iso_8601"]).timestamp() * 1000
    )
    return {
        "size": None,
        "legacy_size": distribution.get("size", 0),
        "timestamp": timestamp,
        "md5": None,
        "legacy_md5": distribution["digests"]["md5"],
        "sha256": None,
        "legacy_sha256": distribution["digests"]["sha256"],
        "depends": [python_requires],
        "url": distribution["url"],
    }


def requires_dist_to_depends(requires_dist: Iterable[Requirement]) -> Iterator[str]:
    for req in requires_dist or ():
        if not req.marker and not req.extras:  # TODO: Support markers and extras
            yield f"{req.name} {req.specifier}"  # TODO: Map to conda package names?


def metadata_to_record(metadata: Metadata) -> dict[str, Any]:
    return {
        "license": metadata.license_expression or (metadata.license or "N/A").splitlines()[0],
    }


def _platform_tag_to_subdir(platform: str) -> str:
    if platform == "any":
        return "noarch"
    if "win" in platform:
        return "win-64"
    if "macosx" in platform:
        return "osx-64"  # TODO: osx-arm64
    if "linux" in platform:
        return "linux-64"  # TODO: other linux archs
    raise ValueError(f"Unknown platform {platform}")


def _tag_platform_match(
    tag_platform: str,
    target_platform: str,
    system_lower_bounds: SystemLowerBounds | None = None,
) -> bool:
    if tag_platform == "any":
        return True
    target_os, target_arch = target_platform.split("-")
    if target_arch == "64":
        target_arch = "x86_64"
    if target_os == "linux":
        system_lower_bound = system_lower_bounds.glibc
        if "manylinux" not in tag_platform:
            return False
        if tag_platform.startswith("manylinux1_"):
            tag_lower_bound = "2.5"
            arch = tag_platform.split("_", 1)[1]
        elif tag_platform.startswith("manylinux2010_"):
            tag_lower_bound = "2.12"
            arch = tag_platform.split("_", 1)[1]
        elif tag_platform.startswith("manylinux2014_"):
            tag_lower_bound = "2.17"
            arch = tag_platform.split("_", 1)[1]
        else:
            _, major, minor, arch = tag_platform.split("_", 3)
            tag_lower_bound = f"{major}.{minor}"
    elif target_os == "osx":
        system_lower_bound = system_lower_bounds.osx
        _, major, minor, arch = tag_platform.split("_", 3)
        tag_lower_bound = f"{major}.{minor}"
    elif target_os == "win":
        arch = "x86_64"  # TODO: Handle arm64
    else:
        raise ValueError(f"Unknown target_platform {target_platform}.")

    if target_arch != arch and not target_arch.startswith("universal"):
        return False
    if Version(system_lower_bound) < Version(tag_lower_bound):
        return False
    return True


def _tags_match(
    tags: str,
    target_platform: str,
    system_lower_bounds: SystemLowerBounds | None = None,
    python_version: str = "3.9",
) -> bool:
    for tag in parse_tag(tags):
        if not tag.interpreter.startswith(("py", "cp")):
            # Ignore if not CPython, for now (TODO)
            continue
        pyver = tag.interpreter[2:]  # remove py or cp
        if len(pyver) == 1 and pyver[0] != python_version[0]:
            continue
        if len(pyver) > 1 and Version(f"{pyver[0]}.{pyver[1:]}") != Version(python_version):
            continue
        if _platform_tag_to_subdir(tag.platform) not in (target_platform, "noarch"):
            continue
        if not _tag_platform_match(tag.platform, target_platform, system_lower_bounds):
            continue
        return True
    return False


def tag_to_record(tag_str: str, record: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_tag(tag_str)
    for tag in parsed:
        platform = tag.platform
        if platform == "any":
            record["subdir"] = "noarch"
            record["noarch"] = "python"
        else:
            record["subdir"] = _platform_tag_to_subdir(platform)


async def create_record(
    name: str, version: str, distribution_metadata: dict[str, Any]
) -> dict[str, Any]:
    filename = distribution_metadata["filename"]
    tag_str = "-".join(filename[: -len(".whl")].rsplit("-", 3)[-3:])
    build_string = "pypi_" + tag_str.replace("-", "_").replace(".", "_") + "_0"
    conda_fn = f"{name}-{version}-{build_string}.conda"
    metadata = await _fetch_metadata_for_wheel(distribution_metadata["url"])
    record = {
        "name": name,
        "version": version,
        "build_number": 0,
        "build": build_string,
        "fn": conda_fn,
        **distribution_to_record(distribution_metadata),
        **metadata_to_record(metadata),
    }
    tag_to_record(tag_str, record)
    record["depends"].extend(requires_dist_to_depends(metadata.requires_dist))
    return record


async def generate_repodata(
    *requirements: str, target_platform: str, python_version: str = "3.9"
) -> dict[str, Any]:
    repodatas = {
        subdir: {
            "info": {"subdir": subdir},
            "packages": {},
            "packages.conda": {},
        }
        for subdir in (target_platform, "noarch")
    }
    queue = Queue()
    for requirement in requirements:
        await queue.put(Requirement(requirement))
    seen = set(["python"])
    while not queue.empty():
        seen_reqs = set()
        requirements = [
            requirement
            for requirement in await asyncio.gather(
                *[queue.get() for _ in range(min([queue.qsize(), 10]))]
            )
            if requirement.name not in seen
        ]

        for record in await asyncio.gather(
            *[
                create_record(requirement.name, version, distribution)
                for requirement in requirements
                async for version, distribution in wheels_for_requirement(
                    requirement,
                    target_platform=target_platform,
                    python_version=python_version,
                )
            ]
        ):
            repodatas[record["subdir"]]["packages.conda"][record["fn"]] = record
            for dep in record["depends"]:
                dep = Requirement(dep)
                if dep.name not in seen and dep.name not in seen_reqs:
                    seen_reqs.add(dep.name)
                    await queue.put(dep)
        seen.update([requirement.name for requirement in requirements])

    return repodatas
