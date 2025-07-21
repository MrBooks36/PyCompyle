import os, sys, platform, shutil, subprocess, ast, importlib.util, logging, argparse, fnmatch, json, urllib.request
from components import getimports, makexe
from getpass import getpass
from datetime import datetime, timedelta, timezone
from logging import info

def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def validate_platform():
    if not platform.system() == 'Windows':
        print("This script is designed to run only on Windows.")
        sys.exit(1)

def find_dlls_with_phrase(directory, phrase):
    return [
        os.path.join(directory, filename) for filename in os.listdir(directory)
        if filename.lower().endswith('.dll') and phrase.lower() in filename.lower()
    ]

def setup_destination_folder(source_file):
    destination_folder = os.path.abspath(source_file.replace('.py', '.build'))
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder)
    return destination_folder

def copy_python_executable(folder_path):
    python_executable = sys.executable
    if not os.path.basename(python_executable) == 'python.exe':
        logging.error('Python interpreter must be named "python.exe".')
        sys.exit(1)

    shutil.copy(python_executable, folder_path)
    info(f"Copied Python executable to {folder_path}")

    python_dir = os.path.dirname(python_executable)
    shutil.copytree(os.path.join(python_dir, 'DLLs'), os.path.join(folder_path, 'DLLs'))
    info(f"Copied Python DLL folder to {folder_path}")

    for dll_phrase in ['python', 'vcruntime']:
        for dll in find_dlls_with_phrase(python_dir, dll_phrase):
            shutil.copy(dll, folder_path)

def copy_tk(folder_path):
    python_folder = os.path.dirname(sys.executable)
    shutil.copytree(os.path.join(python_folder, 'tcl'), os.path.join(folder_path, 'tcl'))       
    info(f'Copied Tcl folder to {folder_path}')
    
def load_linked_imports(force=False):
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    cache_dir = os.path.join(local_appdata, "PyPackager.cache")
    cache_file = os.path.join(cache_dir, "linked_imports.json")
    timestamp_file = os.path.join(cache_dir, "linked_imports.timestamp")
    github_url = "https://raw.githubusercontent.com/MrBooks36/PyPackager/main/linked_imports.json"
    refresh_interval = timedelta(hours=24)
    local_json = os.path.join(os.path.dirname(__file__), "linked_imports.json")

    os.makedirs(cache_dir, exist_ok=True)

    def download_and_update():
        try:
            logging.debug(f"Downloading linked_imports.json from GitHub: {github_url}")
            urllib.request.urlretrieve(github_url, cache_file)
            with open(timestamp_file, "w") as tf:
                tf.write(datetime.now(timezone.utc).isoformat())
            logging.info("linked_imports.json downloaded and timestamp updated.")
        except Exception as e:
            logging.warning(f"Failed to download linked_imports.json: {e}")

    needs_refresh = force or not os.path.exists(cache_file)
    if not needs_refresh and os.path.exists(timestamp_file):
        try:
            with open(timestamp_file, "r") as tf:
                last_updated = datetime.fromisoformat(tf.read().strip())
                if datetime.now(timezone.utc) - last_updated >= refresh_interval:
                    needs_refresh = True
                    logging.debug("linked_imports.json cache is older than 24 hours, will refresh.")
        except Exception as e:
            logging.warning(f"Invalid timestamp format, forcing refresh: {e}")
            needs_refresh = True

    if needs_refresh:
        logging.info("Refreshing cached linked_imports.json")
        download_and_update()

    if os.path.exists(local_json) and os.path.exists(os.path.join(os.path.dirname(__file__), "localjson")):
        try:
            with open(local_json, "r", encoding="utf-8") as f:
                logging.info("Using local linked_imports.json (same folder as script)")
                return json.load(f)
        except Exception as e:
            logging.warning(f"Local linked_imports.json invalid: {e}")    

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                logging.info("Using cached linked_imports.json (from cache directory)")
                return json.load(f)
        except Exception as e:
            logging.warning(f"Cached linked_imports.json invalid: {e}")

    if os.path.exists(local_json):
        try:
            with open(local_json, "r", encoding="utf-8") as f:
                logging.info("Using local linked_imports.json (same folder as script)")
                return json.load(f)
        except Exception as e:
            logging.warning(f"Local linked_imports.json invalid: {e}")
    logging.warning("No valid linked_imports.json could be loaded from local or cache.")
    return {}        

def resolve_linked_imports_recursive(base_modules, linked_map):
    resolved = set()
    queue = list(base_modules)

    while queue:
        module = queue.pop()
        if module not in resolved:
            resolved.add(module)
            linked = linked_map.get(module, [])
            logging.debug(f"Module '{module}' links to: {linked}")
            queue.extend(linked)
    return resolved


def process_imports(source_file_path, packages, keepfile):
    source_dir = os.path.dirname(source_file_path)
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)

    imports = getimports.recursive_imports(source_file_path)
    logging.debug(f"Raw imports from file: {imports}")

    tmp_script_path = os.path.join(source_dir, 'tmp_imports_checker.py')
    tmp_output_path = os.path.join(source_dir, 'tmp_imports_output.txt')

    for tmp_path in [tmp_script_path, tmp_output_path]:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    with open(tmp_script_path, 'w') as tmp_file:
        tmp_file.write('\n'.join(f'try:\n import {imp}\nexcept: pass\n' for imp in imports))
        for package in packages:
            tmp_file.write(f'try:\n import {package}\nexcept: pass\n')
        tmp_file.write('\nimport sys')
        tmp_file.write(f"\nwith open(r'{tmp_output_path}', 'w') as out_file:")
        tmp_file.write('\n    out_file.write(str([m.__name__ for m in sys.modules.values() if m]))')

    original_dir = os.getcwd()
    try:
        os.chdir(source_dir)
        subprocess.run([sys.executable, tmp_script_path], check=True)
    finally:
        os.chdir(original_dir)
    if not keepfile:
        os.remove(tmp_script_path)

    with open(tmp_output_path, "r") as out_file:
        output = out_file.read().strip()
    if not keepfile:
        os.remove(tmp_output_path)

    logging.debug(f"Output read from tmp file: {output}")

    try:
        modules = ast.literal_eval(output)
    except Exception as e:
        logging.error(f"Error parsing modules output: {e}")
        logging.error(f"Output received: {output}")
        modules = []

    cleaned_modules = set(mod.split('.')[0] for mod in modules if mod and isinstance(mod, str))

    linked_imports = load_linked_imports()
    cleaned_modules = resolve_linked_imports_recursive(cleaned_modules.union(packages), linked_imports)
    cleaned_modules = sorted(cleaned_modules)
    logging.debug(f"Final cleaned modules (with linked deps): {cleaned_modules}")
    return cleaned_modules

def copy_dependencies(cleaned_modules, lib_path, folder_path, source_dir):
    for module_name in cleaned_modules:
        if module_name == '__main__':
            continue

        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None or 'built-in' in spec.origin or 'frozen' in spec.origin:
            local_folder = os.path.join(source_dir, module_name)
            if os.path.isdir(local_folder):
                target_path = os.path.join(folder_path, module_name)
                try:
                    copy_folder_with_excludes(local_folder, target_path, exclude_patterns=['__pycache__', '.git'])
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
            try:
                shutil.copy2(origin_path, os.path.join(lib_path, os.path.basename(origin_path)))
                info(f"Copied module file: {os.path.basename(origin_path)} to lib")
            except Exception as e:
                logging.error(f"Error copying module file {origin_path}: {e}")

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

def main():
    validate_platform()

    parser = argparse.ArgumentParser(description="Package a Python script into a EXE with its dependencies.")
    parser.add_argument('source_file', help='The Python script to package.')
    parser.add_argument('-nc', '--noconfirm', action='store_true', help='Skip confirmation for wrapping the exe', default=False)
    parser.add_argument('-i', '--icon', help='Icon for the created EXE', default=False)
    parser.add_argument('-p', '--package', action='append', help='Include a package that might have been missed.', default=[])
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.', default=False)
    parser.add_argument('-w', '--windowed', action='store_true', help='Disable console', default=False)
    parser.add_argument('-k', '--keepfiles', action='store_true', help='Keep the build files', default=False)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable all debugging tools: --verbose --keepfiles and disable --windowed', default=False)
    parser.add_argument('-cf', '--copyfolder', action='append', help='(Deprecated) Folder(s) to copy into the build directory.', default=[])
    parser.add_argument('-c', '--copy', action='append', help='File(s) or folder(s) to copy into the build directory.', default=[])
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh of linked_imports.json from GitHub', default=False)
    parser.add_argument('-tk', '--use-tkinter', action='store_true', help='Force refresh of linked_imports.json from GitHub', default=False)
    parser.add_argument('-uac', '--uac', action='store_true', help='Add UAC to the EXE', default=False)
    args = parser.parse_args()

    if args.debug:
        args.verbose = True
        args.keepfiles = True
        args.windowed = False
    setup_logging(args.verbose)

    source_file_path = os.path.abspath(args.source_file)
    info(f"Source file: {source_file_path}")
    os.chdir(os.path.dirname(source_file_path))

    folder_path = setup_destination_folder(args.source_file)
    copy_python_executable(folder_path)

    if args.use_tkinter:
        copy_tk(folder_path)

    copy_paths = (args.copy or []) + (args.copyfolder or [])
    for path in copy_paths:
        name = os.path.basename(path)
        dest_path = os.path.join(folder_path, name)
        try:
            if os.path.isdir(path):
                copy_folder_with_excludes(path, dest_path, ['__pycache__', '.git'])
                info(f"Copied folder '{path}' to '{dest_path}'")
            elif os.path.isfile(path):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(path, dest_path)
                info(f"Copied file '{path}' to '{dest_path}'")
            else:
                logging.error(f"The specified path does not exist: {path}")
        except Exception as e:
            logging.error(f"Failed to copy '{path}': {e}")

    cleaned_modules = process_imports(source_file_path, args.package, args.keepfiles)
    lib_path = os.path.join(folder_path, 'lib')
    os.makedirs(lib_path, exist_ok=True)
    source_dir = os.path.dirname(source_file_path)
    copy_dependencies(cleaned_modules, lib_path, folder_path, source_dir)

    destination_file_path = os.path.join(folder_path, os.path.basename(source_file_path))
    shutil.copyfile(source_file_path, destination_file_path)
    info(f"Packaged script copied to {destination_file_path}")

    info(f"Packaging complete: {folder_path}")
    if not args.noconfirm:
        getpass('Press Enter to continue wrapping the EXE')
    makexe.main(os.path.basename(source_file_path), folder_path, args.windowed, args.keepfiles, args.icon, uac=args.uac)

if __name__ == "__main__":
    main()
