import os, sys, platform, subprocess, shutil, logging, argparse
from getpass import getpass
from logging import info
try:
    from components.imports import importcheck
    from components.copylogic import exclude_pattens
    from components import makexe, copylogic
    from components.plugins import load_plugin, apply_monkey_patches, run_startup_code, run_halfway_code
except:
    from PyCompyle.components.imports import importcheck # type: ignore
    from PyCompyle.components import makexe, copylogic  # type: ignore
    from PyCompyle.components.imports import importcheck # type: ignore
    from PyCompyle.components.copylogic import exclude_pattens # type: ignore
    from PyCompyle.components.plugins import load_plugin,  run_startup_code, run_halfway_code # type: ignore


exclude_pattens = ['__pycache__', '.git', '.github', '.gitignore', 'readme*', 'license*', '.vscode']

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
        try:
            # Split release number into major and minor parts
            major_minor = release.split('.')
            major_version = int(major_minor[0])

            # Check if the major version is 10 or higher
            if major_version >= 10:
                return True

        except (ValueError, IndexError):
            # Handle unexpected format in release version
            return False

    return False

def validate_platform():
    if not check_system():
        logging.critical("PyCompyle is designed to run only on Windows 10 or higher 64-bit.")
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
    parser.add_argument('--zip', '-zip', action='store_true', help='Build to a zip instead of a onefile exe. (Zipped version of --folder)', default=False)
    parser.add_argument('--bat', '-bat', action='store_true', help='Use a .bat file for starting the built script instead of a exe for faster start times (Automatically implies --folder)', default=False)
    parser.add_argument('--icon', '-icon', help='Icon for the created EXE', default=None)
    parser.add_argument('--uac', '-uac', action='store_true', help='Add UAC to the EXE', default=False)
    parser.add_argument('--package', '-p', action='append', help='Include a package that might have been missed.', default=[])
    parser.add_argument('--plugin', '-pl', action='append', help='Load a plugin by path or name for built-in plugins', default=[])
    parser.add_argument('--midwaycommand', '-m', help='Run a CMD command or batch script before building the EXE', default=None)
    parser.add_argument('--bootloader', help='Use a custom bootloader instead of the default ones (--uac and --windowed will not work as it must be built into the custom bootloader)', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output.', default=False)
    parser.add_argument('--windowed', '-w', action='store_true', help='Disable console', default=False)
    parser.add_argument('--keepfiles', '-k', action='store_true', help='Keep the build files', default=False)
    parser.add_argument('--copy', '-copy', action='append', help='File(s) or folder(s) to copy into the build directory.', default=[])
    parser.add_argument('--pyarg', '-pyarg', action='append', help='Add arguments to the startup of the python interpreter', default=[])
    parser.add_argument('--include-script', action='append', help='Add a file located in PYTHONPATH/Scripts', default=[])
    parser.add_argument('--copy-include', action='store_true', help='Copy PYTHONPATH/include', default=False)
    parser.add_argument('--upx-threads', help='How many threads to use when compressing with UPX. (More=faster but more straining. Less=slower but less straining)', default=False)
    parser.add_argument('--disable-compile', action='store_true', help='Disable compiling Lib to .pyc files (useful for debugging)', default=False)
    parser.add_argument('--disable-compressing', action='store_true', help='Disable compressing files', default=False)
    parser.add_argument('--disable-password', action='store_true', help='Disable the password on the onefile EXE', default=False)
    parser.add_argument('--disable-dll', action='store_true', help='Disable Copying the DLLs folder (not recommended)', default=False)
    parser.add_argument('--force-refresh', action='store_true', help='Remove the PyCompyle.cache folder and reinstall components', default=False)
    parser.add_argument('--debug', action='store_true', help='Enables all debugging tools: --verbose --keepfiles --folder and disables --windowed and --zip', default=False)
    args = parser.parse_args()
    if args.debug:
        args.verbose = True

    setup_logging(args.verbose)

    for plugin in args.plugin:
        try:
            load_plugin(plugin)
        except Exception as e:
            logging.error(f"Failed to load plugin '{plugin}': {e}")
            sys.exit(1)
    apply_monkey_patches()
    folder_path = setup_destination_folder(args.source_file)

    exec('\n'.join(run_startup_code()), globals(), locals())

    if args.debug:
        args.verbose = True
        args.keepfiles = True
        args.folder = True
        args.zip = False
        args.windowed = False
    if args.zip or args.bat:
        args.folder = True

    if args.windowed and args.bat:
        logging.error('Windowed mode is not compatible with batchfile mode')
        sys.exit(1)
    if args.uac and args.bat:
        logging.error('UAC is not compatible with batchfile mode')
        sys.exit(1)

    if args.windowed and args.bootloader:
        logging.error('Windowed mode is not compatible with a custom bootloader')
        sys.exit(1)
    if args.uac and args.bootloader:
        logging.error('UAC is not compatible with a custom bootloader')
        sys.exit(1)
    if args.bat and args.bootloader:
        logging.error('Batchfile mode is not compatible with a custom bootloader')
        sys.exit(1)

    source_file_path = os.path.abspath(args.source_file)
    info(f"Source file: {source_file_path}")
    if not os.path.exists(source_file_path):
        logging.critical(f"{source_file_path} does not exist")
        sys.exit(1)
    os.chdir(os.path.dirname(source_file_path))

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

    if args.include_script:
        copylogic.copy_scripts(args.include_script, folder_path)
    if args.copy_include:
        copylogic.copy_include(folder_path)

    destination_file_path = os.path.join(folder_path, "__main__.py")
    shutil.copy(source_file_path, destination_file_path)
    info(f"{os.path.basename(source_file_path)} copied")

    info("Gathering requirements complete")
    exec('\n'.join(run_halfway_code()), globals(), locals())

    if args.midwaycommand:
        info(f"Running midway command: {args.midwaycommand}")
        subprocess.run(args.midwaycommand, shell=True)

    if not args.noconfirm:
        getpass('Press Enter to continue building the EXE')
    makexe.main(folder_path, args)

if __name__ == "__main__":
    main()
