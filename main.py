import os, sys, platform, shutil, subprocess, ast, importlib.util, logging, argparse, fnmatch, json, urllib.request
from components import getimports, makexe
from getpass import getpass
from datetime import datetime, timedelta
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

def load_linked_imports(force=False):
    import urllib.request
    from datetime import datetime, timedelta, timezone

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    cache_dir = os.path.join(local_appdata, "PyPackager.cache")
    cache_file = os.path.join(cache_dir, "linked_imports.json")
    timestamp_file = os.path.join(cache_dir, "linked_imports.timestamp")
    fallback_path = os.path.join(os.path.dirname(__file__), "linked_imports.json")
    github_url = "https://raw.githubusercontent.com/MrBooks36/PyPackager/main/linked_imports.json"
    refresh_interval = timedelta(hours=24)

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

    if not needs_refresh:
        if os.path.exists(timestamp_file):
            try:
                with open(timestamp_file, "r") as tf:
                    last_updated = datetime.fromisoformat(tf.read().strip())
                    if datetime.now(timezone.utc) - last_updated >= refresh_interval:
                        needs_refresh = True
                        logging.debug("linked_imports.json is older than 24 hours, will refresh.")
            except Exception as e:
                logging.warning(f"Invalid timestamp format, forcing refresh: {e}")
                needs_refresh = True

    if needs_refresh:
        logging.info("Refreshing linked_imports.json (forced or outdated).")
        download_and_update()

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in cached linked_imports.json.")

    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in fallback linked_imports.json.")

    logging.debug("No linked_imports.json could be loaded from any location.")
    return {}


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
    except (SyntaxError, Exception) as e:
        logging.error(f"Error parsing modules output: {e}")
        logging.error(f"Output received: {output}")
        modules = []

    cleaned_modules = set(mod.split('.')[0] for mod in modules if mod and isinstance(mod, str))

    # Add linked imports
    linked_imports = load_linked_imports()
    linked_extras = set()
    for mod in cleaned_modules:
        extras = linked_imports.get(mod, [])
        linked_extras.update(extras)

    cleaned_modules.update(linked_extras)
    cleaned_modules = sorted(cleaned_modules)

    logging.debug(f"Identified cleaned modules: {cleaned_modules}")
    return cleaned_modules

def copy_dependencies(cleaned_modules, lib_path, folder_path):
    for module_name in cleaned_modules:
        if module_name == '__main__':
            continue
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin and 'built-in' not in spec.origin and 'frozen' not in spec.origin:
            path = spec.origin.replace(r'\__init__.py', '')
            target_path = folder_path if 'site-packages' in path else lib_path
            try:
                if os.path.isdir(path):
                    shutil.copytree(path, os.path.join(target_path, os.path.basename(path)))
                    info(f"Copied module: {os.path.basename(path)}")
                else:
                    shutil.copyfile(path, os.path.join(target_path, os.path.basename(path)))
                    info(f"Copied file: {os.path.basename(path)}")
            except Exception as e:
                logging.error(f"Error copying {path}: {e}")

def should_exclude(name, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False

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
    parser.add_argument('-p', '--package', action='append', help='Include a package that might have been missed. (CAPS matter) Can be used multiple times.', default=[])
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.', default=False)
    parser.add_argument('-w', '--windowed', action='store_true', help='Disable console', default=False)
    parser.add_argument('-k', '--keepfiles', action='store_true', help='Keep the build files', default=False)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable all debugging tools: "--verbose" "--keepfiles and disable "--windowed"', default=False)
    parser.add_argument('-cf', '--copyfolder', action='append', help='Path(s) to folder(s) to copy into the build directory. Can be used multiple times.', default=[])
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh of linked_imports.json from GitHub', default=False)
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

    for folder in args.copyfolder:
        if os.path.isdir(folder):
            dest_path = os.path.join(folder_path, os.path.basename(folder))
            try:
                copy_folder_with_excludes(folder, dest_path, ['__pycache__', '.git'])
                info(f"Copied folder '{folder}' to '{dest_path}' ")
            except Exception as e:
                logging.error(f"Failed to copy folder '{folder}': {e}")
        else:
            logging.error(f"The specified path for --copyfolder is not a directory: {folder}")

    cleaned_modules = process_imports(source_file_path, args.package, args.keepfiles)
    lib_path = os.path.join(folder_path, 'lib')
    os.makedirs(lib_path, exist_ok=True)
    copy_dependencies(cleaned_modules, lib_path, folder_path)

    destination_file_path = os.path.join(folder_path, os.path.basename(source_file_path))
    shutil.copyfile(source_file_path, destination_file_path)
    info(f"Packaged script copied to {destination_file_path}")

    info(f"Packaging complete: {folder_path}")
    if not args.noconfirm:
        getpass('Press Enter to continue wrapping the EXE')
    makexe.main(folder_path, args.windowed, os.path.basename(source_file_path), args.keepfiles, args.icon)

if __name__ == "__main__":
    main()
