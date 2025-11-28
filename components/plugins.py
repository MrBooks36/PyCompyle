import os, sys, logging, inspect, textwrap, importlib.machinery, importlib.util
from logging import info

plugins = []

def load_plugin(plugin_path):
    if os.path.isfile(plugin_path):
        plugins.append(plugin_path)
        info(f"Loaded plugin: {os.path.basename(plugin_path)}")
        return
    base = os.path.dirname(sys.modules["__main__"].__file__)
    builtin_plugin_path = os.path.join(base, "Plugins", f"{plugin_path}.py")
    if os.path.exists(builtin_plugin_path):
        plugins.append(builtin_plugin_path)
        info(f"Loaded plugin: {plugin_path}")
    else:
        logging.warning(f"Plugin path {plugin_path} does not exist. Skipping.")
        return

def _load_module(path):
    return importlib.machinery.SourceFileLoader(os.path.basename(path), path).load_module()

def apply_monkey_patches():
    replacements = []
    wrappers = []

    for plugin_path in plugins:
        try:
            plugin = _load_module(plugin_path)
        except Exception as e:
            logging.warning(f"Failed to load plugin {plugin_path}: {e}")
            continue

        if not hasattr(plugin, "patches"):
            continue

        for target_name, patch_info in plugin.patches.items():
            # Expecting: { "func": <callable>, "wrap": bool }
            if not isinstance(patch_info, dict):
                logging.warning(f"Patch for '{target_name}' in {plugin_path} must be a dict")
                continue

            patch_func = patch_info.get("func")
            wrap_flag = patch_info.get("wrap")

            if patch_func is None or wrap_flag is None:
                logging.warning(
                    f"Patch '{target_name}' in {plugin_path} missing 'func' or 'wrap'"
                )
                continue

            parts = target_name.split(".")
            if len(parts) < 2:
                logging.warning(f"Invalid patch target '{target_name}' in {plugin_path}")
                continue

            mod_name, attr_name = ".".join(parts[:-1]), parts[-1]
            target_mod = sys.modules.get(mod_name) or __import__(mod_name, fromlist=[attr_name])

            if wrap_flag:
                wrappers.append((target_mod, attr_name, patch_func, plugin_path))
            else:
                replacements.append((target_mod, attr_name, patch_func, plugin_path))

    # Phase 2: replacements
    for target_mod, attr_name, patch_func, plugin_path in replacements:
        try:
            setattr(target_mod, attr_name, patch_func)
            logging.info(f"Replaced {target_mod.__name__}.{attr_name} from {plugin_path}")
        except Exception as e:
            logging.warning(
                f"Failed to replace {target_mod.__name__}.{attr_name} from {plugin_path}: {e}"
            )

    # Phase 3: wrappers
    for target_mod, attr_name, patch_func, plugin_path in wrappers:
        try:
            original = getattr(target_mod, attr_name)
            wrapped = patch_func(original)
            setattr(target_mod, attr_name, wrapped)
            logging.info(f"Wrapped {target_mod.__name__}.{attr_name} from {plugin_path}")
        except Exception as e:
            logging.warning(
                f"Failed to wrap {target_mod.__name__}.{attr_name} from {plugin_path}: {e}"
            )


def get_special_cases():
    for plugin_path in plugins:
        code = _load_module(plugin_path)

        for attr_name in dir(code):
            if attr_name.startswith("special_case"):
                attr = getattr(code, attr_name)

                if not callable(attr):
                    continue

                source = inspect.getsource(attr)
                body = textwrap.dedent("\n".join(source.splitlines()[1:]))
                sig = inspect.signature(attr)

                import_name = sig.parameters.get("import_name", None)
                top = sig.parameters.get("top", None)
                continue_after = sig.parameters.get("continue_after", None)

                yield (
                    import_name.default if import_name else "__main__",
                    body,
                    top.default if top else False,
                    continue_after.default if continue_after else False)


def _create_code(plugin_path, func_name):
    spec = importlib.util.spec_from_file_location("plugin_mod", plugin_path)
    if spec is None:
        return None

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, func_name):
        return None

    source = inspect.getsource(getattr(mod, func_name))
    body = textwrap.dedent("\n".join(source.splitlines()[1:])) + "\n"


    header = (
        'import importlib.machinery, os\n'
        f"plugin = importlib.machinery.SourceFileLoader(r'{plugin_path}', r'{plugin_path}').load_module()\n"
    )

    return header + body

def run_startup_code():
    for plugin_path in plugins:
        code = _create_code(plugin_path, "init")
        if code:
            yield code

def run_halfway_code():
    for plugin_path in plugins:
        code = _create_code(plugin_path, "midway")
        if code:
            yield code

def run_end_code():
    for plugin_path in plugins:
        code = _create_code(plugin_path, "end")
        if code:
            yield code
