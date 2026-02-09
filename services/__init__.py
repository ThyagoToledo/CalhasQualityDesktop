# -*- coding: utf-8 -*-
"""
CalhaGest - Services Package
Módulos de funcionalidades principais: backup automático e geração de PDF.
"""

# Backup automático
from services.backup import (
    get_default_backup_dir,
    get_backup_dir,
    set_backup_dir,
    get_backup_filepath,
    export_all_data,
    save_backup,
    trigger_backup,
    load_backup,
    restore_from_backup,
)

# Gerador de PDF
from services.pdf_generator import generate_quote_pdf

__all__ = [
    # Backup
    'get_default_backup_dir',
    'get_backup_dir',
    'set_backup_dir',
    'get_backup_filepath',
    'export_all_data',
    'save_backup',
    'trigger_backup',
    'load_backup',
    'restore_from_backup',
    # PDF
    'generate_quote_pdf',
]
