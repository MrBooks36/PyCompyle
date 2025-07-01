import ast
import os
import logging

def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

def get_imports_from_file(file_path, module_root):
    imports = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (OSError, IOError, SyntaxError) as e:
        logging.error(f"Failed to parse {file_path}: {e}")
        return imports

    rel_module_path = os.path.relpath(file_path, module_root).replace(os.sep, ".").rstrip(".py")
    rel_module_parts = rel_module_path.split(".")[:-1]  # remove filename

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Handle relative import
                rel_parts = rel_module_parts[:len(rel_module_parts) - node.level + 1]
                if node.module:
                    rel_parts += node.module.split(".")
                full_module = ".".join(rel_parts)
                if full_module:
                    imports.add(full_module)
            elif node.module:
                imports.add(node.module)

    return imports

def resolve_local_path(module_name, base_dir):
    parts = module_name.split('.')
    py_file = os.path.join(base_dir, *parts) + ".py"
    py_folder = os.path.join(base_dir, *parts)

    if os.path.isfile(py_file):
        return [py_file]

    results = []
    if os.path.isdir(py_folder):
        for root, _, files in os.walk(py_folder):
            for file in files:
                if file.endswith(".py"):
                    results.append(os.path.join(root, file))
    return results

def recursive_imports(entry_file, visited=None, base_dir=None):
    if visited is None:
        visited = set()
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(entry_file))

    to_process = [entry_file]
    top_level = set()

    while to_process:
        current_file = to_process.pop()
        if current_file in visited:
            continue
        visited.add(current_file)

        imports = get_imports_from_file(current_file, base_dir)
        for imp in imports:
            top = imp.split('.')[0]
            top_level.add(top)

            for path in resolve_local_path(imp, base_dir):
                if path not in visited:
                    to_process.append(path)

    return top_level

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test.py"
    print(sorted(recursive_imports(path)))
