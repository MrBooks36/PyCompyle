import os, sys, logging, inspect, textwrap, importlib.machinery
from logging import info

plugins = []

def load_plugin(plugin_path):
    if os.path.isfile(plugin_path):
        plugins.append(plugin_path)
        info(f"Loaded plugin: {plugin_path}")
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
    for plugin_path in plugins:
        try:
            plugin = _load_module(plugin_path)
        except Exception as e:
            logging.warning(f"Failed to load plugin {plugin_path}: {e}")
            continue

        if not hasattr(plugin, "patches"):
            continue

        for target_name, patch_func in plugin.patches.items():
            parts = target_name.split(".")
            if len(parts) < 2:
                logging.warning(f"Invalid patch target '{target_name}' in {plugin_path}")
                continue

            mod_name, attr_name = ".".join(parts[:-1]), parts[-1]

            try:
                target_mod = sys.modules.get(mod_name) or __import__(mod_name, fromlist=[attr_name])
                original = getattr(target_mod, attr_name)

                # Try to call the patch function with original as arg (wrapper)
                try:
                    new_obj = patch_func(original)
                except TypeError:
                    # If patch_func does not accept original, treat as direct replacement
                    new_obj = patch_func

                setattr(target_mod, attr_name, new_obj)
                logging.info(f"Patched {target_name} from {plugin_path}")

            except Exception as e:
                logging.warning(f"Failed to patch {target_name} from {plugin_path}: {e}")


def get_special_cases():
    for plugin_path in plugins:
        code = _load_module(plugin_path)
        if not hasattr(code, "special_case"):
            continue
        source = inspect.getsource(code.special_case)
        body = textwrap.dedent("\n".join(source.splitlines()[1:]))
        sig = inspect.signature(code.special_case)

        import_name = sig.parameters.get("import_name", None)
        top = sig.parameters.get("top", None)
        continue_after = sig.parameters.get("continue_after", None)

        yield (
            import_name.default if import_name else "__main__",
            body,
            top.default if top else False,
            continue_after.default if continue_after else False,
        )

def run_startup_code():
    for plugin_path in plugins:
        code = _load_module(plugin_path)
        if hasattr(code, "init"):
            source = inspect.getsource(code.init)
            yield textwrap.dedent("\n".join(source.splitlines()[1:])) + "\n"

def run_halfway_code():
    for plugin_path in plugins:
        code = _load_module(plugin_path)
        if hasattr(code, "midway"):
            source = inspect.getsource(code.midway)
            yield textwrap.dedent("\n".join(source.splitlines()[1:])) + "\n"

def run_end_code():
    for plugin_path in plugins:
        code = _load_module(plugin_path)
        if hasattr(code, "end"):
            source = inspect.getsource(code.end)
            yield textwrap.dedent("\n".join(source.splitlines()[1:])) + "\n"
