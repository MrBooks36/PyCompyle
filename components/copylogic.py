import sys, os, logging, shutil, importlib.util, platform
from components.plugins import get_special_cases
from logging import info

def find_dlls_with_phrase(directory, phrase):
    return [
        os.path.join(directory, filename) for filename in os.listdir(directory)
        if filename.lower().endswith('.dll') and phrase.lower() in filename.lower()
    ]

def copy_dlls_folder(folder_path, python_dir, disable_dll=False):
    if platform.system() == "Windows" and not disable_dll:
        try:
            shutil.copytree(os.path.join(python_dir, "DLLs"), os.path.join(folder_path, "DLLs"))
            info(f"Copied Python DLL folder to {folder_path}")
        except FileNotFoundError:
            logging.warning("Dlls folder not found")


def copy_python_executable(folder_path, disable_python_environment, disable_dll):
    if disable_python_environment:
        logging.debug("Skipping copying Python executable and DLLs")
        return
    python_executable = sys.executable
    python_dir = os.path.dirname(python_executable)

    if os.name == 'nt' and not disable_dll:
        copy_dlls_folder(folder_path, python_dir, disable_dll)

    if not disable_python_environment:
        shutil.copy(python_executable, os.path.join(folder_path, "python.exe" if os.name == 'nt' else 'python'))
        info(f"Copied Python executable to {folder_path}")
    python_dir = os.path.dirname(python_executable)
    
    for dll_phrase in ['python', 'vcruntime']:
        for dll in find_dlls_with_phrase(python_dir, dll_phrase):
            shutil.copy(dll, folder_path)

def copy_tk(folder_path):
    try:
        python_folder = os.path.dirname(sys.executable)
        tcl_directory = os.path.join(python_folder, 'tcl')

        if not os.path.exists(tcl_directory):
            logging.warning(f"TCL directory does not exist: {tcl_directory}")
            return

        for phrase in ['tk', 'tcl']:
            for item in os.listdir(tcl_directory):
                item_path = os.path.join(tcl_directory, item)
                if os.path.isdir(item_path) and phrase.lower() in item.lower():
                    destination_path = os.path.join(folder_path, 'lib', item)
                    try:
                        if os.path.exists(destination_path):
                            shutil.rmtree(destination_path)
                        shutil.copytree(item_path, os.path.join(destination_path))
                    except IOError as e:
                        logging.error(f"Error copying {item_path} to {destination_path}: {e}")

        info(f'Copied tcl directories')

    except Exception as e:
        logging.error(f"An unexpected error occurred in copying tk: {e}")

def copy_scripts(files, folder_path):
    if files: os.makedirs(os.path.join(folder_path, 'Scripts'), exist_ok=True)
    for filename in files:
        file = os.path.join(os.path.dirname(sys.executable), "Scripts", filename)
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(folder_path, "Scripts", filename))
            logging.debug(f"Copied {filename} to build")
        else: logging.warning(f"{filename} not found in Scripts dir")

def copy_include(folder_path):
    include_path = os.path.join(os.path.dirname(sys.executable), "include")
    shutil.copytree(include_path, os.path.join(folder_path, 'include'))
    info('Copied include folder to build')

def copy_dependencies(cleaned_modules, lib_path, folder_path, source_dir, disable_lib_compressing):
    special_cases = list(get_special_cases())

    for module_name in cleaned_modules:
        if module_name == '__main__':
            continue

        ran_plugin = False
        for import_name, body, top, continue_after in special_cases:
            skip = []
            if module_name == import_name and import_name not in skip:
                ran_plugin = True
                if top:
                    exec(body, globals(), locals())
                    skip.append(import_name)
                if not continue_after:
                    continue
        else:
            spec = importlib.util.find_spec(module_name)
            if spec is None or spec.origin is None or 'built-in' in spec.origin or 'frozen' in spec.origin:
                local_folder = os.path.join(source_dir, module_name)
                if os.path.isdir(local_folder):
                    os.makedirs(os.path.join(folder_path, "local"), exist_ok=True)
                    target_path = os.path.join(folder_path, "local" if not disable_lib_compressing else "lib", module_name) # when lib_c is used for a local import e.g. ./components the python interpreter it doesn't find it for some reason
                    try:
                        shutil.copytree(local_folder, target_path)
                        if logging.DEBUG >= logging.root.level:
                            logging.debug(f"Copied local folder from {local_folder} to {target_path}")
                        else:
                            info(f"Copied local folder module (no __init__.py): {module_name}")
                    except Exception as e:
                        logging.error(f"Error copying local folder {local_folder}: {e}")
                else:
                    logging.debug(f"No local folder found for module: {module_name}")
                continue

            origin_path = spec.origin
            if origin_path.endswith('__init__.py') or origin_path.endswith('__init__.pyc'):
                package_folder = os.path.dirname(origin_path)
                target_path = os.path.join(lib_path, os.path.basename(package_folder))
                try:
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    shutil.copytree(package_folder, target_path)
                    if logging.DEBUG >= logging.root.level:
                        logging.debug(f"Copied package from {package_folder} to {target_path}")
                    else:
                        info(f"Copied package folder: {os.path.basename(package_folder)}")
                except Exception as e:
                    logging.error(f"Error copying package folder {package_folder}: {e}")
            else:
                if origin_path.endswith('.pyd'):
                    try:
                        shutil.copy2(origin_path, os.path.join(os.path.join(os.path.dirname(lib_path), 'DLLs'),
                                                              os.path.basename(origin_path)))
                        if logging.DEBUG >= logging.root.level:
                            logging.debug(f"Copied PYD from {origin_path} to {os.path.join(os.path.dirname(lib_path), 'DLLs')}")
                        else:
                            info(f"Copied package PYD: {os.path.basename(origin_path)}")
                    except Exception as e:
                        logging.error(f"Error copying module PYD {origin_path}: {e}")
                else:
                    try:
                        shutil.copy2(origin_path, os.path.join(lib_path, os.path.basename(origin_path)))
                        if logging.DEBUG >= logging.root.level:
                            logging.debug(f"Copied module file from {origin_path} to {lib_path}")
                        info(f"Copied package file: {os.path.basename(origin_path)}")
                    except Exception as e:
                        logging.error(f"Error copying module file {origin_path}: {e}")

        if module_name == "_tkinter":
            copy_tk(folder_path)

        # execute plugin code here if it had bottom placement
        if ran_plugin:
            skip = []
            for import_name, body, top, continue_after in special_cases:
                if module_name == import_name and not top and import_name not in skip:
                    exec(body, globals(), locals())
                    skip.append(import_name)