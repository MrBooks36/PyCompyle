import os, requests, zipfile, logging
from datetime import datetime, timezone
from logging import info

def download_and_extract_zip(url, extract_to='resource_hacker'):
    """Downloads and extracts a zip file from a given URL."""
    os.makedirs(extract_to, exist_ok=True)
    extract_to= os.path.join(extract_to, 'resource_hacker')
    os.makedirs(extract_to, exist_ok=True)

    zip_filename = os.path.join(extract_to, 'resource_hacker.zip')
    response = requests.get(url, headers={"User-Agent": "XY"})
    response.raise_for_status()  # Ensure the request was successful

    with open(zip_filename, 'wb') as file:
        file.write(response.content)

    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    os.remove(zip_filename)
    info(f"Files extracted to: {extract_to}")


def download_and_update(github_url="https://raw.githubusercontent.com/ofk20/PyCompyle/main/linked_imports.json", cache_dir="cache", cache_file="linked_imports.json", timestamp_file="linked_imports_timestamp.txt"):
    info('Refreshing linked_imports.json')
    try:
        logging.debug(f"Downloading linked_imports.json from GitHub: {github_url}")
        response = requests.get(github_url, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors
        with open(cache_file, "wb") as f:
            f.write(response.content)
        with open(timestamp_file, "w") as tf:
            tf.write(datetime.now(timezone.utc).isoformat())
        logging.info("linked_imports.json downloaded and timestamp updated.")
    except Exception as e:
        logging.warning(f"Failed to download linked_imports.json: {e}")