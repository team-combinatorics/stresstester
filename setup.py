import logging
import os
import configparser
from datetime import datetime
from setuptools import Command
import shutil
from glob import glob

from cx_Freeze import setup, Executable


def get_latest_commit(n=7):
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:n]
    except Exception as e:
        logging.exception(e)
        return "unknown"


__current_dir__ = os.path.dirname(os.path.realpath(__file__))
# parse config
conf = configparser.ConfigParser()
conf.read(os.path.join(__current_dir__, "config.ini"))

__name__ = conf["global"]["title"]
__version__ = conf["global"]["version"].format(
    date=datetime.now().strftime("%y%m%d"),
    commit=get_latest_commit(),
)
__author__ = conf["global"]["author"]

_static_files = glob(os.path.join(__current_dir__, "static", "*"))
_config_files = glob(os.path.join(__current_dir__, "*.ini"))

build_exe_options = {
    "packages": ["stresstester"],
    "include_files": _static_files + _config_files,
    "include_msvcr": True,
    "optimize": 2,
    "build_exe": os.path.join(__current_dir__, "dist"),
}


class Clean(Command):
    description = "Clean the build directory"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # delete ignored files recursively
        from gitignore_parser import parse_gitignore
        for dirpath, dirnames, filenames in os.walk(os.path.join(__current_dir__, "stresstester")):
            gitignore_path = os.path.join(dirpath, '.gitignore')
            if os.path.isfile(gitignore_path):
                is_ignored = parse_gitignore(gitignore_path)
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if is_ignored(file_path):
                        os.remove(file_path)
                        print(f"Removed: {file_path}")

        # delete dist
        if os.path.exists(os.path.join(__current_dir__, "dist")):
            shutil.rmtree(os.path.join(__current_dir__, "dist"))
            print(f'Removed: {os.path.join(__current_dir__, "dist")}')

        # delete *.zip
        for f in glob(os.path.join(__current_dir__, "*.zip")):
            os.remove(f)
            print(f"Removed: {f}")


def _patch_readme():
    _readme_path = os.path.join(__current_dir__, "dist", "请先读我README.txt")
    if not os.path.exists(_readme_path):
        return

    try:
        with open(_readme_path, 'r', encoding='utf-8') as f:
            _readme = f.read()
    except UnicodeDecodeError:
        with open(_readme_path, 'r', encoding='gbk') as f:
            _readme = f.read()
    with open(_readme_path, 'w', encoding='gbk') as f:
        f.write(_readme.format(
            version=__version__,
            date=datetime.now().strftime("%Y-%m-%d"),
            commit=get_latest_commit(),
        ))


class Pack(Command):
    description = "Pack the dist directory into a zip file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        _patch_readme()  # a bit late, but it works

        if os.path.exists(os.path.join(__current_dir__, "dist")):
            # create a zip file
            import zipfile
            zf = zipfile.ZipFile(os.path.join(__current_dir__, f"{__name__}v{__version__}.zip"), "w",
                                 zipfile.ZIP_DEFLATED)
            # copy everything in dist to zip file
            for root, dirs, files in os.walk(os.path.join(__current_dir__, "dist")):
                for file in files:
                    zf.write(os.path.join(root, file),
                             os.path.relpath(os.path.join(root, file), os.path.join(__current_dir__, "dist")))
            zf.close()
        print(f"Created {__name__}v{__version__}.zip")


setup(
    name=__name__,
    version=__version__,
    author=__author__,
    options={"build_exe": build_exe_options},
    executables=[Executable(
        "entrypoint.py",
        target_name=__name__ + ".exe",
        base="Win32GUI",
        uac_admin=True,
        icon=os.path.join(__current_dir__, "stresstester", conf["global"]["icon"]),
    )],
    cmdclass={
        'clean': Clean,
        'pack': Pack,
    },
)
