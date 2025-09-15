from pathlib import Path

from whl2conda.api.converter import Wheel2CondaConverter


class CustomFilenameWheel2CondaConverter(Wheel2CondaConverter):
    custom_conda_pkg_file: str | None = None

    def _conda_package_path(self, package_name: str, version: str):
        if self.custom_conda_pkg_file:
            return Path(self.out_dir).joinpath(self.custom_conda_pkg_file)
        return super()._conda_package_path(package_name, version)
