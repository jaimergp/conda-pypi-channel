import atexit
import json
import logging
import os
import sys
import time
from subprocess import Popen
from tempfile import NamedTemporaryFile

import conda.gateways.connection.download
from conda import plugins
from conda.base.context import context
from conda.core.prefix_data import PrefixData
from conda.gateways.connection.download import download_inner

process: Popen | None = None
log = logging.getLogger(f"conda.{__name__}")


def start_channel(command=None):
    patch_download()
    start = any(
        channel == "http://localhost:8000/conda-pypi-channel" for channel in context.channels
    )
    if not start:
        return
    log.info("Detected conda-pypi-channel! Starting server...")
    global process

    payload = vars(context._argparse_args)
    payload["target_platform"] = context.subdir
    python = PrefixData(context.target_prefix).get("python", None)
    if python:
        payload["python_version"] = python.version
    else:
        payload["python_version"] = "3.12"

    with NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(context._argparse_args, f)
    atexit.register(os.unlink, f.name)
    env = os.environ.copy()
    env["ARGPARSE_PAYLOAD_FOR_CONDA_PYPI_CHANNEL"] = f.name
    env["CONDA_PYPI_CHANNEL_VERBOSITY"] = f"{context.verbosity}"
    log_level = ["warning", "warning", "info", "debug", "debug"][context.verbosity]
    process = Popen(
        ["uvicorn", "conda_pypi_channel.server:app", "--log-level", log_level], env=env
    )
    time.sleep(1)  # wait a bit to let server start; TODO: poll for sentinel output


def patch_download():
    # We need to skip size checks for size=0. This can be done by forcing it to be None.
    def patched_download_inner(
        url,
        target_full_path,
        md5=None,
        sha256=None,
        size=None,
        progress_update_callback=None,
    ):
        size = size or None
        return download_inner(
            url,
            target_full_path,
            md5=md5,
            sha256=sha256,
            size=size,
            progress_update_callback=progress_update_callback,
        )

    sys.modules["conda.gateways.connection.download"].download_inner = patched_download_inner
    conda.gateways.connection.download.download_inner = patched_download_inner


def shutdown_channel(command=None):
    global process
    if process:
        log.info("Stopping conda-pypi-channel server...")
        process.terminate()
        process.wait(timeout=5)


atexit.register(shutdown_channel)


@plugins.hookimpl
def conda_pre_commands():
    yield plugins.CondaPreCommand(
        name="conda-pypi-channel-up",
        action=start_channel,
        run_for={"install", "create", "update", "remove"},
    )


@plugins.hookimpl
def conda_post_commands():
    yield plugins.CondaPostCommand(
        name="conda-pypi-channel-down",
        action=shutdown_channel,
        run_for={"install", "create", "update", "remove"},
    )
