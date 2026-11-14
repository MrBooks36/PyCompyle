import subprocess
import sys
import os
import ast
import logging

found_imports: set[str] = set()
pending_imports: set[str] = set()
checked_imports: set[str] = set()


def add_required_imports(additional_imports=None):
    required_imports = [
        "importlib",
        "encodings",
    ]
    if additional_imports:
        required_imports.extend(additional_imports)
    pending_imports.update(required_imports)
    found_imports.update(required_imports)


class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""

        if module:
            self.imports.add(module.split(".")[0])
            self.imports.add(module)

            for alias in node.names:
                if alias.name != "*":
                    self.imports.add(f"{module}.{alias.name}")

        self.generic_visit(node)

    def visit_Call(self, node):
        # Detect __import__("module")
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
            and node.args
        ):
            module_name_node = node.args[0]

            if isinstance(module_name_node, ast.Constant):
                if isinstance(module_name_node.value, str):
                    self.imports.add(module_name_node.value)

            # Backwards compatibility with older Python ASTs
            elif hasattr(ast, "Str") and isinstance(module_name_node, ast.Str):  # type: ignore
                self.imports.add(module_name_node.s)  # type: ignore

        # Detect importlib.import_module("module")
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
            and node.args
        ):
            module_name_node = node.args[0]

            if isinstance(module_name_node, ast.Constant):
                if isinstance(module_name_node.value, str):
                    self.imports.add(module_name_node.value)

        self.generic_visit(node)


def analyze_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    analyzer = ImportAnalyzer()
    analyzer.visit(tree)

    for imp in sorted(analyzer.imports):
        logging.debug(f"Found import: {imp}")
        found_imports.add(imp)

        if imp not in checked_imports:
            pending_imports.add(imp)

    return analyzer.imports


def run_import_checker(imports, source_dir, keepfiles=False):
    tmp_script_path = "tmp_import_check.py"
    tmp_output_path = "tmp_import_output.txt"
    imports = list(imports)
    with open(tmp_script_path, 'w') as tmp_file:
        tmp_file.write('\n'.join(f'try:\n    import {imp}\nexcept: pass\n' for imp in imports))
        tmp_file.write('\nimport sys')
        tmp_file.write(f"\nwith open(r'{tmp_output_path}', 'w') as out_file:")
        tmp_file.write('\n    out_file.write(str([m.__name__ for m in sys.modules.values() if m]))')

    original_dir = os.getcwd()
    try:
        os.chdir(source_dir)
        subprocess.run([sys.executable, tmp_script_path], check=True)
    finally:
        os.chdir(original_dir)

    with open(tmp_output_path, "r") as out_file:
        output = out_file.read().strip()

    if not keepfiles:
        os.remove(tmp_script_path)
        os.remove(tmp_output_path)

    try:
        modules = ast.literal_eval(output)
    except Exception as e:
        logging.error(f"Error parsing modules output: {e}")
        logging.error(f"Output received: {output}")
        modules = []

    return modules


def recurse_import_check(file_path, additional_imports=None, keepfiles=False):
    logging.info("Checking imports...")

    add_required_imports(additional_imports)
    analyze_file(file_path)
    found_imports = run_import_checker(pending_imports, os.path.dirname(file_path), keepfiles)

    cleaned_imports = set()

    for imp in found_imports:
        cleaned_imports.add(imp.split(".")[0])

    logging.debug(f"Found imports: {found_imports}")
    logging.debug(f"Cleaned imports: {cleaned_imports}")

    return cleaned_imports
