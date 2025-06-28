import subprocess, os, logging, zipfile, requests
from logging import info

def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

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

 

def add_uac(exe_path):
 cache_path = os.path.expandvars('%LOCALAPPDATA%\\PyPackager.cache')
 os.makedirs(cache_path, exist_ok=True)
 resource_hacker = os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')
 info(f'Cache path: {cache_path}')

 if not os.path.exists(os.path.join(cache_path, 'resource_hacker')):
        info('Downloading ResourceHacker...')
        download_and_extract_zip('https://www.angusj.com/resourcehacker/resource_hacker.zip', cache_path)   

 manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>'''

 # Write manifest to temp file
 with open("temp_admin.manifest", "w", encoding="utf-8") as f:
    f.write(manifest_content)

 # Build Resource Hacker command
 cmd = [
    resource_hacker,
    "-open", exe_path,
    "-save", exe_path,
    "-action", "addoverwrite",
    "-res", "temp_admin.manifest",
    "-mask", "MANIFEST,1,"
]

 # Run Resource Hacker
 subprocess.run(cmd, check=True)

 # Clean up
 os.remove("temp_admin.manifest")

 info("Embedded admin manifest into {exe_path}")


def main(exe_path):
    """Main function to add UAC to an executable."""
    setup_logging()
    if not os.path.exists(exe_path):
        logging.error(f"Executable '{exe_path}' does not exist.")
        return

    try:
        add_uac(exe_path)
        logging.info(f"Successfully added UAC to '{exe_path}'.")
    except Exception as e:
        logging.error(f"Failed to add UAC: {e}")