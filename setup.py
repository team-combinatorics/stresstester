from cx_Freeze import setup, Executable
import os
import configparser
from datetime import datetime
from setuptools import Command
import shutil
from glob import glob

def get_latest_commit(n=7):
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:n]
    except:
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

build_exe_options = {
    "packages": ["stresstester"],
    "include_files": ["config.ini", "config_en.ini"],
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


class Pack(Command):
    description = "Pack the dist directory into a zip file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
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
    options={"build_exe": build_exe_options},
    executables=[Executable(
        "entrypoint.py",
        target_name="电脑小队系统测试工具.exe",
        base="Win32GUI",
        uac_admin=True,
        icon=os.path.join(__current_dir__, "stresstester", "icon.ico")
    )],
    cmdclass={
        'clean': Clean,
        'pack': Pack,
    },
)
