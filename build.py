import os
import subprocess
import shutil
import fnmatch
import stat

def remove_readonly(func, path, excinfo):
    """Callback to remove read-only files during shutil.rmtree."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def delete_matching_paths(root_path, patterns):
    """Delete files and folders matching patterns under root_path."""
    for root, dirs, files in os.walk(root_path):
        # Delete matching directories
        for pattern in patterns:
            for dir_name in fnmatch.filter(dirs, pattern):
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path, onexc=remove_readonly)
                except Exception:
                    pass  # Ignore errors

            # Delete matching files
            for file_name in fnmatch.filter(files, pattern):
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # Ignore errors

def read_gitignore(file_path):
    """Read .gitignore and return a list of patterns."""
    patterns = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns

def delete_pycache(start_dir):
    """Recursively delete __pycache__ directories."""
    for root, dirs, _ in os.walk(start_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path, onexc=remove_readonly)
            except Exception:
                pass

def main():
    print('Beginning build process...')
    
    # Step 1: Compile EXEs
    print('Compiling EXEs folder...')
    subprocess.run(['python', 'execompile.py'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 2: Copy project to build folder
    build_folder = os.path.join('.', 'build')
    if os.path.exists(build_folder):
        shutil.rmtree(build_folder, onexc=remove_readonly)

    shutil.copytree('.', build_folder, ignore_dangling_symlinks=True)

    # Step 3: Remove files/folders according to .gitignore
    gitignore_path = os.path.join('.', '.gitignore')
    if os.path.exists(gitignore_path):
        print('Reading .gitignore...')
        gitignore_patterns = read_gitignore(gitignore_path)
        print('Deleting files/folders as per .gitignore...')
        delete_matching_paths(build_folder, gitignore_patterns)

    # Step 4: Remove .github, .git, .gitignore, build.py and execompile.py in build
    for path in ['.github', '.git', '.gitignore', 'build.py']:
        target = os.path.join(build_folder, path)
        if os.path.exists(target):
            if os.path.isdir(target):
                shutil.rmtree(target, onexc=remove_readonly)
            else:
                os.remove(target)

    # Step 5: Remove __pycache__ recursively
    delete_pycache(build_folder)

    print('Build cleanup completed.')

if __name__ == "__main__":
    main()
