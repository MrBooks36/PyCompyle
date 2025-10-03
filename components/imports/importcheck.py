import os, subprocess, logging, sys, ast, json, shutil
from datetime import datetime, timedelta, timezone
from logging import info

try:from components.imports import getimports
except: from PyCompyle.components.imports import getimports
try:
 from PyCompyle.components import download
except ImportError:
 from components import download

def load_linked_imports(force_refresh=False):
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    cache_dir = os.path.join(local_appdata, "PyCompyle.cache")
    cache_file = os.path.join(cache_dir, "linked_imports.json")
    timestamp_file = os.path.join(cache_dir, "linked_imports.timestamp")
    github_url = "https://raw.githubusercontent.com/MrBooks36/PyCompyle/main/linked_imports.json"
    refresh_interval = timedelta(hours=24)
    local_json = os.path.join(os.path.dirname(sys.modules["__main__"].__file__), "linked_imports.json") # type: ignore
    if force_refresh:
        shutil.rmtree(cache_dir, ignore_errors=True)

    os.makedirs(cache_dir, exist_ok=True)

    needs_refresh = not os.path.exists(cache_file)
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
        download.download_and_update(github_url, cache_dir, cache_file, timestamp_file)

    if os.path.exists(local_json) and os.path.exists(os.path.join(os.path.dirname(sys.modules["__main__"].__file__), "localjson")): # type: ignore
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

def run_import_checker(imports, packages, source_dir, tmp_script_path, tmp_output_path):
    with open(tmp_script_path, 'w') as tmp_file:
        tmp_file.write('\n'.join(f'try:\n    import {imp}\nexcept: pass\n' for imp in imports))
        for package in packages:
            tmp_file.write(f'try:\n    import {package}\nexcept: pass\n')
        tmp_file.write('\nimport sys, os')  # do not remove os it is used later down the line
        tmp_file.write(f"\nwith open(r'{tmp_output_path}', 'w') as out_file:")
        tmp_file.write('\n    out_file.write(str([m.__name__ for m in sys.modules.values() if m]))')
    
    original_dir = os.getcwd()
    try:
        os.chdir(source_dir)
        subprocess.run([sys.executable, tmp_script_path], check=True)
    finally:
        os.chdir(original_dir)
    
    with open(tmp_output_path, "r") as out_file:
        output = out_file.read().strip()
    
    try:
        modules = ast.literal_eval(output)
    except Exception as e:
        logging.error(f"Error parsing modules output: {e}")
        logging.error(f"Output received: {output}")
        modules = []
    
    return modules

def process_imports(source_file_path, packages, keepfile, force_refresh=False):
    source_dir = os.path.dirname(source_file_path)
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)

    # Paths for temporary script and output
    tmp_script_path = os.path.join(source_dir, 'tmp_imports_checker.py')
    tmp_output_path = os.path.join(source_dir, 'tmp_imports_output.txt')

    for tmp_path in [tmp_script_path, tmp_output_path]:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Run checker with raw imports
    info('Getting raw imports')
    raw_imports = getimports.recursive_imports(source_file_path)
    logging.debug(f"Raw imports from file: {raw_imports}")
    info('Running import checker')
    raw_modules = run_import_checker(raw_imports, packages, source_dir, tmp_script_path, tmp_output_path)
    logging.debug(f"Modules from raw imports: {raw_modules}")

    # Clean raw modules
    cleaned_modules = set(mod.split('.')[0] for mod in raw_modules if mod and isinstance(mod, str))
    linked_imports = load_linked_imports(force_refresh)
    cleaned_modules = resolve_linked_imports_recursive(cleaned_modules.union(packages), linked_imports)
    cleaned_modules = sorted(cleaned_modules)
    logging.debug(f"First cleaned modules (with linked deps): {cleaned_modules}")

    # run checker again with cleaned modules
    info('Running import checker again')
    cleaned_modules_result = run_import_checker(cleaned_modules, packages, source_dir, tmp_script_path, tmp_output_path)
    logging.debug(f"Modules from cleaned imports: {cleaned_modules_result}")

    cleaned_modules = set(mod.split('.')[0] for mod in raw_modules if mod and isinstance(mod, str))
    cleaned_modules = resolve_linked_imports_recursive(cleaned_modules.union(packages), linked_imports)
    cleaned_modules = sorted(cleaned_modules)
    logging.debug(f"Final cleaned modules (with linked deps): {cleaned_modules}")

    # Cleanup temporary files
    if not keepfile:
        os.remove(tmp_script_path)
        os.remove(tmp_output_path)

    return cleaned_modules