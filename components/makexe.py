import os, shutil, logging
from logging import info
from sys import argv
try: from components import zip_embeder
except: import zip_embeder

def setup_logging():
    """Set up logging configuration."""
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

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


def main(folder_path, no_console, source_file_name, keepfiles):
    setup_logging()
    folder_name = os.path.basename(folder_path).replace('.build','')
    info('Removing __pycache__')
    delete_pycache(folder_path)
    delete_pycache(os.getcwd())
    info('Giving args')
    with open(os.path.join(folder_path, 'thefilename'), 'w') as file:
        file.write(source_file_name)
    info('Compressing')
    shutil.make_archive(base_name=folder_name, root_dir=folder_path, base_dir='.', format='zip')
    zip_path = folder_name+'.zip'
    info('Creating EXE')
    create_exe(folder_name, zip_path, no_console)

    if not keepfiles:
        info('Cleaning up')
        shutil.rmtree(folder_path)
        os.remove(zip_path)