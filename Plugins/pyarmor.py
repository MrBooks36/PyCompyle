# Shutup vars
import os, subprocess, sys, logging, shutil, py_compile, tempfile
args = ''
folder_path = ''
plugin = ''

def write_pth(folder_path):
	with open(os.path.join(folder_path, 'python._pth'), 'w') as file:
			file.write('DLLs\ndist/lib\n.')

def compile_main(*args):
	pass


def compile_and_replace_py_to_pyc(folder, _=""):
	directory = os.path.join(folder, "dist", "lib")
	for root, _, files in os.walk(directory):
		for file in files:
			if file.endswith('.py'):
				py_file_path = os.path.join(root, file)

				temp_dir = r'C:\Windows\Temp' if os.name == 'nt' else '/tmp'

				temp_dir = tempfile.mkdtemp(dir=temp_dir)
				try:
					temp_file_path = os.path.join(temp_dir, file)

					shutil.copy2(py_file_path, temp_file_path)
					pyc_file_path = py_file_path + 'c' 

					try:     
						display_file_path = os.path.relpath(py_file_path, directory)
						py_compile.compile(temp_file_path, cfile=pyc_file_path, dfile=display_file_path, doraise=True)
						os.remove(py_file_path)

					except py_compile.PyCompileError as compile_error:
						logging.error(f"Failed to compile {py_file_path}: {compile_error}")
					except Exception as e:
						logging.error(f"An error occurred with {py_file_path}: {e}")

				finally:
					shutil.rmtree(temp_dir)

def init():
	pyarmor = subprocess.run(["pyarmor", "--version"], stdout=subprocess.DEVNULL) # idk why its like this but python -m pyarmor dosn't work
	if pyarmor.returncode != 0:
		logging.critical("Pyarmor not installed, exiting...")
		sys.exit(1)
	args.disable_lib_compressing = True

def get_py_files(folder_path):
	py_files = []
	for root, dirs, files in os.walk(folder_path):
		if "dist" in dirs:
			dirs.remove("dist")
			
		for file in files:
			if file.endswith(".py"):
				full_path = os.path.join(root, file)
				rel_root = os.path.relpath(root, folder_path)
				py_files.append((full_path, rel_root))
	return py_files


def mod_main(folder_path):
	with open(os.path.join(folder_path, "__main__.py"), "r") as f:
		code = f.read()

	new_code = "__name__ = '__main__'\n" + code

	with open(os.path.join(folder_path, "__main__.py"), "w") as f:
		f.write(new_code)



def midway(folder_path):
	logging.debug("Modding __main__.py")
	plugin.mod_main(folder_path)
	from tqdm import tqdm
	logging.info("Running Pyarmor...")
	
	tasks = plugin.get_py_files(folder_path)
	error_buffer = []
	
	for file_path, rel_root in tqdm(tasks, desc="INFO: Obfuscating", unit="file"):
		output_dir = os.path.join(folder_path, "dist", rel_root)
		os.makedirs(output_dir, exist_ok=True)
		
		# Run pyarmor
		result = subprocess.run(
			["pyarmor", "gen", "--output", output_dir, file_path], 
			stdout=subprocess.DEVNULL, 
			stderr=subprocess.DEVNULL
		)
		
		if result.returncode != 0:
			error_buffer.append(file_path)
			shutil.move(file_path, output_dir)

	for file in error_buffer:
		logging.warning(f"Pyarmor failed on {file}")

	lib_path = os.path.join(folder_path, "lib")
	if os.path.exists(lib_path):
		shutil.rmtree(lib_path)

	os.remove(os.path.join(folder_path, "__main__.py"))
	shutil.move(os.path.join(folder_path, "dist", "__main__.py"), os.path.join(folder_path, "__init__.py"))
	shutil.move(os.path.join(folder_path, "dist", "pyarmor_runtime_000000"), folder_path)
	with open(os.path.join(folder_path, "__main__.py"), "w") as f:
		f.write("import __init__")
	

patches = {
	"components.makexe.write_pth": write_pth,
	"components.makexe.compile_main": compile_main,
	"components.makexe.compile_and_replace_py_to_pyc": compile_and_replace_py_to_pyc,
}
