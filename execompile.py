import os
import subprocess
import shutil
import sys
import platform

SYSTEM = platform.system()

BOOTLOADER = os.path.join("components", "bootloader.py")

# Use a user-local venv on Linux to avoid PEP 668
if SYSTEM == "Windows":
    VENV_DIR = "venv"
    EXEs = [
        "bootloader.exe",
        "bootloaderw.exe",
        "bootloader_uac.exe",
        "bootloaderw_uac.exe"
    ]
    PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe")
else:
    home = os.path.expanduser("~")
    VENV_DIR = os.path.join(home, ".local", "bootloader_venv")
    EXEs = [
        "bootloader",
        "bootloaderw"
    ]
    PYTHON_EXE = os.path.join(VENV_DIR, "bin", "python")

REQUIRED_PACKAGES = ["PyInstaller", "pyzipper"]

# Remove old EXEs
shutil.rmtree("EXEs", ignore_errors=True)
os.makedirs("EXEs", exist_ok=True)

# Create venv if missing
if not os.path.exists(VENV_DIR):
    print(f"Creating virtual environment in '{VENV_DIR}'...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

# Upgrade pip and install required packages
def install_packages(python_exe):
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    for pkg in REQUIRED_PACKAGES:
        subprocess.run([python_exe, "-m", "pip", "install", pkg], check=True)

try:
    install_packages(PYTHON_EXE)
except subprocess.CalledProcessError:
    sys.exit(f"Failed to install required packages in {PYTHON_EXE}.")

def compile_bootloader(pyinstaller_args, output_name, exe_name="bootloader"):
    cmd = [
        PYTHON_EXE, "-m", "PyInstaller",
        "--onefile", "-i", "NONE", "--distpath", "dist"
    ] + pyinstaller_args + [BOOTLOADER]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("PyInstaller failed!")
        print(result.stdout)
        print(result.stderr)
        return

    dist_path = os.path.join("dist", exe_name + (".exe" if SYSTEM == "Windows" else ""))
    if os.path.exists(dist_path):
        shutil.move(dist_path, os.path.join("EXEs", output_name))

# Compile bootloaders
if SYSTEM == "Windows":
    compile_bootloader([], "bootloader.exe")
    compile_bootloader(["--noconsole"], "bootloaderw.exe")
    compile_bootloader(["--uac-admin"], "bootloader_uac.exe")
    compile_bootloader(["--noconsole", "--uac-admin"], "bootloaderw_uac.exe")
else:
    compile_bootloader([], "bootloader")
    compile_bootloader(["--windowed"], "bootloaderw")

# Signing (Windows only)
if SYSTEM == "Windows":
    pfx_path = os.getenv('PFX_PATH')
    pfx_password = os.getenv('PFX_PASSWORD')

    if pfx_path and pfx_password:
        for exe in EXEs:
            exe_path = os.path.join("EXEs", exe)
            if os.path.exists(exe_path):
                try:
                    subprocess.run(
                        ['signtool', 'sign', '/f', pfx_path, '/p', pfx_password,
                         '/fd', 'SHA256', exe_path],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Signing failed for {exe_path}: {e}")
            else:
                print(f"Executable not found: {exe_path}")
    else:
        print("Skipping signing: PFX_PATH or PFX_PASSWORD not set.")

# Cleanup
shutil.rmtree("dist", ignore_errors=True)
for path in ["build", "bootloader.spec"]:
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
