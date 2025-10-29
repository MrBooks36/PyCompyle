import os, requests, zipfile, logging, re, io
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
    localappdata = os.environ.get("LOCALAPPDATA")
    dest_folder = os.path.join(localappdata, "PyCompyle.cache")

    os.makedirs(dest_folder, exist_ok=True)

    releases_url = "https://github.com/upx/upx/releases/latest"
    resp = requests.get(releases_url, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # Prefer 64-bit, fallback to 32-bit
    match = re.search(r"https://github\.com/upx/upx/releases/download/[^\"']+upx-[^\"']+-win64\.zip", html)
    if not match:
        match = re.search(r"https://github\.com/upx/upx/releases/download/[^\"']+upx-[^\"']+-win32\.zip", html)
    if not match:
        logging.error("Could not find UPX Windows release zip.")
        return

    zip_url = match.group(0)

    # Download the zip
    resp = requests.get(zip_url, timeout=30)
    resp.raise_for_status()

    # Extract upx.exe
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        exe_name = [name for name in zf.namelist() if name.endswith("upx.exe")]
        if not exe_name:
            raise RuntimeError("upx.exe not found in zip.")
        exe_name = exe_name[0]

        zf.extract(exe_name, dest_folder)

        src_path = os.path.join(dest_folder, exe_name)
        final_path = os.path.join(dest_folder, "upx.exe")

        # Move to root for convenience
        os.replace(src_path, final_path)

        # Cleanup subdir if it exists
        extracted_dir = os.path.dirname(src_path)
        if extracted_dir != dest_folder:
            try:
                os.rmdir(extracted_dir)
            except OSError:
                pass

        return final_path