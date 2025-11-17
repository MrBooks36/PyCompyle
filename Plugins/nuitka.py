import os
import sys
import subprocess
import logging

folder_path = ''

def midway():
    def compile_file(file_path):
     try:
        import nuitka
     except ImportError:
        logging.error("Nuitka is not installed.")
        return False

     if not os.path.isfile(file_path):
        logging.error(f"Invalid Python file: {file_path}")
        return False
     try:
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(file_path))
        subprocess.run(['python', '-m', 'nuitka', '--module', file_path], check=True)
        os.chdir(original_cwd)
        return True
     except Exception as e:
        logging.error(f"Failed to compile {file_path} with Cython: {e}")
        return False

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

            if not (
                os.path.exists(python_lib_file)
                or os.path.exists(site_packages_file)
                or os.path.exists(win32_lib_file)
            ):
                logging.debug(f"Compiling: {rel_path_in_lib}")
                if not compile_file(file_full_path):
                    sys.exit(1)
                logging.info(f"Successfully compiled {rel_path_in_lib} with Nuitka.")