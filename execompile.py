import os
import sys
import subprocess
import sysconfig
import shutil
import tempfile
import logging
from pathlib import Path
from components.compress import compress_with_upx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

EXE_FOLDER = Path("EXEs")
BUILD_DIR = Path("build_cython")
PY_FILE = Path("components/bootloader.py")
RESOURCE_HACKER_DIR = Path(os.environ["LOCALAPPDATA"]) / "PyCompyle.cache" / "ResourceHacker"
RESOURCE_HACKER_EXE = RESOURCE_HACKER_DIR / "resource_hacker" / "ResourceHacker.exe"
RESOURCE_HACKER_URL = "https://www.angusj.com/resourcehacker/resource_hacker.zip"

def ensure_resource_hacker():
    if RESOURCE_HACKER_EXE.exists():
        return
    logging.info("Downloading Resource Hacker ...")
    import components.download as download  # your module
    download.download_and_extract_zip(RESOURCE_HACKER_URL, extract_to=str(RESOURCE_HACKER_DIR))
    if not RESOURCE_HACKER_EXE.exists():
        logging.error("Failed to get Resource Hacker.")
        sys.exit(1)

def generate_c_file():
    BUILD_DIR.mkdir(exist_ok=True)
    c_file = BUILD_DIR / "bootloader.c"
    if not c_file.exists():
        logging.info(f"Generating C file from {PY_FILE}")
        subprocess.check_call(["cython", "--embed", "-3", "-o", str(c_file), str(PY_FILE)])
    return c_file

def create_win_main_wrapper():
    wrapper = BUILD_DIR / "win_main.c"
    content = """
#ifdef _WIN32
#include <windows.h>
int main(int argc, char **argv);
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    return main(__argc, __argv);
}
#endif
"""
    with open(wrapper, "w", encoding="utf-8") as f:
        f.write(content)
    return wrapper

def compile_exe(c_file, exe_path, windowed=False):
    EXE_FOLDER.mkdir(exist_ok=True)
    include_dir = sysconfig.get_paths()["include"]
    lib_dir = Path(sys.base_prefix) / "libs"
    py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
    python_lib = f"python{py_ver}"

    win_main = create_win_main_wrapper()
    gcc_cmd = [
        "gcc",
        str(win_main),
        str(c_file),
        "-o", str(exe_path),
        f"-I{include_dir}",
        f"-L{lib_dir}",
        f"-l{python_lib}",
        "-static-libgcc",
        "-static-libstdc++"
    ]

    gcc_cmd.append("-mwindows" if windowed else "-mconsole")
    logging.info(f"Compiling {exe_path} ...")
    subprocess.check_call(gcc_cmd)

    # Copy Python DLL next to EXE
    dll_src = Path(sys.base_prefix) / f"python{py_ver}.dll"
    if dll_src.exists():
        shutil.copy(dll_src, EXE_FOLDER)

    logging.info(f"Built {exe_path}")

def cleanup():
    # Remove build folder
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        logging.info(f"Removed build folder {BUILD_DIR}")

    # Remove any Python DLLs in EXEs folder
    for dll in EXE_FOLDER.glob("python*.dll"):
        try:
            dll.unlink()
            logging.info(f"Removed DLL {dll}")
        except Exception as e:
            logging.warning(f"Failed to remove DLL {dll}: {e}")


def embed_manifest(exe_path):
    ensure_resource_hacker()
    manifest_file = Path(tempfile.gettempdir()) / "uac_manifest.xml"
    manifest_file.write_text("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>""", encoding="utf-8")

    cmd = [
        str(RESOURCE_HACKER_EXE),
        "-open", str(exe_path),
        "-save", str(exe_path),
        "-action", "addoverwrite",
        "-res", str(manifest_file),
        "-mask", "MANIFEST,1,"
    ]
    logging.info(f"Embedding manifest into {exe_path} ...")
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

def build_all():
    c_file = generate_c_file()
    variants = [
        ("bootloader.exe", False, False),
        ("bootloaderw.exe", True, False),
        ("bootloader_uac.exe", False, True),
        ("bootloaderw_uac.exe", True, True),
    ]

    for name, windowed, uac in variants:
        exe_path = EXE_FOLDER / name
        compile_exe(c_file, exe_path, windowed=windowed)
        if uac:
            embed_manifest(exe_path)

def cleanup():
    # Remove build folder
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        logging.info(f"Removed build folder {BUILD_DIR}")

    # Remove any Python DLLs in EXEs folder
    for dll in EXE_FOLDER.glob("python*.dll"):
        try:
            dll.unlink()
            logging.info(f"Removed DLL {dll}")
        except Exception as e:
            logging.warning(f"Failed to remove DLL {dll}: {e}")
            

if __name__ == "__main__":
    build_all()
    compress_with_upx(EXE_FOLDER)
    cleanup()
