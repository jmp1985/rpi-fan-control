#
# Copyright (C) 2019 James Parkhurst
#
# This code is distributed under the BSD license.
#
import os
import subprocess
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install


class InstallCommand(install):
    """
    Install the systemd service

    """

    def run(self):
        
        # Do basic install
        install.run(self)

        # Copy the service file to the systemd directory
        directory = os.path.dirname(os.path.realpath(__file__))
        src = os.path.join(directory, "systemd/rpi-fancontrol.service")
        dst = "/lib/systemd/system"
        shutil.copyfile(src, dst)
        
        # Enable the systemd service
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", "rpi-fancontrol.service"])


def main():
    """
    Setup the package

    """

    setup(
        name="rpi-fancontrol",
        author="James Parkhurst",
        version="0.0.1",
        description="A service to control the fan speed on my Raspberry pi",
        package_dir={"": "src"},
        packages=find_packages(where="src"),
        install_requires=[
            "lgpio",
        ],
        entry_points={
            "console_scripts": [
                "rpi-fancontrol=fancontrol:main",
            ]
        },
        cmdclass={
            "install": InstallCommand
        },
    )


if __name__ == "__main__":
    main()
