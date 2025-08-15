import os
import subprocess
import shutil
import logging
import zipfile
import time
try:
 from components.download import download_and_extract_zip
except ImportError:
 from download import download_and_extract_zip
import sys
from logging import info, error
from tqdm import tqdm


def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def zip_embeder(name, exe_file, zip_file):
        setup_logging()
        output_file = os.path.join(os.getcwd(), f'{name}.exe')

        with open(output_file, 'wb') as output:
            with open(exe_file, 'rb') as f_exe:
                output.write(f_exe.read())
            with open(zip_file, 'rb') as f_zip:
                output.write(f_zip.read())

        info(f"Combined executable created: {output_file}")

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


def create_executable(name, zip_path, no_console=False, uac=False, folder=False, folder_path=str()):
    """Creates an executable file using the zip_embeder."""
    exe_folder = os.path.join(os.path.dirname(sys.modules["__main__"].__file__), 'EXEs')  # type: ignore
    
    bootloader_map = {
        (False, False): "bootloader.exe",
        (False, True): "bootloader_uac.exe",
        (True, False): "bootloaderw.exe",
        (True, True): "bootloaderw_uac.exe",
    }
    
    bootloader = bootloader_map[(no_console, uac)]
    if not folder: zip_embeder(name, os.path.join(exe_folder, bootloader), zip_path)
    else: shutil.copy2(src=os.path.join(exe_folder, bootloader), dst=os.path.join(folder_path, f'{name}.exe'))





def add_icon_to_executable(name, icon_path, folder):
    """Adds an icon to an executable using Resource Hacker."""
    name = os.path.abspath(name)
    cache_path = os.path.expandvars('%LOCALAPPDATA%\\PyCompyle.cache')
    os.makedirs(cache_path, exist_ok=True)
    info(f'Cache path: {cache_path}')

    if not os.path.exists(os.path.join(cache_path, 'resource_hacker')):
        info('Downloading ResourceHacker...')
        download_and_extract_zip('https://www.angusj.com/resourcehacker/resource_hacker.zip', cache_path)

    r_hacker_path = os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')
    if folder: command = f'"{r_hacker_path}" -open "{name}.exe" -save "{name}.exe" -action add -res "{icon_path}" -mask ICONGROUP,MAINICON'
    else: command = f'"{r_hacker_path}" -open "{name}.exe" -save "{name}.exe" -action add -res "{icon_path}" -mask ICONGROUP,MAINICON'
    subprocess.run(command, shell=True)


def main(folder_path, no_console=False, keepfiles=False, icon_path=None, uac=False, folder=False):
    """Main function to execute the operations."""
    setup_logging()
    folder_name = os.path.basename(folder_path).replace('.build', '')

    info('Removing __pycache__ directories...')
    delete_pycache(folder_path)
    delete_pycache(os.getcwd())

    info('Writing python args')
    with open(os.path.join(folder_path, 'python._pth'), 'w') as file:
        file.write('Dlls\nLib')

    if not folder: compress_folder_with_progress(folder_path, folder_name)
    else: 
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        try:
            os.rename(folder_path, folder_name) 
        except:
            time.sleep(3)
            os.rename(folder_path, folder_name)
        finally:
            folder_path = folder_path.replace('.build', '')                 
    info('Creating executable...')
    create_executable(folder_name, f"{folder_name}.zip", no_console, uac, folder, folder_path)

    if icon_path:
        if os.path.exists(icon_path):
            info(f'Adding icon: {icon_path}')
            add_icon_to_executable(folder_name, icon_path, folder)
        else:
            error(f'Icon file not found: {icon_path}')

    if not keepfiles and not folder:
        info('Cleaning up...')
        shutil.rmtree(folder_path)
        os.remove(f"{folder_name}.zip")