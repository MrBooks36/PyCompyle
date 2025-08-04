import os
import sys
import zipfile
import io
import subprocess
import shutil
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def get_site_packages_path():
    for path in sys.path:
        if "site-packages" in path:
            return path
    raise Exception("site-packages path not found")

def check_if_already_installed():
    return os.path.exists(os.path.join(get_site_packages_path(), "PyPackager"))

def uninstall():
    target = os.path.join(get_site_packages_path(), "PyPackager")
    if os.path.exists(target):
        shutil.rmtree(target)
        print("Uninstalled PyPackager")
    else:
        print("PyPackager is not installed.")

def get_latest_release(repo_url):
    api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    try:
        response = urlopen(api_url)
        data = json.loads(response.read().decode())
        return data["zipball_url"]
    except HTTPError as e:
        raise Exception(f"HTTP Error: {e.code} - {e.reason}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")
    except Exception as e:
        raise Exception(f"Failed to get latest release: {e}")

def download_and_extract_zip(zip_url, extract_to):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = Request(zip_url, headers=headers)
        with urlopen(req) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                temp_dir = os.path.join(extract_to, "__pypackager_temp__")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                z.extractall(temp_dir)

                inner_folder = next(os.scandir(temp_dir)).path
                final_path = os.path.join(extract_to, "PyPackager")
                if os.path.exists(final_path):
                    shutil.rmtree(final_path)
                shutil.move(inner_folder, final_path)
                shutil.rmtree(temp_dir)
    except Exception as e:
        raise Exception(f"Failed to download and extract zip: {e}")

def install_requirements(package_path):
    req_file = os.path.join(package_path, "requirements.txt")
    if os.path.exists(req_file):
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(result.stderr)
            raise Exception("Failed to install requirements")
    else:
        print("No requirements.txt found, skipping dependency installation.")

def install_latest_release(repo_url):
    site_packages_path = get_site_packages_path()
    print(f"Site-packages path: {site_packages_path}")
    zip_url = get_latest_release(repo_url)
    download_and_extract_zip(zip_url, site_packages_path)
    install_requirements(os.path.join(site_packages_path, "PyPackager"))
    print("Successfully installed PyPackager")

if __name__ == "__main__":
    repository = "MrBooks36/PyPackager"

    try:
        if check_if_already_installed():
            choice = input("PyPackager is already installed. [R]emove, [U]pdate/Repair, [Any other button] Cancel: ").lower()
            if choice == 'r':
                uninstall()
            elif choice == 'u':
                print("Reinstalling PyPackager...")
                install_latest_release(repository)
            else:
                print("Canceled.")
        else:
            print("Installing PyPackager...")
            install_latest_release(repository)
    except Exception as e:
        print(f"An error occurred: {e}")

    input("Press enter to exit...")
