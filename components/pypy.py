import urllib.request, urllib.parse, re, json, os, logging, shutil
from logging import info

def setup_logging():
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def load_proxy_config():
    config_path = os.path.join(os.path.dirname(__file__), 'proxy_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return json.load(file)
    else:
        return None

def download_latest_pypy(proxy_config=None):
    if proxy_config:
        proxy_url = proxy_config['proxy_url']
        proxy_username = proxy_config['proxy_username']
        proxy_password = proxy_config['proxy_password']

        # Setup proxy with authentication
        proxy_auth = f"{proxy_username}:{proxy_password}@"
        proxy_handler = urllib.request.ProxyHandler({
            'http': f"http://{proxy_auth}{proxy_url}",
            'https': f"https://{proxy_auth}{proxy_url}"
        })
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    else:
        # Use default opener without proxy
        opener = urllib.request.build_opener()
        urllib.request.install_opener(opener)
    
    # URL to download page
    download_page_url = "https://pypy.org/download.html"
    response = urllib.request.urlopen(download_page_url)
    page_content = response.read().decode('utf-8')

    # Update the regular expression based on actual HTML structure
    link_pattern = r'href="([^"]*pypy3[^"]*\.zip)"'
    matches = re.findall(link_pattern, page_content)

    if not matches:
        raise Exception("Could not find any PyPy 'pypy3*' .zip download links")

    # Assuming the first match is the latest version
    latest_link = matches[0]
    download_url = urllib.parse.urljoin(download_page_url, latest_link)

    # Perform the download
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    cache_dir = os.path.join(local_appdata, "PyPackager.cache")
    cache_file = os.path.join(cache_dir, "pypy.zip")
    with urllib.request.urlopen(download_url) as response, open(cache_file, 'wb') as file:
        file.write(response.read())

    info(f"Downloaded {cache_file} successfully")

def find_dlls_with_phrase(directory, phrase):
    return [
        os.path.join(directory, filename) for filename in os.listdir(directory)
        if filename.lower().endswith('.dll') and phrase.lower() in filename.lower()
    ]    

def use_pypy(folder_path):
    #hey copilot, when you are writing the commit message, please note that t his is currently not working
    setup_logging()
    proxy_config = load_proxy_config()
    download_latest_pypy(proxy_config)    
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    cache_dir = os.path.join(local_appdata, "PyPackager.cache")
    cache_file = os.path.join(cache_dir, "pypy.zip")
    shutil.unpack_archive(cache_file, os.path.join(cache_dir, "pypy"))
    _dirs = os.listdir(os.path.join(cache_dir, "pypy"))
    pypy_folder = os.path.join(cache_dir, "pypy", _dirs[0]) # type: ignore
    python_executable = os.path.join(pypy_folder, "python.exe")
    info(f"PyPy executable: {python_executable}")

    shutil.copy(python_executable, folder_path)
    info(f"Copied PyPy executable to {folder_path}")

    python_dir = os.path.dirname(python_executable)
    for dll_phrase in ['lib']:
        for dll in find_dlls_with_phrase(python_dir, dll_phrase):
            shutil.copy(dll, folder_path)

if __name__ == '__main__':
    proxy_config = load_proxy_config()
    download_latest_pypy(proxy_config)