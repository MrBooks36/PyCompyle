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


def extract_embedded_zip(output_dir, password: str) -> bool:
    with open(argv[0], 'rb') as f:
        data = f.read()

    # Locate the embedded ZIP magic header
    zip_start = data.find(b'PK\x03\x04')
    if zip_start == -1:
        print("ERROR: No embedded ZIP found in executable.")
        return False

    zip_name = f'embedded_{randint(1000, 9999)}.zip'
    zip_path = join(output_dir, zip_name)

    # Dump the embedded archive to disk temporarily
    with open(zip_path, 'wb') as zip_file:
        zip_file.write(data[zip_start:])

    try:
        with AESZipFile(zip_path, 'r') as zip_ref:
            zip_ref.pwd = password.encode('utf-8')
            zip_ref.extractall(path=output_dir)
    except (RuntimeError, BadZipFile, LargeZipFile) as e:
        print(f"ERROR: Failed to extract ZIP file: {e}")
        return False
    finally:
        try:
            remove(zip_path)
        except FileNotFoundError:
            pass

    return True


def run_extracted_executable(output_dir):
    python_executable = join(output_dir, 'python.exe')
    script_path = join(output_dir, "__main__.py")

    new_text = (
        "import sys\n"
        f"sys.argv[0] = 'r{argv[0]}'\n"
        f"sys.executable = r'{argv[0]}'\n"
        f"sys.path.append(r'{output_dir}')\n"
    )

    try:
        with open(script_path, 'r', encoding='utf-8') as original_file:
            original_content = original_file.read()

        # Check if sys modifications are already in the script
        if not original_content.startswith(new_text.strip()):
            with open(script_path, 'w', encoding='utf-8') as modified_file:
                modified_file.write(new_text + original_content)

    except FileNotFoundError:
        print(f"Script path '{script_path}' not found.")
        return

    additional_args = argv[1:]
    run([python_executable, '-B', output_dir] + additional_args)


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
 elif exists(join(dirname(argv[0]), '__main__.py')):
     remove(output_dir)
     folder = dirname(argv[0])
     run_extracted_executable(folder)
 else:
     print('No emmbeded zip or __main__.py found')


if __name__ == "__main__":
    main()