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

    lib_folder_basename = 'lib'
    for path in sys.path:
        if not os.path.isdir(path):
            continue

        lib_folder = os.path.join(path, lib_folder_basename)

        if not os.path.isdir(lib_folder):
            continue

        for dirpath, dirnames, filenames in os.walk(lib_folder):
            # Skip __pycache__ directories
            if '__pycache__' in dirnames:
                dirnames.remove('__pycache__')

            for filename in filenames:
                if not filename.endswith('.py'):
                    continue

                file_full_path = os.path.join(dirpath, filename)
                rel_path_in_lib = os.path.relpath(file_full_path, lib_folder)

                # Check if the file exists in any of the current sys.path directories
                found = any(
                    os.path.exists(os.path.join(p, rel_path_in_lib))
                    for p in sys.path
                    if os.path.isdir(p)
                )

                if not found:
                    logging.debug(f"Compiling: {rel_path_in_lib}")

                    # Attempt to compile the file
                    if not compile_file(file_full_path):
                        sys.exit(1)

                    logging.info(f"Successfully compiled {rel_path_in_lib}.")