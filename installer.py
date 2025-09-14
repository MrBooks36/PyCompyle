import os
import sys
import zipfile
import io
import subprocess
import shutil
import json
import sysconfig
import tempfile
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from subprocess import CalledProcessError


def get_site_packages_path():
    return sysconfig.get_paths()["purelib"]


def check_if_already_installed():
    target = os.path.join(get_site_packages_path(), "PyCompyle")
    init_file = os.path.join(target, "__main__.py")
    return os.path.isdir(target) and os.path.isfile(init_file)


def uninstall():
    target = os.path.join(get_site_packages_path(), "PyCompyle")
    if os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
        print("Uninstalled PyCompyle")
    else:
        print("PyCompyle is not installed.")


def get_latest_release(repo_url):
    """
    Returns the URL of the latest build zip if it exists,
    otherwise returns the zipball_url of the source.
    """
    api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = Request(api_url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode())

        # Try to find a build zip first
        for asset in data.get("assets", []):
            name = asset.get("name", "").lower()
            if "build" in name and name.endswith(".zip"):
                return asset["browser_download_url"]

        # Fallback: use source zip
        print("No build zip found, using source zip.")
        return data["zipball_url"]

    except HTTPError as e:
        raise Exception(f"HTTP Error: {e.code} - {e.reason}") from e
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}") from e
    except Exception as e:
        raise Exception(f"Failed to get latest release: {e}") from e

def _safe_extract(zip_file, path):
    for member in zip_file.namelist():
        member_path = os.path.abspath(os.path.join(path, member))
        if not member_path.startswith(os.path.abspath(path) + os.sep):
            raise Exception("Zip file contains unsafe paths")
    zip_file.extractall(path)

def download_and_extract_zip(zip_url, extract_to):
    """
    Downloads the zip from zip_url, extracts it safely, and
    moves all files/folders into extract_to/PyCompyle.
    Works for both flat build zips and nested GitHub source zips.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = Request(zip_url, headers=headers)
        with urlopen(req) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                with tempfile.TemporaryDirectory(prefix="PyCompyle_tmp_") as temp_dir:
                    _safe_extract(z, temp_dir)

                    # Locate the real root folder containing __main__.py
                    possible_roots = []
                    for root, dirs, files in os.walk(temp_dir):
                        if "__main__.py" in files:
                            possible_roots.append(root)

                    if not possible_roots:
                        raise Exception("Could not find PyCompyle folder in the zip")

                    # Use the first folder containing __main__.py
                    source_folder = possible_roots[0]
                    final_path = os.path.join(extract_to, "PyCompyle")

                    if os.path.exists(final_path):
                        shutil.rmtree(final_path, ignore_errors=True)

                    # Move all files/folders from source_folder into final_path
                    os.makedirs(final_path, exist_ok=True)
                    for entry in os.listdir(source_folder):
                        src = os.path.join(source_folder, entry)
                        dst = os.path.join(final_path, entry)
                        shutil.move(src, dst)

    except Exception as e:
        raise Exception(f"Failed to download and extract zip: {e}") from e

def install_requirements(package_path):
    req_file = os.path.join(package_path, "requirements.txt")
    if os.path.exists(req_file):
        print(f"Installing dependencies from {req_file}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file],
                capture_output=True,
                text=True,
                check=True
            )
        except CalledProcessError as e:
            print(e.stderr)
            raise Exception("Failed to install requirements") from e
    else:
        print("No requirements.txt found, skipping dependency installation.")

def install_latest_release(repo_url):
    site_packages_path = get_site_packages_path()
    print(f"Site-packages path: {site_packages_path}")
    zip_url = get_latest_release(repo_url)
    download_and_extract_zip(zip_url, site_packages_path)
    install_requirements(os.path.join(site_packages_path, "PyCompyle"))
    print("Successfully installed PyCompyle")

if __name__ == "__main__":
    repository = "MrBooks36/PyCompyle"
    try:
        if check_if_already_installed():
            choice = input("PyCompyle is already installed. [R]emove, [U]pdate/Repair, [Any other button] Cancel: ").lower()
            if choice == 'r':
                uninstall()
            elif choice == 'u':
                print("Reinstalling PyCompyle...")
                install_latest_release(repository)
            else:
                print("Canceled.")
        else:
            print("Installing PyCompyle...")
            install_latest_release(repository)
    except Exception as e:
        print(f"An error occurred: {e}")

    input("Press enter to exit...")
