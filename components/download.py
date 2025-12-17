import os, requests, zipfile, logging, re, io, platform, stat, tarfile
from datetime import datetime, timezone
from logging import info

def download_resourcehacker(cache_path):
    url = 'https://www.angusj.com/resourcehacker/resource_hacker.zip'
    os.makedirs(cache_path, exist_ok=True)
    cache_path= os.path.join(cache_path, 'resource_hacker')
    os.makedirs(cache_path, exist_ok=True)

    zip_filename = os.path.join(cache_path, 'resource_hacker.zip')
    response = requests.get(url, headers={"User-Agent": "XY"})
    response.raise_for_status()  # Ensure the request was successful

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
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open(cache_file, "wb") as f:
            f.write(response.content)
        with open(timestamp_file, "w") as tf:
            tf.write(datetime.now(timezone.utc).isoformat())
        logging.info("linked_imports.json downloaded and timestamp updated.")
    except Exception as e:
        logging.warning(f"Failed to download linked_imports.json: {e}")

def install_upx():
    system = platform.system()

    # Cache directory
    if system == "Windows":
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base_dir = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

    dest_folder = os.path.join(base_dir, "PyCompyle.cache")
    os.makedirs(dest_folder, exist_ok=True)

    releases_url = "https://github.com/upx/upx/releases/latest"
    resp = requests.get(releases_url, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # Determine target archive + binary name
    if system == "Windows":
        patterns = [
            r"https://github\.com/upx/upx/releases/download/[^\"']+/upx-[^\"']+-win64\.zip",
            r"https://github\.com/upx/upx/releases/download/[^\"']+/upx-[^\"']+-win32\.zip",
        ]
        binary_name = "upx.exe"
        archive_type = "zip"

    elif system == "Linux":
        patterns = ['https://github.com/upx/upx/releases/download/v5.0.2/upx-5.0.2-amd64_linux.tar.xz']
        binary_name = "upx"
        archive_type = "tar.xz"

    match = None
    for pat in patterns:
        match = re.search(pat, html)
        if match:
            logging.debug(f"Found UPX download link: {match.group(0)}")
            break

    if not match:
        logging.error("Could not find UPX release for this platform.")
        return None

    archive_url = match.group(0)
    resp = requests.get(archive_url, timeout=30)
    resp.raise_for_status()

    if archive_type == "zip":
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            candidates = [n for n in zf.namelist() if n.endswith("/" + binary_name) or n.endswith(binary_name)]
            if not candidates:
                raise RuntimeError(f"{binary_name} not found in archive.")
            internal_path = candidates[0]
            zf.extract(internal_path, dest_folder)
            src_path = os.path.join(dest_folder, internal_path)
    else:  # tar.xz
        with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:xz") as tf:
            candidates = [m for m in tf.getmembers() if m.name.endswith("/" + binary_name) or m.name.endswith(binary_name)]
            if not candidates:
                raise RuntimeError(f"{binary_name} not found in archive.")
            member = candidates[0]
            tf.extract(member, dest_folder)
            src_path = os.path.join(dest_folder, member.name)

    final_path = os.path.join(dest_folder, binary_name)
    os.replace(src_path, final_path)

    # Cleanup nested dirs
    extracted_dir = os.path.dirname(src_path)
    if extracted_dir and extracted_dir != dest_folder:
        try:
            os.rmdir(extracted_dir)
        except OSError:
            pass

    # Linux: mark executable
    if system != "Windows":
        logging.debug(f"Setting executable permissions for {final_path}")
        st = os.stat(final_path)
        os.chmod(final_path, st.st_mode | stat.S_IEXEC)

    return final_path
