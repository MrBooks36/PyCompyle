import ast
import os

def get_imports_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (OSError, IOError) as e:
        print(f"Could not read file {file_path}: {e}")
        return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def recursive_imports(entry_script, visited=None, base_dir=None):
    if visited is None:
        visited = set()
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(entry_script))

    to_process = [entry_script]
    all_imports = set()

    while to_process:
        current_file = to_process.pop()
        if current_file in visited:
            continue
        visited.add(current_file)

        imports = get_imports_from_file(current_file)
        all_imports.update(imports)

        for imp in imports:
            imp_path = os.path.join(base_dir, imp.replace('.', '/') + ".py")
            if os.path.exists(imp_path):
                to_process.append(imp_path)
            else:
                possible_paths = [
                    os.path.join(base_dir, imp + ".py"),
                    os.path.join(base_dir, imp, "__init__.py")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        to_process.append(path)

            # Add functionality to check for imports in standard Python libraries
            std_lib_path = os.path.join(os.path.dirname(os.__file__), imp + ".py")
            if os.path.exists(std_lib_path):
                all_imports.update(recursive_imports(std_lib_path, visited, os.path.dirname(std_lib_path)))

    return all_imports

if __name__ == "__main__":
    import sys
    script_path = sys.argv[1] if len(sys.argv) > 1 else "test.py"
    imports = recursive_imports(script_path)
    print(f"All imports for {script_path}: {sorted(imports)}")