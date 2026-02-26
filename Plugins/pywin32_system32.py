# Shutup vars
spec = None
folder_path = None
exclude_pattens = None
def info(*args): pass
import os, shutil

def special_case(import_name='pywin32_system32'):
    shutil.copytree(os.path.join(os.path.dirname(spec.origin), 'pywin32_system32'), os.path.join(folder_path, "lib",'pywin32_system32'))
    info(f"Copied pywin32_system32 for {import_name}")