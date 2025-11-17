import os
import sys
import shutil
import logging

folder_path = ''

def midway():
    def compile_file(file_path, keep=False):
     try:
        from Cython.Build import cythonize
        try:
         from setuptools import Extension
         from setuptools.command.build_ext import build_ext
         from setuptools.dist import Distribution
        except ImportError:
            logging.error("Setuptools is not installed")
            return False
     except ImportError:
        logging.error("Cython is not installed.")
        return False

     if not os.path.isfile(file_path):
        logging.error(f"Invalid Python file: {file_path}")
        return False

     module_name = os.path.splitext(os.path.basename(file_path))[0]
     file_dir = os.path.dirname(os.path.abspath(file_path))
     build_dir = r"C:\Windows\Temp\cybuild"
     os.makedirs(build_dir, exist_ok=True)
     # create expected MSVC subdirs
     os.makedirs(os.path.join(build_dir, "Release"), exist_ok=True)
     os.makedirs(os.path.join(build_dir, "Debug"), exist_ok=True)

     temp_pyx = os.path.join(build_dir, f"{module_name}.pyx")
     shutil.copy2(file_path, temp_pyx)

     rel_pyx = f"{module_name}.pyx"

     try:
        extensions = [Extension(module_name, [rel_pyx])]

        # chdir to build_dir so Cython sees relative path
        old_cwd = os.getcwd()
        os.chdir(build_dir)

        cythonize(
            extensions,
            build_dir=build_dir,
            compiler_directives={'language_level': 3},
            annotate=False,
            quiet=False
        )

        dist = Distribution({'name': module_name, 'ext_modules': extensions})
        cmd = build_ext(dist)
        cmd.build_lib = build_dir
        cmd.build_temp = build_dir
        cmd.ensure_finalized()
        cmd.run()

        os.chdir(old_cwd)  # restore cwd

        c_file = os.path.join(build_dir, f"{module_name}.c")
        if not os.path.exists(c_file):
            logging.error(f"Cython did not emit expected .c file: {c_file}")
            return False

        compiled_file = None
        for root, _, files in os.walk(build_dir):
            for f in files:
                if f.startswith(module_name) and (f.endswith(".pyd") or f.endswith(".so")):
                    compiled_file = os.path.join(root, f)
                    break
            if compiled_file:
                break

        if not compiled_file:
            logging.error(f"Compiled file for {file_path} not found.")
            return False

        target_path = os.path.join(file_dir, os.path.basename(compiled_file))
        if os.path.exists(target_path):
            os.remove(target_path)
        shutil.move(compiled_file, target_path)

        if not keep:
            try:
                os.remove(file_path)
            except OSError:
                pass

        shutil.rmtree(build_dir, ignore_errors=True)
        return True

     except Exception as e:
        logging.error(f"Failed to compile {file_path} with Cython: {e}")
        return False

    lib_folder = os.path.join(folder_path, 'lib')
    python_lib_path = os.path.dirname(os.__file__)
    site_packages_path = os.path.join(python_lib_path, 'site-packages')
    # Win32 compatibility
    win32_lib_path = os.path.join(site_packages_path, 'win32', 'lib')

    for dirpath, dirnames, filenames in os.walk(lib_folder):
        if '__pycache__' in dirnames:
            dirnames.remove('__pycache__')

        for filename in filenames:
            if not filename.endswith('.py'):
                if not filename.endswith('.pyx'):
                 continue

            file_full_path = os.path.join(dirpath, filename)
            rel_path_in_lib = os.path.relpath(file_full_path, lib_folder)

            python_lib_file = os.path.join(python_lib_path, rel_path_in_lib)
            site_packages_file = os.path.join(site_packages_path, rel_path_in_lib)
            win32_lib_file = os.path.join(win32_lib_path, rel_path_in_lib)

            if not (
                os.path.exists(python_lib_file)
                or os.path.exists(site_packages_file)
                or os.path.exists(win32_lib_file)
            ):
                logging.debug(f"Compiling: {rel_path_in_lib}")
                if not compile_file(file_full_path):
                    sys.exit(1)
                logging.info(f"Successfully compiled {rel_path_in_lib} with Cython.")