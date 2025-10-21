import sys, os, logging, shutil, importlib.util, fnmatch
try:
    from components.plugins import get_special_cases
except: 
    from PyCompyle.components.plugins import get_special_cases # type: ignore
from logging import info

global exclude_pattens
exclude_pattens = []

def find_dlls_with_phrase(directory, phrase):
    return [
        os.path.join(directory, filename) for filename in os.listdir(directory)
        if filename.lower().endswith('.dll') and phrase.lower() in filename.lower()
    ]

def copy_python_executable(folder_path):
    python_executable = sys.executable

    shutil.copy(python_executable, os.path.join(folder_path, "python.exe"))
    info(f"Copied Python executable to {folder_path}")

    python_dir = os.path.dirname(python_executable)
    shutil.copytree(os.path.join(python_dir, 'DLLs'), os.path.join(folder_path, 'DLLs'))
    info(f"Copied Python DLL folder to {folder_path}")

    for dll_phrase in ['python', 'vcruntime']:
        for dll in find_dlls_with_phrase(python_dir, dll_phrase):
            shutil.copy(dll, folder_path)
    
    # PyCompyle.utils special case
    os.makedirs(os.path.join(folder_path, 'PyCompyle'))
    shutil.copy2(os.path.join(os.path.dirname(sys.modules["__main__"].__file__), "util.py"), os.path.join(folder_path, "PyCompyle"))

def copy_tk(folder_path):
    try:
        python_folder = os.path.dirname(sys.executable)
        tcl_directory = os.path.join(python_folder, 'tcl')

        # Check if the path exists to avoid errors.
        if not os.path.exists(tcl_directory):
            logging.warning(f"TCL directory does not exist: {tcl_directory}")
            return

        # Locate and copy directories that match the phrase
        for phrase in ['tk', 'tcl']:
            for item in os.listdir(tcl_directory):
                item_path = os.path.join(tcl_directory, item)
                # Check if item is a directory and matches the phrase
                if os.path.isdir(item_path) and phrase.lower() in item.lower():
                    destination_path = os.path.join(folder_path, 'Lib', item)
                    try:
                        if os.path.exists(destination_path):
                            shutil.rmtree(destination_path)
                        shutil.copytree(item_path, os.path.join(destination_path))
                    except IOError as e:
                        logging.error(f"Error copying {item_path} to {destination_path}: {e}")

        info(f'Copied tcl directories to {folder_path}')

    except Exception as e:
        logging.error(f"An unexpected error occurred in copying tk: {e}")


def copy_dependencies(cleaned_modules, lib_path, folder_path, source_dir):
    special_cases = list(get_special_cases())

    for module_name in cleaned_modules:
        if module_name == '__main__' or module_name == 'PyCompyle':
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
                    target_path = os.path.join(folder_path, module_name)
                    try:
                        copy_folder_with_excludes(local_folder, target_path, exclude_patterns=exclude_pattens)
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
                    info(f"Copied package folder: {os.path.basename(package_folder)} to lib")
                except Exception as e:
                    logging.error(f"Error copying package folder {package_folder}: {e}")
            else:
                if origin_path.endswith('.pyd'):
                    try:
                        shutil.copy2(origin_path, os.path.join(os.path.join(os.path.dirname(lib_path), 'Dlls'),
                                                              os.path.basename(origin_path)))
                        info(f"Copied module PYD: {os.path.basename(origin_path)}")
                    except Exception as e:
                        logging.error(f"Error copying module PYD {origin_path}: {e}")
                else:
                    try:
                        shutil.copy2(origin_path, os.path.join(lib_path, os.path.basename(origin_path)))
                        info(f"Copied module file: {os.path.basename(origin_path)}")
                    except Exception as e:
                        logging.error(f"Error copying module file {origin_path}: {e}")

        if module_name == "tkinter" or module_name == "_tkinter":
            copy_tk(folder_path)

        # execute plugin code here if it had bottom placement
        if ran_plugin:
            skip = []
            for import_name, body, top, continue_after in special_cases:
                if module_name == import_name and not top and import_name not in skip:
                    exec(body, globals(), locals())
                    skip.append(import_name)

def should_exclude(name, patterns):
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)

def copy_folder_with_excludes(src, dst, exclude_patterns):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dest_root = os.path.join(dst, rel_path) if rel_path != '.' else dst

        dirs[:] = [d for d in dirs if not should_exclude(d, exclude_patterns)]

        for file in files:
            if should_exclude(file, exclude_patterns):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_root, file)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)