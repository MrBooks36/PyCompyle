# utilities for scripts to interact with the core structure of PyCompyle
global pythonexe


def _get_pythonexe():
    import os, sys
    mrb36_folder = os.path.dirname(sys.modules["__main__"].__file__) # type: ignore
    if "mrb36" in mrb36_folder:
     _python_exe = os.path.join(mrb36_folder, "python.exe")
     if os.path.exists(_python_exe):
        return _python_exe
    else: return sys.executable

pythonexe = _get_pythonexe()