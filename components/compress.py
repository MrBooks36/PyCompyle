import os, shutil, logging, pyzipper, subprocess, hashlib, time, stat
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info
try:
    from components.download import install_upx
except ImportError:
    from PyCompyle.components.download import install_upx # type: ignore

def compress_folder_with_progress(folder_path, output_zip_name, password=None, compression_level=6, text='INFO: Zipping'):
    total_size = sum(
        os.path.getsize(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
    )

    encryption = pyzipper.WZ_AES if password else None

    with tqdm(total=total_size, unit='B', unit_scale=True, desc=text) as pbar, \
         pyzipper.AESZipFile(
             f"{output_zip_name}.zip",
             'w',
             compression=pyzipper.ZIP_DEFLATED,
             compresslevel=compression_level,
             encryption=encryption
         ) as zipf:

        if password:
            zipf.setpassword(password.encode('utf-8'))

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
                pbar.update(os.path.getsize(file_path))

def compress_top_level_pyc(lib_folder, output_name="lib_c"):
    lib_c_path = os.path.join(os.path.dirname(lib_folder), output_name)
    if os.path.exists(lib_c_path):
        shutil.rmtree(lib_c_path)
    os.makedirs(lib_c_path, exist_ok=True)

    # Move top-level .pyc files
    for item in os.listdir(lib_folder):
        item_path = os.path.join(lib_folder, item)
        if os.path.isfile(item_path) and item_path.endswith((".pyc", ".py")):
            shutil.move(item_path, lib_c_path)

    # Move top-level folders containing only .pyc or py files
    for item in os.listdir(lib_folder):
        item_path = os.path.join(lib_folder, item)
        if os.path.isdir(item_path):
            only_pyc_or_py = all(
                f.endswith((".pyc", ".py"))
                for root, _, files in os.walk(item_path)
                for f in files
                if os.path.isfile(os.path.join(root, f))
                )
            if only_pyc_or_py:
                shutil.move(item_path, lib_c_path)

    # Remove empty folders in original lib
    for root, dirs, files in os.walk(lib_folder, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                shutil.rmtree(dir_path)

    compress_folder_with_progress(lib_c_path, output_name, password=None, text='INFO: Compressing top-level python files')

    shutil.rmtree(lib_c_path)

def compress_with_upx(folder_path, threads):
    max_workers = max(1, os.cpu_count() // 2) if not threads else int(threads)
    if max_workers <= 0:
        return

    is_windows = os.name == "nt"

    extensions = (".exe", ".dll", ".pyd", ".so", ".bin")

    base_cache = os.path.join(
        os.environ.get("LOCALAPPDATA") if is_windows else os.path.expanduser("~/.cache"),
        "PyCompyle.cache"
    )

    upx_path = os.path.join(base_cache, "upx.exe" if is_windows else "upx")
    upx_cache = os.path.join(base_cache, "upxcache")
    os.makedirs(upx_cache, exist_ok=True)

    if not os.path.exists(upx_path):
        info("UPX not found, downloading...")
        upx_path = install_upx()
        if not os.path.exists(upx_path):
            logging.error("Failed to install UPX. Compression will be skipped.")
            return

    if not is_windows:
        st = os.stat(upx_path)
        if not (st.st_mode & stat.S_IXUSR):
            os.chmod(upx_path, st.st_mode | stat.S_IXUSR)           


    def hash_file(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    files_to_compress = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions or os.access(file, os.X_OK)):
                if file.lower().startswith(("qwindows", "vcruntime")):
                    continue
                files_to_compress.append(os.path.join(root, file))

    def compress_file(file_path):
        file_hash = hash_file(file_path)
        cached_file = os.path.join(upx_cache, f"{file_hash}.bin")

        if os.path.exists(cached_file):
            os.utime(cached_file, None)  # refresh last access time
            shutil.copy2(cached_file, file_path)
            return

        temp_compressed = file_path + ".tmp"
        try:
            subprocess.run([upx_path, "--brute", "-o", temp_compressed, file_path],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)
            shutil.move(temp_compressed, file_path)
            shutil.copy2(file_path, cached_file)
        except subprocess.CalledProcessError:
            if os.path.exists(temp_compressed):
                os.remove(temp_compressed)

    logging.debug(f'Using {max_workers} threads for UPX compression')

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compress_file, f): f for f in files_to_compress}
        with tqdm(total=len(files_to_compress),
                  desc="INFO: Compressing binary files with UPX", unit="file") as pbar:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error compressing {futures[future]}: {e}")
                pbar.update(1)

    # Remove stale cache files
    now = time.time()
    max_age = 30 * 24 * 3600  # 30 days in seconds
    for name in os.listdir(upx_cache):
        path = os.path.join(upx_cache, name)
        try:
            if os.path.isfile(path):
                last_used = os.path.getatime(path)
                if now - last_used > max_age:
                    os.remove(path)
                    logging.debug(f"Removed stale cache file: {name}")
        except Exception as e:
            logging.warning(f"Failed to check/remove cache file {name}: {e}")

def compress_file_with_upx(file_path):
    is_windows = os.name == "nt"
    base_cache = os.path.join(
        os.environ.get("LOCALAPPDATA") if is_windows else os.path.expanduser("~/.cache"),
        "PyCompyle.cache"
    )

    upx_path = os.path.join(base_cache, "upx.exe" if is_windows else "upx")
    upx_cache = os.path.join(base_cache, "upxcache")
    os.makedirs(upx_cache, exist_ok=True)

    if not os.path.exists(upx_path):
        info("UPX not found, downloading...")
        upx_path = install_upx()
        if not upx_path or not os.path.exists(upx_path):
            logging.error("Failed to install UPX. Compression will be skipped.")
            return

    if os.path.isfile(file_path):
        subprocess.run([upx_path, "--brute", '--force', file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)