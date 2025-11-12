# Shutup vars
import os, shutil
folder_path = ''
info = print


def special_case5(import_name='PyQt5', top=False):
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

    remove = ['QtXml', 'QtXmlPatterns', 'QtNetwork', 'QtMultimedia', 'QtMultimediaWidgets',
                  'QtQml', 'QtQuick', 'QtQuickWidgets', 'QtSensors', 'QtWebChannel', 'QtSerialPort',
                  'QtQuick3D', 'QtSql', 'QtRemoteObjects', 'QtWebSockets', 'QtBluetooth', 'QtPositioning',
                  'QtprintSupport', 'QtTextToSpeech', 'QtLocation', 'QtHelp', 'QtNfc'
                  ]
    for item in remove:
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyd'))
        os.remove(os.path.join(folder_path, 'lib', 'PyQt5', f'{item}.pyi'))
        try:
         os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'bin', f'{item}.dll'))
        except: 
            try: os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', 'bin', f'qt5{item}.dll'))
            except: pass
    for item in remove:
        for file in os.listdir(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations")):
            if fnmatch.fnmatch(file, f'qt{item[2:].lower()}*'):
                os.remove(os.path.join(folder_path, 'lib', 'PyQt5', 'Qt5', "translations", file))


def special_case6(import_name='PyQt6', top=False):
    '''Special case handler for PyQt6 stripping. Removes unnecessary PyQt6 components that are not needed for basic PyQt6 applications.'''
    import fnmatch
    info("Stripping PyQt6")
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt6', 'bindings'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt6', 'uic'), ignore_errors=True)
    shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', 'qml'), ignore_errors=True)
    for folder in os.listdir(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', 'plugins')):
        if folder == 'platforms':
            continue
        else: shutil.rmtree(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', 'plugins', folder))

    remove = ['QtXml', 'QtNetwork', 'QtMultimedia', 'QtMultimediaWidgets',
                  'QtQml', 'QtQuick', 'QtQuickWidgets', 'QtSensors', 'QtWebChannel', 'QtSerialPort',
                  'QtQuick3D', 'QtSql', 'QtRemoteObjects', 'QtWebSockets', 'QtBluetooth', 'QtPositioning',
                  'QtprintSupport', 'QtTextToSpeech', 'QtHelp', 'QtNfc', 'QtSpatialAudio',
                  'QtStateMachine', 'QtPdf', 'QtSvgWidgets', 'QtSvg', 'QtDesigner', 'QtPdfWidgets'
                  ]
    for item in remove:
        os.remove(os.path.join(folder_path, 'lib', 'PyQt6', f'{item}.pyd'))
        os.remove(os.path.join(folder_path, 'lib', 'PyQt6', f'{item}.pyi'))
        try:
         os.remove(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', 'bin', f'Qt6{item.replace('Qt', '')}.dll'))
        except: pass
    for item in remove:
        for file in os.listdir(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', "translations")):
            if fnmatch.fnmatch(file, f'{item[2:].lower()}*'):
                os.remove(os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', "translations", file))            

    dlls = [
    'Qt6Labs*.dll',
    'Qt6PositioningQuick.dll',
    'Qt6LocationQuick.dll',
    'Qt6QuickTemplates2.dll',
    'Qt6QuickTimelineBlendTrees.dll',
    'Qt6Quick3DRuntimeRender.dll',
    'Qt6ShaderTools.dll',
    'Qt6Quick*.dll',
    'Qt6*quick.dll',
    'Qt6*qml*.dll',
    ]

    for pattern in dlls:
     bin_path = os.path.join(folder_path, 'lib', 'PyQt6', 'Qt6', 'bin')
     for file in os.listdir(bin_path):
        if fnmatch.fnmatch(file, pattern):
            os.remove(os.path.join(bin_path, file))