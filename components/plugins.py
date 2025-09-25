import os, sys, logging, inspect, textwrap
import importlib.machinery
from logging import info

plugins = []

def load_plugin(plugin_path):
    info(f"Loading plugin: {plugin_path}")
    if os.path.isfile(plugin_path):
        if os.path.exists(plugin_path):
            plugins.append(plugin_path)
        else:
            logging.warning(f"Plugin path {plugin_path} does not exist. Skipping.")
        return
    base = os.path.dirname(sys.modules["__main__"].__file__)
    builtin_plugin_path = os.path.join(base, "Plugins", f"{plugin_path}.py")
    if os.path.exists(builtin_plugin_path):
        plugins.append(builtin_plugin_path)
    else:
        logging.warning(f"Plugin path {plugin_path} does not exist. Skipping.")


def get_special_cases():
    for plugin in plugins:
        code = importlib.machinery.SourceFileLoader("plugin", plugin).load_module()
        source = inspect.getsource(code.special_case)
        body = textwrap.dedent("\n".join(source.splitlines()[1:]))
        sig = inspect.signature(code.special_case)

        import_name = sig.parameters.get('import_name', None)
        top = sig.parameters.get('top', None)
        continue_after = sig.parameters.get('continue_after', None)

        if import_name is None or import_name.default is inspect.Parameter.empty:
            import_name = "__main__"
        else:
            import_name = import_name.default

        if top is None or top.default is inspect.Parameter.empty:
            top = False
        else:
            top = top.default

        if continue_after is None or continue_after.default is inspect.Parameter.empty:
            continue_after = False
        else:
            continue_after = continue_after.default

        yield (import_name, body, top, continue_after)

