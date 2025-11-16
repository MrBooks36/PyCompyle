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

    lib_folder_basename = 'lib'
    for path in sys.path:
        if not os.path.isdir(path):
            continue

        lib_folder = os.path.join(path, lib_folder_basename)

        if not os.path.isdir(lib_folder):
            continue

        for dirpath, dirnames, filenames in os.walk(lib_folder):
            # Skip __pycache__ directories
            if '__pycache__' in dirnames:
                dirnames.remove('__pycache__')

            for filename in filenames:
                if not filename.endswith('.py'):
                    continue

                file_full_path = os.path.join(dirpath, filename)
                rel_path_in_lib = os.path.relpath(file_full_path, lib_folder)

                # Check if the file exists in any of the current sys.path directories
                found = any(
                    os.path.exists(os.path.join(p, rel_path_in_lib))
                    for p in sys.path
                    if os.path.isdir(p)
                )

                if not found:
                    logging.debug(f"Compiling: {rel_path_in_lib}")

                    # Attempt to compile the file
                    if not compile_file(file_full_path):
                        sys.exit(1)

                    logging.info(f"Successfully compiled {rel_path_in_lib}.")