import os, shutil, stat, logging, subprocess, fnmatch, argparse, platform

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

main_folder = os.path.abspath(os.path.dirname(__file__))

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def delete_pycache(start_dir):
    for root, dirs, _ in os.walk(start_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path, onexc=remove_readonly)
            except Exception:
                pass

def read_gitignore(file_path):
    logging.info(f"Reading .gitignore")
    patterns = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns

def delete_matching_paths(root_path, patterns):
    for root, dirs, files in os.walk(root_path):
        for pattern in patterns:
            for dir_name in fnmatch.filter(dirs, pattern):
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path, onexc=remove_readonly)
                except Exception:
                    pass
            for file_name in fnmatch.filter(files, pattern):
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                except Exception:
                    pass

def build(suffix, no_zip=False):
    logging.info(f"Compiling EXEs...")
    if suffix == "linux" and platform.system().lower() != "linux":
        subprocess.run(["wsl.exe", "--", "bash", "-lc", "python3 execompile.py"],check=True)

    else:
        subprocess.run(['python', os.path.join(main_folder, 'execompile.py')])

    build_folder = os.path.join(main_folder, 'build' + suffix)
    if os.path.exists(build_folder):
        shutil.rmtree(build_folder, onexc=remove_readonly)

    shutil.copytree(main_folder, build_folder)

    logging.info("Cleaning build folder...")
    gitignore_path = os.path.join(main_folder, '.gitignore')
    if os.path.exists(gitignore_path):
        patterns = read_gitignore(gitignore_path)
        delete_matching_paths(build_folder, patterns)
    else:
        logging.warning(".gitignore not found, skipping pattern-based cleanup.")

    logging.info("Removing extra files...")
    items = ['.github', '.git', '.gitignore', 'build.py', 'execompile.py', 'readme.md', 'bootloader', 'installer.py']

    for item in items:
        target = os.path.join(build_folder, item)
        if os.path.exists(target):
            if os.path.isdir(target):
                shutil.rmtree(target, onexc=remove_readonly)
            else:
                os.remove(target)

    logging.info('Build cleanup completed.')
    if not no_zip:
        logging.info("Compressing build folder...")
        shutil.make_archive(build_folder, 'zip', build_folder)
        logging.info('Build process completed successfully.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--include-linux', action='store_true', help='Create builds for Windows and Linux')
    parser.add_argument('--no-zip', action='store_true', help='Do not create zip archives of the builds')
    args = parser.parse_args()

    logging.info("Starting build process...")
    delete_pycache(main_folder)

    build(suffix="win" if args.include_linux else "", no_zip=args.no_zip)

    if args.include_linux:
        logging.info("Starting Linux build process...")
        build(suffix="linux" if args.include_linux else "", no_zip=args.no_zip)
if __name__ == '__main__':
    main()