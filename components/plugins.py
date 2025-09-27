import os, sys, logging, inspect, textwrap
import importlib.machinery
import argparse
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
        if not hasattr(code, "special_case"):
            continue
        source = inspect.getsource(code.special_case)
        body = textwrap.dedent("\n".join(source.splitlines()[1:]))
        sig = inspect.signature(code.special_case)

        import_name_param = sig.parameters.get('import_name')
        top_param = sig.parameters.get('top')
        continue_after_param = sig.parameters.get('continue_after')

        import_name = "__main__" if (
            import_name_param is None or
            import_name_param.default is inspect.Parameter.empty
        ) else import_name_param.default

        top = False if (
            top_param is None or
            top_param.default is inspect.Parameter.empty
        ) else top_param.default

        continue_after = False if (
            continue_after_param is None or
            continue_after_param.default is inspect.Parameter.empty
        ) else continue_after_param.default

        yield (import_name, body, top, continue_after)

def load_modified_args(args):
    base = vars(args).copy()
    for plugin in plugins:
        code = importlib.machinery.SourceFileLoader("plugin", plugin).load_module()
        if hasattr(code, "modify_args"):
            mod = code.modify_args(args)
            for k, v in vars(mod).items():
                # replace only when plugin supplies a non-None value
                if v is not None:
                    base[k] = v
    return argparse.Namespace(**base)
