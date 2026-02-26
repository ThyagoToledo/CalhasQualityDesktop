# -*- mode: python ; coding: utf-8 -*-
"""
CalhaGest - PyInstaller Build Configuration
Inclui todas as dependências necessárias para evitar erros como 'No module named unittest'.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Coletar todos os submódulos necessários
fpdf_submodules = collect_submodules('fpdf')
unittest_submodules = collect_submodules('unittest')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon', 'icon'),
        ('components', 'components'),
        ('views', 'views'),
        ('services', 'services'),
        ('database', 'database'),
        ('analytics', 'analytics'),
    ],
    hiddenimports=[
        # CustomTkinter
        'customtkinter',
        'darkdetect',
        'packaging',
        
        # PIL / Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        
        # fpdf2 e todas as suas dependências (coletadas automaticamente)
        *fpdf_submodules,
        'defusedxml',
        'defusedxml.ElementTree',
        'fonttools',
        
        # Matplotlib
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        
        # unittest (necessário pelo fpdf.sign que faz 'from unittest.mock import patch')
        *unittest_submodules,
        
        # Outros módulos padrão que o PyInstaller pode não incluir
        'html.parser',
        'xml.etree.ElementTree',
        'sqlite3',
        'tempfile',
        'subprocess',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'sphinx',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CalhaGest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon\\CalhaGest.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CalhaGest'
)
