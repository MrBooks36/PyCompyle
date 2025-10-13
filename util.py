import os, sys
global pythonexe


__all__ = ["extract_embedded_zip", "pythonexe"]

def _get_python_exe():
    """
    This funtion will return the location of the real python exe as the bootloader exe will change sys.executable and sys.argv[0] to the onefile exe or folder bootloader


    Returns a list with this format:
    0: cpu cores.
    1: RAM
    2:
    """
    build_exe = os.path.join(os.path.dirname(sys.modules["__main__"].__file__), "python.exe")
    if os.path.exists(build_exe):
        return build_exe
    else:
        return sys.executable

def extract_embedded_zip(extract_to):
    """
    Extracts the embedded ZIP archive from the current executable
    and saves it as a standalone file without unzipping.
    Args:
        extract_to (str): File or directory path for the output ZIP.
    """
    exe_path = sys.argv[0]
    bufsize = 1024 * 1024
    offset = 0
    start = -1

    # Locate ZIP header in the executable
    with open(exe_path, 'rb') as f:
        while True:
            chunk = f.read(bufsize)
            if not chunk:
                break
            i = chunk.find(b'PK\x03\x04')
            if i != -1:
                start = offset + i
                break
            offset += len(chunk)

    if start == -1:
        raise RuntimeError("No embedded ZIP found.")

    # Determine output path correctly
    if extract_to.lower().endswith(".zip"):
        zip_path = extract_to
        os.makedirs(os.path.dirname(zip_path) or ".", exist_ok=True)
    else:
        os.makedirs(extract_to, exist_ok=True)
        zip_path = os.path.join(extract_to, "embedded.zip")

    # Write ZIP portion to file
    with open(exe_path, 'rb') as f:
        f.seek(start)
        with open(zip_path, 'wb') as out_zip:
            while True:
                chunk = f.read(bufsize)
                if not chunk:
                    break
                out_zip.write(chunk)

    return zip_path

# Setup
pythonexe = _get_python_exe()