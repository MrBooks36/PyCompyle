# Shutup vars
import os, shutil
folder_path = ''
info = print


def special_case(import_name='PyQt5', top=False):
    '''Special case handler for PyQt5 stripping. Removes unnecessary PyQt5 components that are not needed for basic PyQt5 applications.'''
    import fnmatch
    info("Stripping PyQt5")
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'bindings'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'uic'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'qml'), ignore_errors=True)
    for folder in os.listdir(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'plugins')):
        if folder == 'platforms':
            continue
        else: shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'plugins', folder))
    
    not_needed = ['QtXml', 'QtXmlPatterns', 'QtNetwork', 'QtMultimedia', 'QtMultimediaWidgets',
                  'QtQml', 'QtQuick', 'QtQuickWidgets', 'QtSensors', 'QtWebChannel', 'QtSerialPort',
                  'QtQuick3D', 'QtSql', 'QtRemoteObjects', 'QtWebSockets', 'QtBluetooth', 'QtPositioning',
                  'QtprintSupport', 'QtTextToSpeech', 'QtLocation', 'QtHelp', 'QtNfc'
                  ]
    for item in not_needed:
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyd'))
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyi'))
        try:
         os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'bin', f'{item}.dll'))
        except: pass
    for item in not_needed:
        for file in os.listdir(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations")):
            if fnmatch.fnmatch(file, f'qt{item[2:].lower()}*'):
                os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations", file))