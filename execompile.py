import os
import subprocess
import shutil

os.makedirs("EXEs", exist_ok=True)

for exe in ["bootloader.exe", "bootloaderw.exe", "bootloader_uac.exe", "bootloaderw_uac.exe"]:
    exe_path = os.path.join("EXEs", exe)
    if os.path.exists(exe_path):
        os.remove(exe_path)

BOOTLOADER = os.path.join("components", "bootloader.py")

def compile_bootloader(pyinstaller_args, output_name):
    subprocess.run(
        ["pyinstaller", "--onefile", "-i NONE", "--distpath", "dist" ]+ pyinstaller_args + [BOOTLOADER],
        check=True
    )
    dist_path = os.path.join("dist", "bootloader.exe")
    if os.path.exists(dist_path):
        shutil.move(dist_path, os.path.join("EXEs", output_name))
    build_dir = "build"
    spec_file = "bootloader.spec"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(spec_file):
        os.remove(spec_file)

# regular
compile_bootloader([], "bootloader.exe")
# windowed
compile_bootloader(["--noconsole"], "bootloaderw.exe")
# UAC
compile_bootloader(["--uac-admin"], "bootloader_uac.exe")
# windowed UAC
compile_bootloader(["--noconsole", "--uac-admin"], "bootloaderw_uac.exe")
