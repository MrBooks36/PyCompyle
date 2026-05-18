import os
import subprocess
import py_compile
import shutil
import logging
import time
import tempfile
import sys
import platform
import stat
from components.download import download_resourcehacker
from components.compress import compress_folder_with_progress, compress_top_level_pyc, compress_with_upx
from components.plugins import run_end_code
from logging import info, error

MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds


def zip_embeder(output, bootloader, zip_file):
    with open(output, 'wb') as output:
        with open(bootloader, 'rb') as f_exe:
            output.write(f_exe.read())
        with open(zip_file, 'rb') as f_zip:
            output.write(f_zip.read())


def delete_pycache(start_dir):
    deleted_count = 0

    for root, dirs, _ in os.walk(start_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                deleted_count += 1
            except Exception as e:
                error(f"Error deleting {pycache_path}: {e}")

    logging.debug(f"Total '__pycache__' folders deleted: {deleted_count}")


def create_executable(output_file, bootloader, no_console, zip_path=None):
    exe_folder = os.path.join(os.path.dirname(sys.modules["__main__"].__file__), 'EXEs')  # type: ignore
    if not os.path.exists(exe_folder):
        logging.critical("EXEs folder not found")
        sys.exit(1)

    bootloader_map = {
        (False, False): "bootloader.exe",
        (True, False): "bootloaderw.exe",
        (False, True): "bootloader",
        (True, True): "bootloaderw",
    }

    if not bootloader:
        bootloader = bootloader_map[(no_console, platform.system() == "Linux")]
        bootloader = os.path.join(exe_folder, bootloader)
    else:
        info(f'Using custom bootloader: "{bootloader}"')

    if zip_path is not None:
        zip_embeder(output_file, bootloader, zip_path)
    else:
        shutil.copyfile(bootloader, output_file)

    if platform.system() == "Linux":
        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | stat.S_IXUSR)


def compile_and_replace_py_to_pyc(folder, name="lib"):
    directory = os.path.join(folder, name)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_file_path = os.path.join(root, file)

                temp_dir = r'C:\Windows\Temp' if os.name == 'nt' else '/tmp'

                temp_dir = tempfile.mkdtemp(dir=temp_dir)
                try:
                    temp_file_path = os.path.join(temp_dir, file)

                    shutil.copy2(py_file_path, temp_file_path)
                    pyc_file_path = py_file_path + 'c'

                    try:
                        display_file_path = os.path.relpath(py_file_path, directory)
                        py_compile.compile(temp_file_path, cfile=pyc_file_path, dfile=display_file_path, doraise=True)
                        os.remove(py_file_path)

                    except py_compile.PyCompileError as compile_error:
                        logging.error(f"Failed to compile {py_file_path}: {compile_error}")
                    except Exception as e:
                        error(f"An error occurred with {py_file_path}: {e}")

                finally:
                    shutil.rmtree(temp_dir)


def compile_main(folder_path):
    main_file = os.path.join(folder_path, '__main__.py')
    with open(main_file, 'r') as f:
        original_content = f.read()

    modified_content = "__name__ = '__main__'\n" + original_content

    with open(main_file, 'w') as f:
        f.write(modified_content)

    pyc_file_path = main_file.replace('__main__', '__init__') + 'c'
    display_file_path = os.path.relpath(main_file, folder_path)
    py_compile.compile(main_file, cfile=pyc_file_path, dfile=display_file_path, doraise=True)

    with open(main_file, 'w') as f:
        f.write('import __init__')


def add_icon_to_executable(exe_path, icon_path, noconfirm):
    cache_path = os.path.expandvars(
        '%LOCALAPPDATA%\\PyCompyle.cache') if os.name == 'nt' else os.path.expanduser('~/.cache/PyCompyle.cache')
    os.makedirs(cache_path, exist_ok=True)
    logging.debug(f'Cache path: {cache_path}')

    if not os.path.exists(os.path.join(cache_path, 'resource_hacker')):
        info('Downloading ResourceHacker...')
        if download_resourcehacker(cache_path, noconfirm) is None:
            logging.info("Skipping icon")
            return

    r_hacker_path = os.path.join(cache_path, 'resource_hacker', 'ResourceHacker.exe')
    command = [
        r_hacker_path,
        "-open", exe_path,
        "-save", exe_path,
        "-action", "add",
        "-res", icon_path,
        "-mask", "ICONGROUP,MAINICON"
    ]
    subprocess.run(command)


def add_uac(file_path, noconfirm):
    info('Adding UAC to executable...')
    manifest_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
"""

    fd, manifest_path = tempfile.mkstemp(suffix=".manifest")
    os.close(fd)
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)

    cache_path = (
        os.path.expandvars("%LOCALAPPDATA%\\PyCompyle.cache")
        if os.name == "nt"
        else os.path.expanduser("~/.cache/PyCompyle.cache")
    )
    os.makedirs(cache_path, exist_ok=True)
    logging.debug(f"Cache path: {cache_path}")
    r_hacker_path = os.path.join(cache_path, "resource_hacker", "ResourceHacker.exe")

    if not os.path.exists(r_hacker_path):
        info("Downloading ResourceHacker...")
        if download_resourcehacker(cache_path, noconfirm) is None:
            logging.info("Skipping UAC...")
            return
    command = [
        r_hacker_path,
        "-open", file_path,
        "-save", file_path,
        "-action", "addoverwrite",
        "-res", manifest_path,
        "-mask", "MANIFEST,1,"
    ]
    subprocess.run(command)
    os.remove(manifest_path)


def write_pth(folder_path):
    with open(os.path.join(folder_path, 'python._pth'), 'w') as file:
        file.write('DLLs\nlib\nlib_c.zip\nlocal\n.')


def main(folder_path, args):
    folder_name = os.path.basename(folder_path).removesuffix('.build')
    zip_path = f"{folder_name}.zip"

    info('Removing __pycache__ directories...')
    delete_pycache(folder_path)

    if not args.disable_compile:
        info("Generating byte-code")
        compile_and_replace_py_to_pyc(folder_path)
        compile_and_replace_py_to_pyc(folder_path, "local")
        compile_main(folder_path)

    if not args.disable_python_environment:
        info('Writing python args')
        write_pth(folder_path)

    if not any((args.disable_bootloader, args.disable_python_environment, args.bat)) and args.pyarg:
        pyargs = list(args.pyarg or [])
        if pyargs:
            with open(os.path.join(folder_path, 'pyargs'), 'w') as file:
                file.write('\n'.join(pyargs) + '\n')

    if not args.disable_lib_compressing:
        compress_top_level_pyc(
            os.path.join(folder_path, "lib"),
            output_name=os.path.join(folder_path, "lib_c"),
        )

    if args.upx_threads not in (0, None, "0"):
        compress_with_upx(folder_path, args.upx_threads, args.noconfirm)

    if not args.folder:
        compress_folder_with_progress(
            folder_path,
            zip_path,
            password=None if args.disable_password else 'PyCompyle'
        )
    else:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if os.path.exists(folder_name):
                    shutil.rmtree(folder_name)
                new_path = os.path.splitext(folder_name)[0]
                new_path = os.path.abspath(new_path)
                shutil.move(folder_path, new_path)
                folder_path = new_path
                zip_path = None
                break
            except OSError as e:
                logging.warning(f"Attempt {attempt} failed to rename {folder_path} -> {folder_name}: {e}")
                if attempt == MAX_RETRIES:
                    logging.critical(f"Failed to rename {folder_path} after {MAX_RETRIES} attempts. Exiting.")
                    sys.exit(1)
                time.sleep(RETRY_DELAY)

    exe_path = os.path.join(folder_path, f'{folder_name}.exe') if args.folder else f'{folder_name}.exe'


    if args.bat:
        info('Creating Batchfile...')
        bat_path = os.path.join(folder_path, f'{folder_name}.bat')
        with open(bat_path, 'w') as file:
            file.write(f'@echo off\n"%~dp0\\python.exe" {args} "%~dp0\\__main__.py"')
    elif not args.disable_bootloader:
        info('Creating executable...')
        create_executable(
            exe_path,
            args.bootloader,
            args.windowed,
            zip_path,
        )

    if args.icon:
        if os.path.exists(args.icon):
            if args.icon.endswith(".ico"):
                info(f'Adding icon: {args.icon}')
                add_icon_to_executable(exe_path, args.icon, args.noconfirm)
            else:
                error(f"Not an icon file: {args.icon}")
        else:
            error(f'Icon file not found: {args.icon}')

    if args.uac:
        add_uac(exe_path, args.noconfirm)

    if args.zip:
        compress_folder_with_progress(folder_path, folder_name)

    end_code = run_end_code()
    if end_code:
        exec('\n'.join(end_code), globals(), locals())

    if not args.keepfiles and not args.folder:
        info('Cleaning up...')
        shutil.rmtree(folder_path, ignore_errors=True)
        if os.path.exists(folder_path):  # this is redundant
            shutil.rmtree(folder_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)

    info("Done!")
