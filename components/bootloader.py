import os
import sys
import time
import shutil
from zipfile import ZipFile
from datetime import datetime
from random import randint
from subprocess import run

def generate_unique_output_dir(base_path='C:\\Windows\\TEMP\\mrb36'):
    now = datetime.now()
    datetime_int = int(now.strftime("%Y%m%d%H%M%S"))
    random_number = randint(1, 100)
    output_dir = f'{base_path}.{datetime_int}.{random_number}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def generate_random_zip_name():
    # Generate a unique name for the embedded ZIP file
    random_zip_number = randint(1000, 9999)
    return f'embedded_{random_zip_number}.zip'

def find_embedded_zip(data):
    zip_start = data.find(b'PK\x03\x04')
    return zip_start

def extract_embedded_zip(output_dir):
    exe_path = sys.argv[0]
    zip_name = generate_random_zip_name()
    zip_path = os.path.join(output_dir, zip_name)

    # Read binary data from the script/executable
    with open(exe_path, 'rb') as f:
        data = f.read()

    # Locate and extract ZIP archive if present
    zip_start = find_embedded_zip(data)
    if zip_start == -1:
        print("No embedded ZIP archive found.")
        return

    # Write extracted ZIP data to a file
    with open(zip_path, 'wb') as zip_file:
        zip_file.write(data[zip_start:])

    # Extract contents from ZIP and remove the archive
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    os.remove(zip_path)

def run_extracted_executable(output_dir):
    python_executable = os.path.join(output_dir, 'python.exe')
    script_filename = os.path.join(output_dir, 'thefilename')
    
    try:
        with open(script_filename, 'r') as file:
            script_path = os.path.join(output_dir, file.read().strip())
    except FileNotFoundError:
        print(f"File '{script_filename}' not found.")
        return

    # Modify script with sys.path and sys.argv adjustments
    new_text = (
        f"import sys\n"
        f"sys.argv[0] = '{sys.argv[0].replace('\\', '/')}'\n"
        f"sys.executable = '{sys.argv[0].replace('\\', '/')}'\n"
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

    # Execute the script using Python executable with forwarded args
    additional_args = sys.argv[1:]  # Skip the current script name
    run('cls', shell=True)
    run([python_executable, '-B', script_path] + additional_args, shell=True)

def cleanup_directory(output_dir):
    try:
        shutil.rmtree(output_dir)
    except Exception as e:
        print(f"Failed to remove directory: {e}. Retrying...")
        time.sleep(1)
        shutil.rmtree(output_dir, ignore_errors=True)

def main():
    print('Loading...')
    output_dir = generate_unique_output_dir()
    extract_embedded_zip(output_dir)
    run_extracted_executable(output_dir)
    cleanup_directory(output_dir)

if __name__ == "__main__":
    main()