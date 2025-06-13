# getimports.py

import ast
import os

def get_imports_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

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
            # Check for local module (e.g., `my_module.py` in the same folder)
            imp_path = os.path.join(base_dir, imp + ".py")
            if os.path.exists(imp_path):
                to_process.append(imp_path)

    return all_imports
