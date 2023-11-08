from cx_Freeze import setup, Executable
import os
import configparser
from datetime import datetime

__current_dir__ = os.path.dirname(os.path.realpath(__file__))

build_exe_options = {
    "packages": ["stresstester"],
    "include_files": ["config.ini", "config_en.ini"],
    "include_msvcr": True,
    "optimize": 2,
    "build_exe": os.path.join(__current_dir__, "dist"),
}

# parse config
conf = configparser.ConfigParser()
conf.read(os.path.join(__current_dir__, "config.ini"))

__name__ = conf["global"]["title"]
__version__ = conf["global"]["version"].format(
    date=datetime.now().strftime("%y%m%d"),
)

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
)

if os.path.exists(os.path.join(__current_dir__, "dist")):
    # create a zip file
    import zipfile
    zf = zipfile.ZipFile(os.path.join(__current_dir__, f"{__name__}v{__version__}.zip"), "w", zipfile.ZIP_DEFLATED)
    # copy everything in dist to zip file
    for root, dirs, files in os.walk(os.path.join(__current_dir__, "dist")):
        for file in files:
            zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(__current_dir__, "dist")))
    zf.close()
