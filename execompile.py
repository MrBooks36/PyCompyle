import os
import subprocess
import shutil
import sys

VENV_DIR = "venv"
REQUIRED_PACKAGES = ["PyInstaller", "pyzipper"]

EXEs = [
    "bootloader.exe",
    "bootloaderw.exe",
    "bootloader_uac.exe",
    "bootloaderw_uac.exe"
]

# ---- Ensure EXEs directory exists ----
os.makedirs("EXEs", exist_ok=True)

# ---- Remove old EXEs ----
for exe in EXEs:
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

# ---- 2. Try to install required packages in venv ----
def install_packages(python_exe):
    for pkg in REQUIRED_PACKAGES:
        try:
            subprocess.run([python_exe, "-m", "pip", "show", pkg],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"Installing {pkg}...")
            try:
                subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
                subprocess.run([python_exe, "-m", "pip", "install", pkg], check=True)
            except subprocess.CalledProcessError:
                print(f"Failed to install {pkg} with {python_exe}.")
                return False
    return True

# ---- Attempt to use venv or fallback to system Python ----
if not install_packages(PYTHON_EXE):
    print("Falling back to system-wide Python environment.")
    PYTHON_EXE = sys.executable
    if not install_packages(PYTHON_EXE):
        sys.exit("Failed to install required packages in both virtual and system-wide environments.")

def compile_bootloader(pyinstaller_args, output_name):
    """Compile the bootloader using PyInstaller."""
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


# --- 4. Sign the bootloaders ---
pfx_path = os.getenv('PFX_PATH')
if not pfx_path:
    print('PFX_PATH environment variable not set. Skipping...')
    sys.exit(0)

# Ensure the files and paths exist
if not os.path.exists(pfx_path):
    print(f"PFX file not found at {pfx_path}. Skipping...")
    sys.exit(0)

# Securely retrieve sensitive information from environment variables
pfx_password = os.getenv('PFX_PASSWORD')
if not pfx_password:
    raise EnvironmentError("PFX_PASSWORD environment variable not set")

# Define the path to the executables directory
EXEs_directory = os.path.abspath('EXEs')

# Ensure the directory exists
if not os.path.isdir(EXEs_directory):
    raise FileNotFoundError(f"Executable directory not found at {EXEs_directory}")

# Loop through files and sign them
for exe in EXEs:
    exe_path = os.path.join(EXEs_directory, exe)

    # Validate that the executable exists
    if os.path.exists(exe_path):
        try:
            subprocess.run(
                [
                    'signtool', 'sign', '/f', pfx_path, '/p', pfx_password, 
                    '/fd', 'SHA256', exe_path
                ],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Signing failed for {exe_path}: {e}")
    else:
        print(f"Executable not found: {exe_path}")

# ---- Final cleanup ----
shutil.rmtree("dist", ignore_errors=True)