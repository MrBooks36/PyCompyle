import os
import sys
import subprocess
import logging
import hashlib

# Shutup vars
folder_path = ''
plugin = ''

def compile_file(file_path):
     try:
        import nuitka
        del nuitka
     except ImportError:
        logging.error("Nuitka is not installed.")
        return False

     if not os.path.isfile(file_path):
        logging.error(f"Invalid Python file: {file_path}")
        return False
     try:
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(file_path))
        subprocess.run(['python', '-m', 'nuitka', '--module', '--remove-output', file_path], check=True)
        os.chdir(original_cwd)
        return True
     except Exception as e:
        logging.error(f"Failed to compile {file_path} with Cython: {e}")
        return False
     
def hash_file(file_path):
    if os.path.exists(file_path):
     sha256 = hashlib.sha256()
     with open(file_path, 'rb') as f:
      while chunk := f.read(65536): # Read in chunks of 64 KB
       sha256.update(chunk)
     return sha256.hexdigest()      

def midway():
    logging.info("Starting Nuitka compilation of .py files.")
    lib_folder = os.path.join(folder_path, 'lib')
    python_lib_path = os.path.dirname(os.__file__)
    site_packages_path = os.path.join(python_lib_path, 'site-packages')
    # Win32 compatibility
    win32_lib_path = os.path.join(site_packages_path, 'win32', 'lib')

    for dirpath, dirnames, filenames in os.walk(lib_folder):
        if '__pycache__' in dirnames:
            dirnames.remove('__pycache__')

        for filename in filenames:
            if not filename.endswith('.py'):
                 continue

            file_full_path = os.path.join(dirpath, filename)
            rel_path_in_lib = os.path.relpath(file_full_path, lib_folder)
    
            python_lib_file = os.path.join(python_lib_path, rel_path_in_lib)
            site_packages_file = os.path.join(site_packages_path, rel_path_in_lib)
            win32_lib_file = os.path.join(win32_lib_path, rel_path_in_lib)
    
            files_exist = os.path.exists(python_lib_file) or os.path.exists(site_packages_file) or os.path.exists(win32_lib_file)

            files_match_hashes = (
                plugin.hash_file(file_full_path) == plugin.hash_file(python_lib_file) or
                plugin.hash_file(file_full_path) == plugin.hash_file(site_packages_file) or
                plugin.hash_file(file_full_path) == plugin.hash_file(win32_lib_file)
            )

            if not files_exist and not files_match_hashes:
                logging.debug(f"Compiling: {rel_path_in_lib}")
                if not plugin.compile_file(file_full_path):
                    logging.error(f"Failed to compile {rel_path_in_lib}. Exiting.")
                    sys.exit(1)
                logging.info(f"Successfully compiled {rel_path_in_lib} with Nuitka.")



def compile_main(folder_path):
    main_file = os.path.join(folder_path, '__main__.py')
    init_file = os.path.join(folder_path, 'PyCompyle_nuitka_start.py')
    with open(main_file, 'r') as f:
            original_content = f.read()

    modified_content = "__name__ = '__main__'\n" + original_content

    with open(init_file, 'w') as f:
                f.write(modified_content)

    compile_file(init_file)

    os.remove(init_file)
    with open(main_file, 'w') as f:
        f.write('import PyCompyle_nuitka_start')





patches = {
    "components.makexe.compile_main": {"func": compile_main, "wrap": False}
}