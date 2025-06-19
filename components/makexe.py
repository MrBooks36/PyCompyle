import os
import shutil
import logging
import zipfile
import requests
from logging import info, error
from sys import argv
from tqdm import tqdm

try:
    from components import zip_embeder
except ImportError:
    import zip_embeder


def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')


def compress_folder_with_progress(folder_path, output_zip_name):
    """Compresses a folder into a ZIP file with a progress bar."""
    total_size = sum(os.path.getsize(os.path.join(root, file))
                     for root, _, files in os.walk(folder_path) for file in files)

    with tqdm(total=total_size, unit='B', unit_scale=True, desc='INFO: Compressing') as pbar, \
         zipfile.ZipFile(f"{output_zip_name}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=arcname)
                pbar.update(os.path.getsize(file_path))


def delete_pycache(start_dir):
    """Deletes __pycache__ directories recursively."""
    deleted_count = 0

    for root, dirs, _ in os.walk(start_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                info(f"Deleted folder: {pycache_path}")
                deleted_count += 1
            except Exception as e:
                error(f"Error deleting {pycache_path}: {e}")

    info(f"Total '__pycache__' folders deleted: {deleted_count}")


def create_executable(name, zip_path, no_console=False):
    """Creates an executable file using the zip_embeder."""
    exe_folder = os.path.join(os.path.dirname(argv[0]), 'EXEs')
    bootloader = 'bootloaderw.exe' if no_console else 'bootloader.exe'
    zip_embeder.main(name, os.path.join(exe_folder, bootloader), zip_path)


def download_and_extract_zip(url, extract_to='resource_hacker'):
    """Downloads and extracts a zip file from a given URL."""
    os.makedirs(extract_to, exist_ok=True)

    zip_filename = os.path.join(extract_to, 'resource_hacker.zip')
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    with open(zip_filename, 'wb') as file:
        file.write(response.content)

    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    os.remove(zip_filename)
    print(f"Files extracted to: {extract_to}")


def add_icon_to_executable(name, icon_path):
    """Adds an icon to an executable using Resource Hacker."""
    cache_path = os.path.expandvars('%LOCALAPPDATA%\\PyPackager.cache')
    os.makedirs(cache_path, exist_ok=True)
    info(f'Cache path: {cache_path}')

    if not os.path.exists(os.path.join(cache_path, 'resource_hacker')):
        info('Downloading ResourceHacker...')
        download_and_extract_zip('https://www.angusj.com/resourcehacker/resource_hacker.zip', cache_path)

    r_hacker_path = os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')
    command = f'"{r_hacker_path}" -open "{name}.exe" -save "{name}.exe" -action add -res "{icon_path}" -mask ICONGROUP,MAINICON'
    os.system(command)


def main(folder_path, no_console=False, source_file_name='source.pyw', keepfiles=False, icon_path=None):
    """Main function to execute the operations."""
    setup_logging()
    folder_name = os.path.basename(folder_path).replace('.build', '')

    info('Removing __pycache__ directories...')
    delete_pycache(folder_path)
    delete_pycache(os.getcwd())

    info('Writing source file name...')
    with open(os.path.join(folder_path, 'thefilename'), 'w') as file:
        file.write(source_file_name)

    compress_folder_with_progress(folder_path, folder_name)

    info('Creating executable...')
    create_executable(folder_name, f"{folder_name}.zip", no_console)

    if icon_path:
        if os.path.exists(icon_path):
            info(f'Adding icon: {icon_path}')
            add_icon_to_executable(folder_name, icon_path)
        else:
            error(f'Icon file not found: {icon_path}')

    if not keepfiles:
        info('Cleaning up...')
        shutil.rmtree(folder_path)
        os.remove(f"{folder_name}.zip")