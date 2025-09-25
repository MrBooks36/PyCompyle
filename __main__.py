import os, sys, platform, shutil, logging, argparse
from getpass import getpass
from logging import info
try:
    from components.imports import importcheck
    from components.copylogic import exclude_pattens
    from components import makexe, copylogic
    from components.plugins import load_plugin, get_special_cases
except: 
    from PyCompyle.components.imports import importcheck # type: ignore
    from PyCompyle.components import makexe, copylogic  # type: ignore
    from PyCompyle.components.imports import importcheck # type: ignore
    from PyCompyle.components.copylogic import exclude_pattens # type: ignore
    from PyCompyle.components.plugins import load_plugin # type: ignore


exclude_pattens = ['__pycache__', '.git', '.github', '.gitignore', 'readme*', 'licence*', '.vscode']

def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def check_system():
    # Get architecture, operating system, and machine details
    arch, _ = platform.architecture()
    system = platform.system()
    machine = platform.machine()
    release = platform.release()

    # Check if the system is Windows, 64-bit, and x86_64 architecture
    if system == "Windows" and arch == "64bit" and machine in ["x86_64", "AMD64"]:
        # Split release number into major and minor parts
        major_minor = release.split('.')
        major_version = int(major_minor[0])

        # Check if the major version is 10 or higher, or is 6 and minor version is 3 or higher
        if major_version > 6 or (major_version == 6 and len(major_minor) > 1 and int(major_minor[1]) >= 3):
            return True

    return False  

def validate_platform():
    if not check_system():
        print("PyCompyle is designed to run only on Windows 64-bit.")
        sys.exit(1)

def setup_destination_folder(source_file):
    destination_folder = os.path.abspath(source_file.replace('.py', '.build'))
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder)
    return destination_folder


def main():
    validate_platform()

    parser = argparse.ArgumentParser(description="Package a Python script into a EXE with its dependencies.", prog='python -m PyCompyle')
    parser.add_argument('source_file', help='The Python script to package.')
    parser.add_argument('--noconfirm', '-nc', action='store_true', help='Skip confirmation for wrapping the exe', default=False)
    parser.add_argument('--folder', '-f', action='store_true', help='Build to a folder instead of a onefile exe', default=False)
    parser.add_argument('--zip', '-zip', action='store_true', help='Build to a zip instead of a onefile exe (Zip version of --folder)', default=False)
    parser.add_argument('--bat', '-bat', action='store_true', help='Use a .bat file for starting the built script instead of a exe for faster start times (Automatically implies --folder)', default=False)
    parser.add_argument('--icon', '-icon', help='Icon for the created EXE', default=None)
    parser.add_argument('--uac', '-uac', action='store_true', help='Add UAC to the EXE', default=False)
    parser.add_argument('--package', '-p', action='append', help='Include a package that might have been missed.', default=[])
    parser.add_argument('--plugin', '-pl', action='append', help='Load a plugin by path or name for built-in plugins', default=[])
    parser.add_argument('--bootloader', help='Use a custom bootloader instead of the default ones (--uac and --windowed will not work as it must be built into the custom bootloader)', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output.', default=False)
    parser.add_argument('--windowed', '-w', action='store_true', help='Disable console', default=False)
    parser.add_argument('--keepfiles', '-k', action='store_true', help='Keep the build files', default=False)
    parser.add_argument('--copy', '-copy', action='append', help='File(s) or folder(s) to copy into the build directory.', default=[])
    parser.add_argument('--disable-compile', action='store_true', help='Disable compiling Lib to .pyc files (useful for debugging)', default=False)
    parser.add_argument('--disable-compressing', action='store_true', help='Disable compressing files', default=False)
    parser.add_argument('--disable-password', action='store_true', help='Disable the password on the onefile EXE', default=False)
    parser.add_argument('--disable-dll', action='store_true', help='Disable Copying the DLLs folder (not recommended)', default=False)
    parser.add_argument('--force-refresh', action='store_true', help='Remove the PyCompyle.cache folder and reinstall components', default=False)
    parser.add_argument( '--debug', action='store_true', help='Enables all debugging tools: --verbose --keepfiles --folder and disables --windowed and --zip', default=False)
    args = parser.parse_args()

    if args.debug:
        args.verbose = True
        args.keepfiles = True
        args.folder = True
        args.zip = False
        args.windowed = False
    if args.zip or args.bat:
        args.folder = True       
    setup_logging(args.verbose)

    for plugin in args.plugin:
        try:
            load_plugin(plugin)
        except Exception as e:
            logging.error(f"Failed to load plugin '{plugin}': {e}")
            sys.exit(1)     

    if args.windowed and args.bat:
        logging.error('Windowed mode is not compatible with batchfile mode')
        sys.exit(1)
    if args.uac and args.bat:
        logging.error('UAC is not compatible with batchfile mode')
        sys.exit(1)

    source_file_path = os.path.abspath(args.source_file)
    info(f"Source file: {source_file_path}")
    if not os.path.exists(source_file_path):
        logging.critical(f"{source_file_path} does not exist")
        exit()
    os.chdir(os.path.dirname(source_file_path))

    folder_path = setup_destination_folder(args.source_file)
    copylogic.copy_python_executable(folder_path)

    copy_paths = (args.copy or [])
    for path in copy_paths:
        name = os.path.basename(path)
        dest_path = os.path.join(folder_path, name)
        try:
            if os.path.isdir(path):
                copylogic.copy_folder_with_excludes(path, dest_path, exclude_patterns=exclude_pattens)
                info(f"Copied folder '{path}' to '{dest_path}'")
            elif os.path.isfile(path):
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(path, dest_path)
                info(f"Copied file '{path}' to '{dest_path}'")
            else:
                logging.error(f"The specified path does not exist: {path}")
        except Exception as e:
            logging.error(f"Failed to copy '{path}': {e}")

    cleaned_modules = importcheck.process_imports(source_file_path, args.package, args.keepfiles, args.force_refresh)
    lib_path = os.path.join(folder_path, 'lib')
    os.makedirs(lib_path, exist_ok=True)
    source_dir = os.path.dirname(source_file_path)
    copylogic.copy_dependencies(cleaned_modules, lib_path, folder_path, source_dir)

    destination_file_path = os.path.join(folder_path, "__main__.py")
    shutil.copyfile(source_file_path, destination_file_path)
    info(f"Packaged script copied to {destination_file_path}")

    info(f"Packaging complete: {folder_path}")
    if not args.noconfirm:
        getpass('Press Enter to continue wrapping the EXE')
    makexe.main(folder_path, args.windowed, args.keepfiles, args.icon, uac=args.uac, folder=args.folder, zip=args.zip, bat=args.bat, disable_compiling=args.disable_compile, disable_compressing=args.disable_compressing, disable_password=args.disable_password, bootloader=args.bootloader)

if __name__ == "__main__":
    main()