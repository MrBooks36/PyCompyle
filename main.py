import os
import sys

# Platform-specific import
import platform

# Ensure script runs only if on Windows
if platform.system() != 'Windows':
    print("This script is designed to run only on Windows.")
    sys.exit(1)

import shutil
import subprocess
import ast
import importlib.util
import logging
import argparse
import tempfile
from components import getimports, makexe
from getpass import getpass

def setup_logging(verbose=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def find_dlls_with_phrase(directory, phrase):
    matching_dlls = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.dll') and phrase.lower() in filename.lower():
            full_path = os.path.join(directory, filename)
            matching_dlls.append(full_path)
    return matching_dlls

def setup_destination_folder(source_file, destination_folder=None):
    """Sets up the destination folder path."""
    if not destination_folder:
        folder_name = os.path.splitext(source_file)[0]  # Remove file extension
        destination_folder = os.path.abspath(folder_name)+'.build'
        
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder)
    return destination_folder

def copy_python_executable(folder_path):
    """Copies Python executable to the destination folder."""
    python_executable = sys.executable
    if not 'python.exe' in python_executable:
        logging.error('Python interpreter must be named "python.exe" because I(MrBooks36) am lazy')
    shutil.copy(python_executable, folder_path)
    logging.info(f"Copied Python executable to {folder_path}")

    python_dir = os.path.dirname(python_executable)
    shutil.copytree(os.path.join(python_dir, 'DLLs'), os.path.join(folder_path, 'DLLs'))
    logging.info(f"Copied Python DLL folder to {folder_path}")

    for dll in find_dlls_with_phrase(python_dir, 'python'):
        shutil.copy(dll, folder_path)

    for dll in find_dlls_with_phrase(python_dir, 'vcruntime'):
        shutil.copy(dll, folder_path)

def process_imports(source_file_path, python_executable):
    """Processes imports in the source file and returns cleaned module paths."""
    try:
        # Get the directory of the source file
        source_dir = os.path.dirname(source_file_path)
        
        # Add the source file's directory to sys.path for relative imports
        if source_dir not in sys.path:
            sys.path.insert(0, source_dir)

        # Use `recursive_imports` from getimports.py to gather all import statements
        imports = getimports.recursive_imports(source_file_path)
        logging.debug(f"Raw imports from file: {imports}")

        # Create temporary file paths in the source directory
        tmp_script_path = os.path.join(source_dir, 'tmp_imports_checker.py')
        tmp_output_path = os.path.join(source_dir, 'tmp_imports_output.txt')

        # Ensure any existing temp files are removed
        if os.path.exists(tmp_script_path):
            os.remove(tmp_script_path)
        if os.path.exists(tmp_output_path):
            os.remove(tmp_output_path)

        # Write the temporary script
        with open(tmp_script_path, 'w') as tmp_file:
            for imp in imports:
                tmp_file.write(f'import {imp}\n')
            tmp_file.write('import sys\n')
            # Use raw string or os.path methods for writing the file path
            tmp_file.write(f"with open(r'{tmp_output_path}', 'w') as out_file:\n")
            tmp_file.write('    out_file.write(str([m.__name__ for m in sys.modules.values() if m]))\n')

        # Save the current working directory
        original_dir = os.getcwd()
        
        try:
            # Change to the source directory and run the temporary script
            os.chdir(source_dir)
            subprocess.run([python_executable, tmp_script_path], check=True)
        finally:
            # Change back to the original directory
            os.chdir(original_dir)

        # Remove the temporary script after execution
        os.remove(tmp_script_path)

        # Read output from the temporary result file
        with open(tmp_output_path, "r") as out_file:
            output = out_file.read().strip()
        os.remove(tmp_output_path)
        
        logging.debug(f"Output read from tmp file: {output}")
        
        try:
            modules = ast.literal_eval(output)
        except SyntaxError as e:
            logging.error(f"Syntax error while parsing modules output: {e}")
            logging.error(f"Output received: {output}")
            modules = []
        except Exception as e:
            logging.error(f"Error parsing modules output: {e}")
            logging.error(f"Output received: {output}")
            modules = []

        # Clean the module list to avoid duplicates and handle local imports
        cleaned_modules = sorted(set(mod.split('.')[0] for mod in modules if isinstance(mod, str)))
        logging.debug(f"Identified cleaned modules: {cleaned_modules}")
        return cleaned_modules

    except Exception as e:
        logging.error(f"Error processing imports: {e}")
        exit()
        return []

def copy_dependencies(cleaned_modules, lib_path, folder_path):
    """Copies module files or directories based on their paths."""
    module_paths = []
    for module_name in cleaned_modules:
        # Skip the current script ('__main__') or any empty module names
        if module_name == '__main__' or not module_name:
            continue
            
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin and 'built-in' not in spec.origin and 'frozen' not in spec.origin:
            module_paths.append(spec.origin)

    for path in set(module_paths):
        path = str(path).replace(r'\__init__.py','')
        if 'site-packages' in path:
            try:
             if os.path.isdir(path):
                shutil.copytree(path, os.path.join(folder_path, os.path.basename(path)))
             else:
                shutil.copy(path, os.path.join(folder_path, os.path.basename(path)))
             logging.info(f"Copied module: {os.path.basename(path)}")
            except Exception as e:
             logging.error(f"Error copying {path}: {e}")
        else:
         try:
            if os.path.isdir(path):
                shutil.copytree(path, os.path.join(lib_path, os.path.basename(path)))
            else:
                shutil.copy(path, os.path.join(lib_path, os.path.basename(path)))
            logging.info(f"Copied module: {os.path.basename(path)}")
         except Exception as e:
            logging.error(f"Error copying {path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Package a Python script with its dependencies.")
    parser.add_argument('source_file', help='The Python script to package.')
    parser.add_argument('-nc', '--noconfirm', action='store_true', help='Skip confirmation for wraping the exe', default=False)
    parser.add_argument('-d', '--destination', help='Destination folder for the package.', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output.')
    parser.add_argument('-w', '--windowed', action='store_true', help='Disable console', default=False)
    parser.add_argument('-k', '--keepfiles', action='store_true', help='Keep the build files', default=False)
    args = parser.parse_args()

    setup_logging(args.verbose)

    source_file_path = os.path.abspath(args.source_file)
    source_file_name = os.path.basename(source_file_path)
    logging.info(f"Source file: {source_file_path}")

    # Set up destination folder
    folder_path = setup_destination_folder(args.source_file, args.destination)

    # Copy Python executable
    copy_python_executable(folder_path)

    # Process imports and copy dependencies
    cleaned_modules = process_imports(source_file_path, sys.executable)
    copy_dependencies(cleaned_modules, os.path.join(folder_path, 'lib'), folder_path)

    # Copy the original source script into the destination folder
    destination_file_path = os.path.join(folder_path, os.path.basename(source_file_path))
    shutil.copyfile(source_file_path, destination_file_path)
    logging.info(f"Packaged script copied to {destination_file_path}")

    logging.info(f"Packaging complete: {folder_path}")
    if not args.noconfirm:
     getpass('Press Enter to continue wraping the EXE')
    makexe.main(folder_path, args.windowed, source_file_name, args.keepfiles)

if __name__ == "__main__":
    main()