from os import makedirs, environ, remove
from os.path import join, exists, basename, dirname
from sys import argv
from shutil import rmtree
from pyzipper import AESZipFile, BadZipFile, LargeZipFile
from datetime import datetime
from random import randint
from subprocess import run


def generate_unique_output_dir(base_path=None):
    if base_path is None:
        base_path = join(environ.get('TEMP', r'C:\Windows\TEMP'), 'mrb36')

    output_dir = f'{base_path}.{int(datetime.now().strftime("%Y%m%d%H%M%S"))}.{randint(1, 100)}'
    if not exists(output_dir):
        makedirs(output_dir)
    return output_dir


def extract_embedded_zip(output_dir: str, password: str) -> bool:
    exe_path = argv[0]
    bufsize = 1024*1024
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
        if not exists(join(dirname(exe_path), '__main__.py')):
            print("ERROR: No embedded ZIP found.")
        return False
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


def run_extracted_executable(output_dir):
    python_executable = join(output_dir, 'python.exe')
    script_path = join(output_dir, "__main__.py")

    marker_comment = "# PyCompyle custom sys injection above DO NOT EDIT\n"

    new_text = (
        "import sys\n"
        f"sys.argv[0] = r'{argv[0]}'\n"
        f"sys.executable = r'{argv[0]}'\n"
        f"sys.path.append(r'{output_dir}')\n"
    )

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Detect if marker exists
        if marker_comment in original_content:
            # Replace everything above the marker
            _, after_marker = original_content.split(marker_comment, 1)
            # Strip any old sys modifications above marker
            modified_content = new_text + marker_comment + after_marker.lstrip()
        else:
            # No marker: prepend sys modifications + marker
            modified_content = new_text + marker_comment + original_content

        # Avoid rewriting if content is identical
        if modified_content != original_content:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

    except FileNotFoundError:
        print(f"Script path '{script_path}' not found.")
        return
    
    pyargs = ['-B']
    pyargs_file = join(output_dir, 'pyargs')

    if exists(pyargs_file):
     pyargs = []
     with open(pyargs_file, 'r') as f:
        for line in f:
            pyargs.extend(line.strip().split())

    additional_args = argv[1:]

    run([python_executable] + pyargs + [output_dir] + additional_args)


def cleanup_directory(output_dir):
    try:
        rmtree(output_dir)
        return True
    except Exception:
        return False


def schedule_startup_folder_deletion(output_dir):
    global bat_path
    localappdata = environ['LOCALAPPDATA']
    scripts_dir = join(localappdata, 'TempDeleteScripts')
    makedirs(scripts_dir, exist_ok=True)

    folder_name = basename(output_dir)
    startup_dir = join(
            environ['APPDATA'],
            r'Microsoft\Windows\Start Menu\Programs\Startup'
    )
    bat_filename = f"delete_{folder_name}.bat"
    bat_path = join(startup_dir, bat_filename)


    with open(bat_path, 'w') as f:
        f.write(f"""@echo off
echo "Hi. The reason you can see this is because a program ended unexpectedly and a temporary folder was not deleted"
echo "We are deleting it now so there is no reason to be alarmed"
if exist "{output_dir}" (
    rmdir /s /q "{output_dir}"
)
del "%~f0"
""")


def main():
 output_dir = generate_unique_output_dir()
 if extract_embedded_zip(output_dir, password='PyCompyle'):
     schedule_startup_folder_deletion(output_dir)
     run_extracted_executable(output_dir)
     if cleanup_directory(output_dir):
        remove(bat_path)
 elif exists(join(dirname(argv[0]), '__main__.pyc')):
     rmtree(output_dir)
     folder = dirname(argv[0])
     run_extracted_executable(folder)
 else:
     print('No emmbeded zip or __main__.pyc found')


if __name__ == "__main__":
    main()