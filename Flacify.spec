import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Собираем данные qfluentwidgets (иконки, стили, ресурсы)
qfw_datas = collect_data_files('qfluentwidgets')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=qfw_datas + [
        ('app/assets/icon.ico', 'app/assets'),
    ],
    hiddenimports=[
        'mutagen', 'mutagen.mp3', 'mutagen.flac', 'mutagen.oggvorbis', 
        'mutagen.wave', 'pygame', 'qfluentwidgets',
        'pyexpat', 'xml.parsers.expat', 'xml.parsers', 'xml', 'PyQt5.sip'
    ] + collect_submodules('mutagen'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'xmlrpc', 'pydoc',
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 
        'PyQt6.QtNetwork', 'PyQt6.QtDBus', 'PyQt6.sip',
        'sip', 'darkdetect._mac_detect'
    ],
    win_no_prefer_redirects=False,
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,       # Для режима onefile
    a.datas,          # Для режима onefile
    exclude_binaries=False,  # FALSE = режим onefile (все в один exe)
    name='Flacify',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(SPECPATH, 'app', 'assets', 'icon.ico')
)
