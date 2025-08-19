import os, subprocess, py_compile, shutil, logging, pyzipper, time, tempfile, sys
try:
 from components.download import download_and_extract_zip
except ImportError:
 from download import download_and_extract_zip
from logging import info, error
from tqdm import tqdm


def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def zip_embeder(name, exe_file, zip_file):
        setup_logging()
        output_file = os.path.join(os.getcwd(), f'{name}.exe')

        with open(output_file, 'wb') as output:
            with open(exe_file, 'rb') as f_exe:
                output.write(f_exe.read())
            with open(zip_file, 'rb') as f_zip:
                output.write(f_zip.read())

        info(f"Combined executable created: {output_file}")



def compress_folder_with_progress(folder_path, output_zip_name, password=None, compression_level=6):
    total_size = sum(
        os.path.getsize(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
    )
    
    encryption = pyzipper.WZ_AES if password else None

    with tqdm(total=total_size, unit='B', unit_scale=True, desc='INFO: Compressing') as pbar, \
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


def delete_pycache(start_dir):
    """Deletes __pycache__ directories recursively."""
    deleted_count = 0

    for root, dirs, _ in os.walk(start_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                deleted_count += 1
            except Exception as e:
                error(f"Error deleting {pycache_path}: {e}")

    info(f"Total '__pycache__' folders deleted: {deleted_count}")


def create_executable(name, zip_path, no_console=False, uac=False, folder=False, folder_path=str()):
    """Creates an executable file using the zip_embeder."""
    exe_folder = os.path.join(os.path.dirname(sys.modules["__main__"].__file__), 'EXEs')  # type: ignore
    
    bootloader_map = {
        (False, False): "bootloader.exe",
        (False, True): "bootloader_uac.exe",
        (True, False): "bootloaderw.exe",
        (True, True): "bootloaderw_uac.exe",
    }
    
    bootloader = bootloader_map[(no_console, uac)]
    if not folder: zip_embeder(name, os.path.join(exe_folder, bootloader), zip_path)
    else: shutil.copy2(src=os.path.join(exe_folder, bootloader), dst=os.path.join(folder_path, f'{name}.exe'))


def compile_and_replace_py_to_pyc(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_file_path = os.path.join(root, file)

                # Specify the base directory for temporary files
                windows_temp_dir = r'C:\Windows\Temp'
                
                # Create a temporary directory within C:\Windows\Temp
                temp_dir = tempfile.mkdtemp(dir=windows_temp_dir)
                try:
                    temp_file_path = os.path.join(temp_dir, file)

                    # Copy the .py file to the temporary directory
                    shutil.copy2(py_file_path, temp_file_path)

                    # Prepare the destination .pyc file path
                    pyc_file_path = py_file_path + 'c'

                    try:
                        # Use relative path for display file name
                        display_file_path = os.path.relpath(py_file_path, directory)

                        # Compile the .py file in the temporary directory
                        py_compile.compile(temp_file_path, cfile=pyc_file_path, dfile=display_file_path, doraise=True)

                        # Remove the original .py file after successful compilation
                        os.remove(py_file_path)

                    except py_compile.PyCompileError as compile_error:
                        print(f"Failed to compile {py_file_path}: {compile_error}")
                    except Exception as e:
                        print(f"An error occurred with {py_file_path}: {e}")

                finally:
                    # Clean up the temporary directory
                    shutil.rmtree(temp_dir)


def add_icon_to_executable(name, icon_path, folder):
    """Adds an icon to an executable using Resource Hacker."""
    name = os.path.abspath(name)
    cache_path = os.path.expandvars('%LOCALAPPDATA%\\PyCompyle.cache')
    os.makedirs(cache_path, exist_ok=True)
    info(f'Cache path: {cache_path}')

    if not os.path.exists(os.path.join(cache_path, 'resource_hacker')):
        info('Downloading ResourceHacker...')
        download_and_extract_zip('https://www.angusj.com/resourcehacker/resource_hacker.zip', cache_path)

    r_hacker_path = os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')
    if folder: command = f'"{r_hacker_path}" -open "{name}.exe" -save "{name}.exe" -action add -res "{icon_path}" -mask ICONGROUP,MAINICON'
    else: command = f'"{r_hacker_path}" -open "{name}.exe" -save "{name}.exe" -action add -res "{icon_path}" -mask ICONGROUP,MAINICON'
    subprocess.run(command, shell=True)


def main(folder_path, no_console=False, keepfiles=False, icon_path=None, uac=False, folder=False, zip=False, bat=False, disable_compiling=False):
    """Main function to execute the operations."""
    setup_logging()
    folder_name = os.path.basename(folder_path).replace('.build', '')

    info('Removing __pycache__ directories...')
    delete_pycache(folder_path)
    delete_pycache(os.getcwd())
    if not disable_compiling:
     info("Compiling code to PYC files for speed")
     compile_and_replace_py_to_pyc(os.path.join(folder_path, "Lib"))

    info('Writing python args')
    with open(os.path.join(folder_path, 'python._pth'), 'w') as file:
        file.write('Dlls\nLib')

    if not folder: compress_folder_with_progress(folder_path, folder_name, password='PyCompyle')
    else: 
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        try:
            os.rename(folder_path, folder_name) 
        except:
            time.sleep(3)
            os.rename(folder_path, folder_name)
        finally:
            folder_path = folder_path.replace('.build', '')      
    if bat:
        info('Creating Batchfile...')
        with open(os.path.join(folder_path, f'{folder_name}.bat'), 'w') as file:
            file.write('@echo off\n%~dp0\\python.exe %~dp0\\__main__.py')
    else:
        info('Creating executable...')
        create_executable(folder_name, f"{folder_name}.zip", no_console, uac, folder, folder_path)

    if icon_path:
        if os.path.exists(icon_path):
            info(f'Adding icon: {icon_path}')
            add_icon_to_executable(folder_name, icon_path, folder)
        else:
            error(f'Icon file not found: {icon_path}')

    if zip: compress_folder_with_progress(folder_path, folder_name)       

    if not keepfiles and not folder:
        info('Cleaning up...')
        shutil.rmtree(folder_path)
        os.remove(f"{folder_name}.zip")
    if zip and not keepfiles:
        info('Cleaning up...')
        shutil.rmtree(folder_path)