# Shutup vars
def copy_folder_with_excludes(*args): pass
spec = None
folder_path = None
exclude_pattens = None
def info(*args): pass
import os

def special_case(import_name='pythoncom'):
    copy_folder_with_excludes(
                os.path.join(os.path.dirname(spec.origin), 'pywin32_system32'),
                os.path.join(folder_path, "Lib",'pywin32_system32'),
                exclude_patterns=exclude_pattens)
    info(f"Copied pywin32_system32 for {import_name}")


def init(args):
    for package in ["pythoncom", "traceback", "winerror", "glob", "win32event", "pickle"]:
        if package not in args.package:
            args.package.append(package)    