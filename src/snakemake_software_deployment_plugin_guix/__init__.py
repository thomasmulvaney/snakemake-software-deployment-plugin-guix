from typing import Iterable, Optional
import subprocess as sp
from snakemake_interface_software_deployment_plugins import (
    EnvBase,
    EnvSpecBase,
    SoftwareReport,
)
from snakemake_interface_common.exceptions import WorkflowError
from snakemake_interface_software_deployment_plugins.settings import CommonSettings

from pathlib import Path

from dataclasses import dataclass

common_settings = CommonSettings(provides="guix")


@dataclass
class EnvSpec(EnvSpecBase):
    # There are a number of ways of specifying the required software
    # but for now using a manifest and channels should be enough.

    # A more minimalistic approach would be to provide git commit and url
    # of channel along with list of packages, which could fairly
    # compactly added inline in a Snakefile.
    manifest: Optional[Path] = None
    channels: Optional[Path] = None

    def identity_attributes(self) -> Iterable[str]:
        return ["manifest", "channels"]

    def source_path_attributes(self) -> Iterable[str]:
        # no paths involved here
        return ()


class Env(EnvBase):
    def __post_init__(self):
        # Check if the module command is available
        self.check()

    @EnvBase.once
    def check(self) -> None:
        if self.run_cmd("type guix", stdout=sp.PIPE, stderr=sp.PIPE).returncode != 0:
            raise WorkflowError(
                "The 'guix' command is not available. "
                "Please make sure that guix is available on your system."
            )

    def decorate_shellcmd(self, cmd: str) -> str:
        # We run guix time-machine to get software at a particular point in time.
        # Then we spawn a shell with the set of packages defined in manifest.
        # There are some additional settings for the shell we may wish users to
        # be able to tune, like running in a isolated container.
        return f"guix time-machine --channels={self.spec.channels} -- shell -m {self.spec.manifest} -- {cmd}"

    def record_hash(self, hash_object) -> None:
        # We should really pretty print these in case their formatting changes
        # before reading them in or use a scheme parser.
        # Or there maybe a useful Guix command for returning something.
        with open(self.spec.channels) as channels_file:
            hash_object.update(channels_file.read())

        with open(self.spec.manifest) as manifest_file:
            hash_object.update(manifest_file.read())

    def report_software(self) -> Iterable[SoftwareReport]:
        # TODO: Figure out best way to report software
        return ()
