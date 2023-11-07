from cx_Freeze import setup, Executable
import os

__name__ = "电脑小队系统测试工具"
__version__ = "2023.11"
__current_dir__ = os.path.dirname(os.path.realpath(__file__))

build_exe_options = {
    "include_files": ["stresstester"],
    "packages": ["stresstester"],
    "include_msvcr": True,
    "optimize": 2,
    "build_exe": os.path.join(__current_dir__, "dist"),
}

setup(
    name=__name__,
    version=__version__,
    options={"build_exe": build_exe_options},
    executables=[Executable("entrypoint.py", target_name="电脑小队系统测试工具.exe", base="Win32GUI", uac_admin=True, icon=os.path.join(__current_dir__, "stresstester", "icon.ico"))],
)

if os.path.exists(os.path.join(__current_dir__, "dist", "stresstester")):
    # create a zip file
    import zipfile
    zf = zipfile.ZipFile(os.path.join(__current_dir__, f"{__name__}v{__version__}.zip"), "w", zipfile.ZIP_DEFLATED)
    # copy everything in dist to zip file
    for root, dirs, files in os.walk(os.path.join(__current_dir__, "dist")):
        for file in files:
            zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(__current_dir__, "dist")))
    zf.close()
