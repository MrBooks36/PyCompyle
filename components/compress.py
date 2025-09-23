import os, shutil, logging, pyzipper, subprocess
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info
try:
    from components.download import install_upx
except ImportError:
    from PyCompyle.components.download import install_upx

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

def compress_top_level_pyc(lib_folder, output_name="Lib_c"):
    if not os.path.exists(lib_folder):
        logging.error(f"Lib folder not found: {lib_folder}")
        return

    lib_c_path = os.path.join(os.path.dirname(lib_folder), output_name)
    if os.path.exists(lib_c_path):
        shutil.rmtree(lib_c_path)
    os.makedirs(lib_c_path, exist_ok=True)

    # Move top-level .pyc files
    for item in os.listdir(lib_folder):
        item_path = os.path.join(lib_folder, item)
        if os.path.isfile(item_path) and item_path.endswith(".pyc"):
            shutil.move(item_path, lib_c_path)

    # Move top-level folders containing only .pyc files
    for item in os.listdir(lib_folder):
        item_path = os.path.join(lib_folder, item)
        if os.path.isdir(item_path):
            only_pyc = all(f.endswith(".pyc") for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))
            if only_pyc:
                shutil.move(item_path, lib_c_path)

    # Remove empty folders in original Lib
    for root, dirs, files in os.walk(lib_folder, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                shutil.rmtree(dir_path)

    # Compress Lib_c using your existing function (no password)
    compress_folder_with_progress(lib_c_path, output_name, password=None, text='INFO: Compressing top-level PYC files')

    # Delete the temporary Lib_c folder
    shutil.rmtree(lib_c_path)

def compress_with_upx(folder_path):
    extensions = [".exe", ".dll", ".pyd", ".so"]

    upx_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PyCompyle.cache", "upx.exe")
    if not os.path.exists(upx_path):
        info("UPX not found, downloading...")
        upx_path = install_upx()
        if not upx_path:
            logging.error("Failed to install UPX. Compression will be skipped.")
            return
    
    # Gather all files to compress
    files_to_compress = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                # Skip common problematic system/runtime files
                if file.lower().startswith(("qwindows", "vcruntime")):
                    continue
                files_to_compress.append(os.path.join(root, file))

    def compress_file(file_path):
        subprocess.run([upx_path, "--brute", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    with ThreadPoolExecutor() as executor:
        # Submit all tasks to the executor
        futures = {executor.submit(compress_file, file_path): file_path for file_path in files_to_compress}
        
        # Use tqdm to show progress
        with tqdm(total=len(files_to_compress), desc="INFO: Compressing binary files with UPX", unit="file") as pbar:
            for future in as_completed(futures):
                try:
                    future.result()  # Catch exceptions raised during compression
                except Exception as e:
                    logging.error(f"Error compressing {futures[future]}: {e}")
                pbar.update(1)

def compress_file_with_upx(file_path):
    upx_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PyCompyle.cache", "upx.exe")
    if not os.path.exists(upx_path):
        info("UPX not found, downloading...")
        upx_path = install_upx()
        if not upx_path:
            logging.error("Failed to install UPX. Compression will be skipped.")
            return

    if os.path.isfile(file_path):
        subprocess.run([upx_path, "--brute", '--force', file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)