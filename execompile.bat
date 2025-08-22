@echo off

:: Remove old executables
del EXEs\bootloader.exe
del EXEs\bootloaderw.exe
del EXEs\bootloader_uac.exe
del EXEs\bootloaderw_uac.exe

:: Compile regular bootloader
pyinstaller --onefile -i "NONE" components\bootloader.py
move dist\bootloader.exe EXEs\bootloader.exe

:: Compile windowed bootloader
pyinstaller --onefile --windowed -i "NONE" components\bootloader.py
move dist\bootloader.exe EXEs\bootloaderw.exe

:: Compile UAC bootloader
pyinstaller --onefile -i "NONE" --uac-admin components\bootloader.py
move dist\bootloader.exe EXEs\bootloader_uac.exe

:: Compile windowed UAC bootloader
pyinstaller --onefile --windowed -i "NONE" --uac-admin components\bootloader.py
move dist\bootloader.exe EXEs\bootloaderw_uac.exe

:: Clean up temporary files
del bootloader.spec
rmdir /q /s build
rmdir /q /s dist