import os, shutil, logging
folder_path = ''
info = print  # Placeholder for the actual logging function


def special_case(import_name='PyQt5', top=False):
    import fnmatch
    '''Special case handler for PyQt5 stripping. Removes unnecessary PyQt5 components that are not needed for basic PyQt5 applications.'''
    info(f"Applying PyQt5 stripping plugin for module: {import_name}")
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'bindings'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'uic'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'qml'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'plugins'), ignore_errors=True)
    not_needed = ['QtXml', 'QtXmlPatterns', 'QtNetwork', 'QtMultimedia', 'QtMultimediaWidgets',
                  'QtQml', 'QtQuick', 'QtQuickWidgets', 'QtSensors', 'QtWebChannel', 'QtSerialPort',
                  'QtQuick3D', 'QtSql', 'QtRemoteObjects', 'QtWebSockets', 'QtBluetooth', 'QtPositioning',
                  'QtprintSupport', 'QtTextToSpeech', 'QtLocation'
                  ]
    for item in not_needed:
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyd'))
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyi'))

    for item in not_needed:
        for file in os.listdir(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations")):
            if fnmatch.fnmatch(file, f'qt{item[2:].lower()}*'):
                os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations", file))