# PyPackager <span style="font-size: 55%;">by MrBooks36</span>

Package a Python script into an executable (EXE) with its dependencies without being flagged by Windows Defender. It provides several options to customize the packaging process.

## Features

- Package a Python script into an EXE.
- Option to skip confirmation dialogs.
- Ability to specify an icon for the EXE.
- Include additional packages that might have been missed during automatic dependency resolution.
- Enable verbose output for more insights during the packaging process.
- Create a windowed application (without a console) if desired.
- Option to keep the build files after the packaging process.
- Support for debugging with additional tools.
- Copy specific files or folders into the build directory.
- Option to force refresh essential files from GitHub.
- Add UAC (User Account Control) prompt to the EXE.

## Installation
To access the latest releases of this project, please visit our [Releases page](https://github.com/MrBooks36/PyPackager/releases).  
Simply download the `installer.py` script and execute it to install PyPackager directly into the site-packages directory.

## Usage

`python -m PyPackager source_file` 


### Arguments

- `-nc`, `--noconfirm`: Skip confirmation for wrapping the EXE (Default: `False`).
- `-i`, `--icon`: Specify an icon for the created EXE (Default: `None`).
- `-p`, `--package`: Include a package that might have been missed. Can be used multiple times to add multiple packages.
- `-v`, `--verbose`: Enable verbose output (Default: `False`).
- `-w`, `--windowed`: Create a windowed application; the console won't be displayed (Default: `False`).
- `-k`, `--keepfiles`: Keep the build files after packaging (Default: `False`).
- `-d`, `--debug`: Enable all debugging tools; turns `--verbose` and `--keepfiles` on, `--windowed` off (Default: `False`).
- `-c`, `--copy`: File(s) or folder(s) to copy into the build directory. Can be used multiple times. *(CAPS matter)*
- `--force-refresh`: Force refresh of `linked_imports.json` from GitHub (Default: `False`).
- `-uac`, `--uac`: Add UAC prompt to the EXE (Default: `False`).

## Example Command
This command packages `my_script.py` into an EXE with a custom icon, enables verbose output, creates a windowed application, includes an additional package, and forces a refresh of `linked_imports.json`.  
`python -m PyPackager --force-refresh --icon="myicon.ico" --verbose --windowed --package=numpy --package=ollama my_script.py`

## Contributing

Feel free to submit [issues](github.com/MrBooks36/PyPackager/issues) or pull requests if you find any bugs or have feature requests.  
If you find a import that is not detected create a [issue](github.com/MrBooks36/PyPackager/issues) with the tag `Oh shit I forgot what I called it I'll change this before I commit it`

## License

This project is licensed under the 3-Clause BSD License - see the LICENSE.md for details.