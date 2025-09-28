import os
import subprocess
import shutil

os.makedirs("EXEs", exist_ok=True)

# Remove old EXEs
for exe in ["bootloader.exe", "bootloaderw.exe", "bootloader_uac.exe", "bootloaderw_uac.exe"]:
    exe_path = os.path.join("EXEs", exe)
    if os.path.exists(exe_path):
        os.remove(exe_path)

BOOTLOADER = os.path.join("components", "bootloader.py")

def compile_bootloader(pyinstaller_args, output_name):
    cmd = ["pyinstaller", "--onefile", "-i", "NONE", "--distpath", "dist"] + pyinstaller_args + [BOOTLOADER]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("PyInstaller failed!")
        print(result.stdout)
        print(result.stderr)
        return

    dist_path = os.path.join("dist", "bootloader.exe")
    if os.path.exists(dist_path):
        shutil.move(dist_path, os.path.join("EXEs", output_name))

    # Cleanup
    for path in ["build", "bootloader.spec"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

# regular
compile_bootloader([], "bootloader.exe")
# windowed
compile_bootloader(["--noconsole"], "bootloaderw.exe")
# UAC
compile_bootloader(["--uac-admin"], "bootloader_uac.exe")
# windowed UAC
compile_bootloader(["--noconsole", "--uac-admin"], "bootloaderw_uac.exe")

shutil.rmtree("dist", ignore_errors=True)