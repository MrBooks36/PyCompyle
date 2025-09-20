# PyCompyle <span style="font-size: 55%;">by MrBooks36</span>

Package a Python script into an executable (EXE) with its dependencies without being flagged by Windows Defender.

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

Python version 3.6 or higher

To access the latest releases of this project, please visit our [Releases page](https://github.com/MrBooks36/PyCompyle/releases).  
Simply download the `installer.py` script and execute it to install PyCompyle directly into the site-packages directory.

## Usage

`python -m PyCompyle source_file` 


### Arguments

- `-nc`, `--noconfirm`: Skip confirmation for wrapping the EXE .
- `-f` `--folder`: Build to a folder instead of a onefile exe 
- `-zip` `--zip`: Build to a zip instead of a onefile exe (Zip version of --folder) 
- `-bat`, `--bat`: Use a .bat file for starting the built script instead of a exe for faster start times (Automatically implies --folder) 
- `-i`, `--icon`: Specify an icon for the created EXE.
- `-p`, `--package`: Include a package that might have been missed. Can be used multiple times to add multiple packages. 
- `-v`, `--verbose`: Enable verbose output .
- `-w`, `--windowed`: Create a windowed application; the console won't be displayed .
- `-k`, `--keepfiles`: Keep the build files after packaging .
- `-d`, `--debug`: Enable all debugging tools; turns `--verbose` and `--keepfiles` on, `--windowed` and `--zip` off. 
- `-c`, `--copy`: File(s) or folder(s) to copy into the build directory. Can be used multiple times. *(CAPS matter)* 
- `-uac`, `--uac`: Add UAC prompt to the EXE .
- `--force-refresh`: Remove the PyCompyle.cache folder and reinstall components.
- `--disable-compressing`: Disable compressing files
- `--disable-password`: Disable the password on the onefile EXE


## Example Command
This command packages `my_script.py` into an EXE with a custom icon, enables verbose output, creates a windowed application, includes an additional package, and forces a refresh of `linked_imports.json`.  
`python -m PyCompyle --force-refresh --icon="myicon.ico" --verbose --windowed --package=numpy --package=ollama my_script.py`

## Contributing

Feel free to submit [issues](github.com/MrBooks36/PyCompyle/issues) or pull requests if you find any bugs or have feature requests.  
If you find a import that is not detected create a [issue](github.com/MrBooks36/PyCompyle/issues) with the label `linked imports enhancement`

## License

See the LICENSE.md for details.
