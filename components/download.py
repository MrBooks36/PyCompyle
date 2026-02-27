import os, requests, zipfile, logging, io, platform, stat, tarfile
from datetime import datetime, timezone
from logging import info

def download_resourcehacker(cache_path):
    url = 'https://www.angusj.com/resourcehacker/resource_hacker.zip'
    os.makedirs(cache_path, exist_ok=True)
    cache_path= os.path.join(cache_path, 'resource_hacker')
    os.makedirs(cache_path, exist_ok=True)

    zip_filename = os.path.join(cache_path, 'resource_hacker.zip')
    response = requests.get(url, headers={"User-Agent": "XY"})
    response.raise_for_status()

    with open(zip_filename, 'wb') as file:
        file.write(response.content)

    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(cache_path)

    os.remove(zip_filename)
    info(f"Files extracted to: {cache_path}")


def download_and_update_linked_imports(cache_file="linked_imports.json", timestamp_file="linked_imports_timestamp.txt"):
    github_url="https://raw.githubusercontent.com/MrBooks36/PyCompyle/main/linked_imports.json"
    info('Refreshing linked_imports.json')
    try:
        logging.debug(f"Downloading linked_imports.json from GitHub: {github_url}")
        response = requests.get(github_url, timeout=10)
        response.raise_for_status()
        with open(cache_file, "wb") as f:
            f.write(response.content)
        with open(timestamp_file, "w") as tf:
            tf.write(datetime.now(timezone.utc).isoformat())
        logging.info("linked_imports.json downloaded and timestamp updated.")
    except Exception as e:
        logging.warning(f"Failed to download linked_imports.json: {e}")

def install_upx():
    system = platform.system()

    if system == "Windows":
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base_dir = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

    dest_folder = os.path.join(base_dir, "PyCompyle.cache")
    os.makedirs(dest_folder, exist_ok=True)

    api_url = "https://api.github.com/repos/upx/upx/releases/latest"

    logging.debug("Fetching UPX release info from GitHub API")
    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    assets = data.get("assets", [])
    if not assets:
        logging.error("No assets found in UPX release")
        return None

    # Determine platform match
    if system == "Windows":
        preferred = ["win64", "win32"]
        archive_ext = ".zip"
        binary_name = "upx.exe"
    elif system == "Linux":
        preferred = ["linux-amd64", "amd64"]
        archive_ext = ".tar.xz"
        binary_name = "upx"
    else:
        logging.error(f"Unsupported platform: {system}")
        return None

    archive_url = None

    for pref in preferred:
        for asset in assets:
            name = asset["name"].lower()
            if pref in name and name.endswith(archive_ext):
                archive_url = asset["browser_download_url"]
                logging.debug(f"Selected asset: {asset['name']}")
                break
        if archive_url:
            break

    if not archive_url:
        logging.error("No suitable UPX binary found for this platform")
        return None

    logging.debug(f"Downloading UPX from {archive_url}")
    resp = requests.get(archive_url, timeout=60)
    resp.raise_for_status()

    # Extract archive
    if archive_ext == ".zip":
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            candidates = [
                n for n in zf.namelist()
                if n.endswith("/" + binary_name) or n.endswith(binary_name)
            ]
            if not candidates:
                raise RuntimeError(f"{binary_name} not found in archive")

            internal_path = candidates[0]
            zf.extract(internal_path, dest_folder)
            src_path = os.path.join(dest_folder, internal_path)

    else:
        with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:xz") as tf:
            candidates = [
                m for m in tf.getmembers()
                if m.name.endswith("/" + binary_name) or m.name.endswith(binary_name)
            ]
            if not candidates:
                raise RuntimeError(f"{binary_name} not found in archive")

            member = candidates[0]
            tf.extract(member, dest_folder)
            src_path = os.path.join(dest_folder, member.name)

    final_path = os.path.join(dest_folder, binary_name)

    # Move binary to flat location
    os.replace(src_path, final_path)

    try:
        extracted_dir = os.path.dirname(src_path)
        if extracted_dir != dest_folder:
            os.removedirs(extracted_dir)
    except OSError:
        pass

    # Make executable on Linux
    if system != "Windows":
        st = os.stat(final_path)
        os.chmod(final_path, st.st_mode | stat.S_IEXEC)

    logging.debug(f"UPX installed at {final_path}")

    return final_path