# conda-pypi-channel

EXPERIMENTAL.

Sets an ephemeral channel that knows how to fetch PyPI wheels and generate `repodata.json` files on the fly.

Needs the magic URL `http://localhost:8000/conda-pypi-channel` to be enabled.
PyPI wheels need to be prefixed with `:pypi:`. Example:

```
$ pixi run conda create -d -c http://localhost:8000/conda-pypi-channel python :pypi:niquests
Detected conda-pypi-channel! Starting server...
INFO:     Started server process [94261]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
Channels:
 - http://localhost:8000/conda-pypi-channel
 - defaults
Platform: osx-arm64
niquests:   0%|                       00:00, ? wheels/s]
jh2: 100%|█████████████████████████████████| 6/6 [00:06<00:00,  1.16s/it, version=5.0.4]
done
Solving environment: done

## Package Plan ##

  environment location: /var/folders/1b/z374sygs1s96t_xxxv0hr3lr0000gn/T/tmpq7_8h8t2/unused-env-name

  added / updated specs:
    - niquests
    - python


The following packages will be downloaded:

    package                    |               build
    ---------------------------|--------------------
    bzip2-1.0.8                |        h80987f9_6      129 KB  defaults
    ca-certificates-2025.9.9   |        hca03da5_0      127 KB  defaults
    charset-normalizer-3.4.3   | pypi_py3_none_any_0     52 KB  http://localhost:8000/conda-pypi-channel
    expat-2.7.1                |        h313beb8_0      156 KB  defaults
    h11-0.16.0                 | pypi_py3_none_any_0     37 KB  http://localhost:8000/conda-pypi-channel
    jh2-5.0.9                  | pypi_py3_none_any_0     96 KB  http://localhost:8000/conda-pypi-channel
    libcxx-20.1.8              |        h8869778_0      351 KB  defaults
    libffi-3.4.4               |        hca03da5_1      120 KB  defaults
    libmpdec-4.0.0             |        h80987f9_0       69 KB  defaults
    libzlib-1.3.1              |        h5f15de7_0       47 KB  defaults
    ncurses-6.5                |        hee39554_0      886 KB  defaults
    niquests-3.15.2            | pypi_py3_none_any_0    163 KB  http://localhost:8000/conda-pypi-channel
    openssl-3.0.17             |        h4ee41c1_0      4.3 MB  defaults
    pip-25.2                   |      pyhc872135_0      1.2 MB  defaults
    python-3.13.7              | hc28b8d9_100_cp313    12.7 MB  defaults
    python_abi-3.13            |           1_cp313        6 KB  defaults
    readline-8.3               |        h0b18652_0      464 KB  defaults
    setuptools-78.1.1          |   py313hca03da5_0      2.2 MB  defaults
    sqlite-3.50.2              |        h79febb2_1      1.0 MB  defaults
    tk-8.6.15                  |        hcd8a7d5_0      3.3 MB  defaults
    tzdata-2025b               |        h04d1e81_0      116 KB  defaults
    urllib3-future-2.13.909    | pypi_py3_none_any_0    659 KB  http://localhost:8000/conda-pypi-channel
    wassima-2.0.1              | pypi_py3_none_any_0    142 KB  http://localhost:8000/conda-pypi-channel
    wheel-0.45.1               |   py313hca03da5_0      145 KB  defaults
    xz-5.6.4                   |        h80987f9_1      289 KB  defaults
    zlib-1.3.1                 |        h5f15de7_0       77 KB  defaults
    ----------------------------------------------------------
                                           Total:      28.7 MB

The following NEW packages will be INSTALLED:

  bzip2              pkgs/main/osx-arm64::bzip2-1.0.8-h80987f9_6
  ca-certificates    pkgs/main/osx-arm64::ca-certificates-2025.9.9-hca03da5_0
  charset-normalizer conda-pypi-channel/noarch::charset-normalizer-3.4.3-pypi_py3_none_any_0
  expat              pkgs/main/osx-arm64::expat-2.7.1-h313beb8_0
  h11                conda-pypi-channel/noarch::h11-0.16.0-pypi_py3_none_any_0
  jh2                conda-pypi-channel/noarch::jh2-5.0.9-pypi_py3_none_any_0
  libcxx             pkgs/main/osx-arm64::libcxx-20.1.8-h8869778_0
  libffi             pkgs/main/osx-arm64::libffi-3.4.4-hca03da5_1
  libmpdec           pkgs/main/osx-arm64::libmpdec-4.0.0-h80987f9_0
  libzlib            pkgs/main/osx-arm64::libzlib-1.3.1-h5f15de7_0
  ncurses            pkgs/main/osx-arm64::ncurses-6.5-hee39554_0
  niquests           conda-pypi-channel/noarch::niquests-3.15.2-pypi_py3_none_any_0
  openssl            pkgs/main/osx-arm64::openssl-3.0.17-h4ee41c1_0
  pip                pkgs/main/noarch::pip-25.2-pyhc872135_0
  python             pkgs/main/osx-arm64::python-3.13.7-hc28b8d9_100_cp313
  python_abi         pkgs/main/osx-arm64::python_abi-3.13-1_cp313
  readline           pkgs/main/osx-arm64::readline-8.3-h0b18652_0
  setuptools         pkgs/main/osx-arm64::setuptools-78.1.1-py313hca03da5_0
  sqlite             pkgs/main/osx-arm64::sqlite-3.50.2-h79febb2_1
  tk                 pkgs/main/osx-arm64::tk-8.6.15-hcd8a7d5_0
  tzdata             pkgs/main/noarch::tzdata-2025b-h04d1e81_0
  urllib3-future     conda-pypi-channel/noarch::urllib3-future-2.13.909-pypi_py3_none_any_0
  wassima            conda-pypi-channel/noarch::wassima-2.0.1-pypi_py3_none_any_0
  wheel              pkgs/main/osx-arm64::wheel-0.45.1-py313hca03da5_0
  xz                 pkgs/main/osx-arm64::xz-5.6.4-h80987f9_1
  zlib               pkgs/main/osx-arm64::zlib-1.3.1-h5f15de7_0



DryRunExit: Dry run. Exiting.

Shutting down server...
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [94261]
```
