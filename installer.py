import os
import sys
import zipfile
import io
import subprocess
import shutil
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

def get_site_packages_path():
    if hasattr(sys, 'real_prefix'):  # Check if in a virtual environment
        return os.path.join(sys.prefix, 'lib', 'python{}'.format(sys.version[:3]), 'site-packages')
    elif sys.base_prefix != sys.prefix:  # Another virtual environment check
        return os.path.join(sys.prefix, 'lib', 'python{}'.format(sys.version[:3]), 'site-packages')
    else:
        return str(next(p for p in sys.path if 'site-packages' in p))

def check_if_already_installed():
    site_packages_path = get_site_packages_path()
    if os.path.exists(os.path.join(site_packages_path, "Pypackager")):
        return True
    return False

def uninstall():
    shutil.rmtree(os.path.join(get_site_packages_path(), "PyPackager"))
    print("Uninstalled PyPackager")

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
        with urlopen(zip_url) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                z.extractall(extract_to)
    except HTTPError as e:
        raise Exception(f"HTTP Error: {e.code} - {e.reason}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")
    except Exception as e:
        raise Exception(f"Failed to download and extract zip: {e}")

def install_latest_release(repo_url):
    site_packages_path = get_site_packages_path()
    print(f"Site-packages path: {site_packages_path}")
    zip_url = get_latest_release(repo_url)
    download_and_extract_zip(zip_url, site_packages_path)
    print("Installing requirements via pip")
    output = subprocess.run([sys.executable, "-m pip install", os.path.join(site_packages_path, "Pypackager", "requirements.txt")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if output.returncode != 0:
        print(output.stderr)
        raise Exception("Failed to install requirement via pip")
    print(f"Successfully installed the PyPackager")

if __name__ == "__main__":
    repository = "mrbooks36/pypackager"
    if check_if_already_installed():
        output = input('PyPackager is already installed: [R]Remove, [U]Update/Repair [Any other button]Cancel\n').lower()
        if output == 'r':
            uninstall()
        elif output == 'u':
            print("Reinstalling Pypackager...")
            install_latest_release(repository)
        else:
            print("Canceled")    
    else:
        try:
            print("Installing Pypackager...")
            install_latest_release(repository)
            input('Press enter to exit...')
        except Exception as e:
            print(f"An error occurred: {e}")