from os import makedirs, path, environ
from sys import argv
from shutil import rmtree
from zipfile import ZipFile
from datetime import datetime
from random import randint
from subprocess import run
from pythoncom import CoInitialize
from win32com.client import Dispatch


def generate_unique_output_dir(base_path=None):
    if base_path is None:
        base_path = path.join(environ.get('TEMP', r'C:\Windows\TEMP'), 'mrb36')
    now = datetime.now()
    datetime_int = int(now.strftime("%Y%m%d%H%M%S"))
    random_number = randint(1, 100)
    output_dir = f'{base_path}.{datetime_int}.{random_number}'
    if not path.exists(output_dir):
        makedirs(output_dir)
    return output_dir


def generate_random_zip_name():
    random_zip_number = randint(1000, 9999)
    return f'embedded_{random_zip_number}.zip'


def find_embedded_zip(data):
    zip_start = data.find(b'PK\x03\x04')
    return zip_start


def extract_embedded_zip(output_dir):
    exe_path = argv[0]
    zip_name = generate_random_zip_name()
    zip_path = path.join(output_dir, zip_name)

    with open(exe_path, 'rb') as f:
        data = f.read()

    zip_start = find_embedded_zip(data)
    if zip_start == -1:
        print("No embedded ZIP archive found.")
        return

    with open(zip_path, 'wb') as zip_file:
        zip_file.write(data[zip_start:])

    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    try:
        path.remove(zip_path)
    except AttributeError:
        # os.path has no remove, fallback to os.remove
        import os
        os.remove(zip_path)


def run_extracted_executable(output_dir):
    python_executable = path.join(output_dir, 'python.exe')
    script_filename = path.join(output_dir, 'thefilename')

    try:
        with open(script_filename, 'r') as file:
            script_path = path.join(output_dir, file.read().strip())
    except FileNotFoundError:
        print(f"File '{script_filename}' not found.")
        return

    new_text = (
        f"import sys\n"
        f"sys.argv[0] = '{argv[0].replace('\\', '/')}'\n"
        f"sys.executable = '{argv[0].replace('\\', '/')}'\n"
        f"sys.path.append(r'{output_dir}')\n"
    )

    try:
        with open(script_path, 'r') as original_file:
            original_content = original_file.read()

        with open(script_path, 'w') as modified_file:
            modified_file.write(new_text + original_content)
    except FileNotFoundError:
        print(f"Script path '{script_path}' not found.")
        return

    additional_args = argv[1:]
    #run('cls', shell=True)
    run([python_executable, '-B', script_path] + additional_args)


def cleanup_directory(output_dir):
    try:
        rmtree(output_dir)
    except Exception as e:
        print(f"Failed to remove directory: {e}. Scheduling deletion on next login.")
        schedule_startup_folder_deletion(output_dir)


def schedule_startup_folder_deletion(output_dir):
    """
    Creates batch and VBScript in %LOCALAPPDATA%\TempDeleteScripts,
    then places the VBScript directly into the user's Startup folder
    to run silently on next login.
    """
    try:
        localappdata = environ['LOCALAPPDATA']
        scripts_dir = path.join(localappdata, 'TempDeleteScripts')
        makedirs(scripts_dir, exist_ok=True)

        folder_name = path.basename(output_dir)
        bat_filename = f"delete_{folder_name}.bat"
        bat_path = path.join(scripts_dir, bat_filename)

        with open(bat_path, 'w') as f:
            f.write(f"""@echo off
timeout /t 3 >nul
rmdir /s /q "{output_dir}"
del "%~f0"
""")

        vbs_filename = f"run_delete_{folder_name}.vbs"

        startup_dir = path.join(
            environ['APPDATA'],
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        vbs_path = path.join(startup_dir, vbs_filename)

        with open(vbs_path, 'w') as f:
            # VBScript runs batch hidden with 0 window style, non-blocking
            f.write(f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "{bat_path}", 0, False
''')

        print(f"Scheduled deletion: batch in '{bat_path}', VBScript in Startup '{vbs_path}'")

    except Exception:
        print("Failed to schedule folder deletion on startup.")



def main():
    print('Loading...')
    output_dir = generate_unique_output_dir()
    extract_embedded_zip(output_dir)
    schedule_startup_folder_deletion(output_dir)
    run_extracted_executable(output_dir)
    cleanup_directory(output_dir)


if __name__ == "__main__":
    main()