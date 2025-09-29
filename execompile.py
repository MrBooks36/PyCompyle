import os
import subprocess
import shutil
import sys

VENV_DIR = "venv"
REQUIRED_PACKAGES = ["PyInstaller", "pyzipper"]

# ---- Ensure EXEs directory exists ----
os.makedirs("EXEs", exist_ok=True)

# ---- Remove old EXEs ----
for exe in ["bootloader.exe", "bootloaderw.exe",
            "bootloader_uac.exe", "bootloaderw_uac.exe"]:
    exe_path = os.path.join("EXEs", exe)
    if os.path.exists(exe_path):
        os.remove(exe_path)

BOOTLOADER = os.path.join("components", "bootloader.py")

# ---- 1. Create venv if it doesn't exist ----
if not os.path.exists(VENV_DIR):
    print(f"Creating virtual environment in '{VENV_DIR}'...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

# ---- Locate venv Python ----
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe")

# ---- 2. Ensure required packages are installed ----
for pkg in REQUIRED_PACKAGES:
    try:
        subprocess.run([PYTHON_EXE, "-m", pkg, "--version"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Installing {pkg} in the virtual environment...")
        subprocess.run([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([PYTHON_EXE, "-m", "pip", "install", pkg], check=True)

def compile_bootloader(pyinstaller_args, output_name):
    """Run PyInstaller inside the venv to compile the bootloader."""
    cmd = [
        PYTHON_EXE, "-m", "PyInstaller",
        "--onefile", "-i", "NONE", "--strip",
        "--distpath", "dist"
    ] + pyinstaller_args + [BOOTLOADER]

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

    # Cleanup build folders and spec file
    for path in ["build", "bootloader.spec"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

# ---- 3. Compile the bootloaders ----
compile_bootloader([], "bootloader.exe")                    # Regular
compile_bootloader(["--noconsole"], "bootloaderw.exe")      # Windowed
compile_bootloader(["--uac-admin"], "bootloader_uac.exe")   # UAC
compile_bootloader(["--noconsole", "--uac-admin"], "bootloaderw_uac.exe")  # Windowed UAC

# ---- Final cleanup ----
shutil.rmtree("dist", ignore_errors=True)
