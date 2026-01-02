from os import makedirs, environ, remove, name, chmod
from os.path import join, exists, basename, dirname
from sys import argv
from shutil import rmtree
from pyzipper import AESZipFile, BadZipFile, LargeZipFile
from datetime import datetime
from random import randint
from subprocess import run
from stat import S_IMODE, S_IRWXU, S_IRGRP, S_IXGRP, S_IROTH, S_IXOTH

debug = environ.get('PYCOMPYLEDEBUG')


def generate_unique_output_dir(base_path=None):
    if base_path is None:
        if name == 'nt':
            base_path = join(environ.get('TEMP', r'C:\Windows\TEMP'), 'mrb36')
        else:
            base_path = join('/tmp', 'mrb36')

    output_dir = f'{base_path}.{int(datetime.now().strftime("%Y%m%d%H%M%S"))}.{randint(1, 100)}'
    makedirs(output_dir, exist_ok=True)
    return output_dir


def extract_embedded_zip(output_dir, password):
    exe_path = argv[0]
    bufsize = 1024 * 1024
    offset = 0
    start = -1

    with open(exe_path, 'rb') as f:
        while True:
            chunk = f.read(bufsize)
            if not chunk:
                break
            i = chunk.find(b'PK\x03\x04')
            if i != -1:
                start = offset + i
                break
            offset += len(chunk)

    if start == -1:
        return False
    if debug:
        print('Extracting embedded zip')

    with open(exe_path, 'rb') as f:
        f.seek(start)
        try:
            with AESZipFile(f) as zf:
                zf.pwd = password.encode()
                zf.extractall(output_dir)
        except (RuntimeError, BadZipFile, LargeZipFile) as e:
            print(f"ERROR: Failed to extract ZIP: {e}")
            return False

    return True


def make_executable(path):
    if name != 'nt' and exists(path):
        st = S_IMODE(S_IRWXU | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH)
        chmod(path, st)


def run_extracted_executable(output_dir):
    python_executable = join(output_dir, 'python.exe' if name == 'nt' else 'python')
    script_path = join(output_dir, '__main__.py')

    if not exists(script_path):
        print("ERROR: __main__.py missing")
        return

    if name != 'nt':
        make_executable(python_executable)

    marker_comment = "# PyCompyle custom sys injection above DO NOT EDIT\n"

    new_text = (
        "import sys\n"
        f"sys.argv[0] = r'{argv[0]}'\n"
        f"sys.executable = r'{argv[0]}'\n"
        f"sys.path.insert(0, r'{output_dir}')\n"
    )

    with open(script_path, 'r', encoding='utf-8') as f:
        original = f.read()

    if marker_comment in original:
        _, after = original.split(marker_comment, 1)
        modified = new_text + marker_comment + after.lstrip()
    else:
        modified = new_text + marker_comment + original

    if modified != original:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(modified)

    pyargs = ['-B']
    pyargs_file = join(output_dir, 'pyargs')

    if exists(pyargs_file):
        pyargs = []
        with open(pyargs_file, 'r') as f:
            for line in f:
                pyargs.extend(line.strip().split())

    additional_args = argv[1:]

    if debug:
        print('Starting embedded Python')

    run([python_executable] + pyargs + [script_path] + additional_args, check=False)


def cleanup_directory(output_dir):
    try:
        rmtree(output_dir)
        return True
    except Exception:
        return False


def schedule_startup_folder_deletion(output_dir):
    localappdata = environ['LOCALAPPDATA']
    scripts_dir = join(localappdata, 'TempDeleteScripts')
    makedirs(scripts_dir, exist_ok=True)

    folder_name = basename(output_dir)
    startup_dir = join(
        environ['APPDATA'],
        r'Microsoft\Windows\Start Menu\Programs\Startup'
    )

    bat_path = join(startup_dir, f"delete_{folder_name}.bat")

    with open(bat_path, 'w') as f:
        f.write(f"""@echo off
if exist "{output_dir}" rmdir /s /q "{output_dir}"
del "%~f0"
""")

    return bat_path


def main():
    if debug:
        print('Bootloader started')

    output_dir = generate_unique_output_dir()
    bat_path = None

    if extract_embedded_zip(output_dir, password='PyCompyle'):
        if name == 'nt':
            bat_path = schedule_startup_folder_deletion(output_dir)

        run_extracted_executable(output_dir)

        if cleanup_directory(output_dir) and bat_path:
            remove(bat_path)

    elif exists(join(dirname(argv[0]), '__main__.py')):
        run_extracted_executable(dirname(argv[0]))

    else:
        print('ERROR: No embedded ZIP or __main__.py found')


if __name__ == "__main__":
    main()