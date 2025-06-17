import os, shutil, logging, zipfile, requests
from logging import info
from sys import argv
from tqdm import tqdm
try: from components import zip_embeder
except: import zip_embeder

def setup_logging():
    """Set up logging configuration."""
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')


def compress_with_progress(folder_path, folder_name):

    # Calculate the total size of files to be compressed
    total_size = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            total_size += os.path.getsize(os.path.join(root, file))

    # Initialize tqdm progress bar
    pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc='INFO: Compressing')

    with zipfile.ZipFile(f"{folder_name}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=arcname)
                # Update progress bar
                pbar.update(os.path.getsize(file_path))

    pbar.close()    

def delete_pycache(start_dir):
    deleted_count = 0
    for root, dirs, files in os.walk(start_dir):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_path = os.path.join(root, dir_name)
                try:
                    # Remove all files in the __pycache__ directory
                    for file in os.listdir(pycache_path):
                        file_path = os.path.join(pycache_path, file)
                        os.remove(file_path)

                    # Remove the __pycache__ directory
                    os.rmdir(pycache_path)
                    info(f"Deleted folder: {pycache_path}")
                    deleted_count += 1
                except Exception as e:
                    info(f"Error deleting {pycache_path}: {e}")
    
    info(f"Total '__pycache__' folders deleted: {deleted_count}")

def create_exe(name, zip_path, no_console):
    exe_folder = os.path.join(os.path.dirname(argv[0]), 'EXEs')
    if no_console: zip_embeder.main(name, os.path.join(exe_folder, 'bootloaderw.exe'), zip_path)
    else: zip_embeder.main(name, os.path.join(exe_folder, 'bootloader.exe'), zip_path)

def download_and_extract_zip(url, extract_to='resource_hacker'):
    # Ensure the directory exists
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    # Download the file
    zip_filename = os.path.join(extract_to, 'resource_hacker.zip')
    response = requests.get(url)
    
    with open(zip_filename, 'wb') as file:
        file.write(response.content)

    # Extract the ZIP file
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    # Clean up
    os.remove(zip_filename)
    print(f"Files extracted to: {extract_to}")    

def add_icon(name, icon):
    cache_path = os.path.expandvars('%LOCALAPPDATA%\\PyPackager.cache')
    if not os.path.exists(cache_path): os.makedirs(cache_path)
    info(f'Cache path: {cache_path}')
    if not os.path.exists(os.path.join(cache_path, 'resource_hacker')): 
        info('Downloading ResourceHacker: https://www.angusj.com/resourcehacker/resource_hacker.zip')
        download_and_extract_zip('https://www.angusj.com/resourcehacker/resource_hacker.zip')

    r_hacker_path =  os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')

    os.system(f'{r_hacker_path} -open {name}.exe -save {name}.exe -action add -res {icon} -mask ICONGROUP,MAINICON,')



def main(folder_path, no_console, source_file_name, keepfiles, icon):
    setup_logging()
    folder_name = os.path.basename(folder_path).replace('.build','')
    info('Removing __pycache__')
    delete_pycache(folder_path)
    delete_pycache(os.getcwd())
    info('Giving args')
    with open(os.path.join(folder_path, 'thefilename'), 'w') as file:
        file.write(source_file_name)
    compress_with_progress(folder_path, folder_name)
    zip_path = folder_name+'.zip'
    info('Creating EXE')
    create_exe(folder_name, zip_path, no_console)

    if icon:
        if os.path.exists(icon):
         info(f'Adding icon: {icon}')
         add_icon(folder_name, icon)
        else:
         logging.error(f'Icon file not found: {icon}')     

    if not keepfiles:
        info('Cleaning up')
        shutil.rmtree(folder_path)
        os.remove(zip_path)

if __name__ == '__main__':
    setup_logging()
    add_icon('test', r"C:\Users\ofk20\Documents\GitHub\talon\media\ICON.ico")