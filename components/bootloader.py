from os import makedirs, remove
from os.path import exists, join
from sys import argv
from zipfile import ZipFile
from datetime import datetime
from random import randint
from subprocess import run
from shutil import rmtree

now = datetime.now()
datetime_int = int(now.strftime("%Y%m%d%H%M%S"))

random_number = randint(1, 100)

output_dir=f'C:\\Windows\\TEMP\\mrb36.{datetime_int}.{random_number}'

def extract_embedded_zip():
    # Get the path of this script
    zip_path = join(output_dir,'embedded.zip')
    exe_path = argv[0]

    # Open the script/executable in binary mode
    with open(exe_path, 'rb') as f:
            data = f.read()

    # Find the ZIP file start based on its signature
    zip_start = data.find(b'PK\x03\x04')
    if zip_start == -1:
        print("No embedded ZIP archive found.")
        return
            
    # Ensure output directory exists
    if not exists(output_dir):
     makedirs(output_dir)

    # Extract the ZIP archive from the binary data
    zip_data = data[zip_start:]
    with open(zip_path, 'wb') as zip_file:
        zip_file.write(zip_data)

    # Extract the contents of the ZIP file
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    remove(zip_path)  # Clean up the ZIP file

def run_exe():
    python = join(output_dir, 'python.exe')
    script_path = join(output_dir, open(join(output_dir, 'thefilename'), 'r').read())

    # Define the text to prepend
    new_text = f"import sys\nsys.argv[0] = '{argv[0].replace('\\','/')}'\nsys.executable = '{argv[0].replace('\\','/')}'\nsys.path.append(r'{output_dir}')\n"

    # Open the file in read mode to get its current content
    with open(script_path, "r") as file:
     original_content = file.read()

    # Open the file in write mode to overwrite it with the new content
    with open(script_path, "w") as file:
     file.write(new_text + original_content)
    
    # Forward all extra args passed to the current script
    args = argv[1:]  # skip current script name
    run('cls', shell=True)
    run([python, '-B', script_path] + args, shell=True)
    try: rmtree(output_dir)
    except: pass

def main():
    print('Loading...')
    extract_embedded_zip()
    run_exe()

if __name__ == "__main__":
    main()