import os
import subprocess
import shutil

# Ensure EXEs directory exists
os.makedirs("EXEs", exist_ok=True)

# Remove old executables
for exe in ["bootloader.exe", "bootloaderw.exe", "bootloader_uac.exe", "bootloaderw_uac.exe"]:
    exe_path = os.path.join("EXEs", exe)
    if os.path.exists(exe_path):
        os.remove(exe_path)

# Set bootloader path
BOOTLOADER = os.path.join("components", "bootloader.py")

# Helper function to run Nuitka
def compile_bootloader(args, output_name):
    subprocess.run(["python", "-m", "nuitka"] + args + [BOOTLOADER], check=True)
    # Move compiled exe to EXEs folder
    dist_path = os.path.join("dist", "bootloader.exe")
    if os.path.exists(dist_path):
        shutil.move(dist_path, os.path.join("EXEs", output_name))

# Compile regular bootloader
compile_bootloader(["--standalone", "--onefile", "--remove-output", "--output-dir=dist"], "bootloader.exe")

# Compile windowed bootloader (no console)
compile_bootloader(["--standalone", "--onefile", "--windows-console-mode=disable", "--remove-output", "--output-dir=dist"], "bootloaderw.exe")

# Compile UAC bootloader
compile_bootloader(["--standalone", "--onefile", "--windows-uac-admin", "--remove-output", "--output-dir=dist"], "bootloader_uac.exe")

# Compile windowed UAC bootloader
compile_bootloader(["--standalone", "--onefile", "--windows-console-mode=disable", "--windows-uac-admin", "--remove-output", "--output-dir=dist"], "bootloaderw_uac.exe")
