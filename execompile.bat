@echo off
del EXEs\bootloader.exe
del EXEs\bootloaderw.exe
pyinstaller --onefile components\bootloader.py
move dist\bootloader.exe EXEs\bootloader.exe
pyinstaller --onefile --windowed components\bootloader.py
move dist\bootloader.exe EXEs\bootloaderw.exe
del bootloader.spec
rmdir /q /s build
rmdir /q /s dist