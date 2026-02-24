# -*- coding: utf-8 -*-
"""
CalhaGest - Integração com Google Drive
Faz upload automático do backup para uma pasta do Google Drive configurada pelo usuário.
"""

import os
import re
import pickle
from typing import Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE_LIBS = True
except ImportError:
    HAS_GOOGLE_LIBS = False


# Escopo necessário para fazer upload de arquivos
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Arquivo de credenciais OAuth2 (gerado no Google Cloud Console)
CREDS_FILE = os.path.join(os.path.dirname(__file__), "..", "google_creds.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "google_token.pickle")


def extract_folder_id_from_link(link: str) -> Optional[str]:
    """
    Extrai o ID da pasta a partir de um link do Google Drive.
    Suporta formatos:
      - https://drive.google.com/drive/folders/FOLDER_ID
      - https://drive.google.com/drive/folders/FOLDER_ID?usp=sharing
      - https://drive.google.com/open?id=FOLDER_ID
      - ID puro (sem link)
    Retorna None se não conseguir extrair.
    """
    if not link:
        return None

    link = link.strip()

    # Padrão: /folders/ID
    m = re.search(r'/folders/([a-zA-Z0-9_-]+)', link)
    if m:
        return m.group(1)

    # Padrão: ?id=ID ou &id=ID
    m = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', link)
    if m:
        return m.group(1)

    # Padrão: ID puro (só letras, números, _ e -)
    if re.fullmatch(r'[a-zA-Z0-9_-]{10,}', link):
        return link

    return None


def get_configured_folder_id() -> Optional[str]:
    """
    Retorna o folder ID configurado pelo usuário no banco de dados.
    Extrai o ID do link salvo em settings.drive_folder_link.
    """
    try:
        from database import db
        settings = db.get_settings()
        link = settings.get("drive_folder_link", "") or ""
        return extract_folder_id_from_link(link)
    except Exception:
        return None


def get_drive_service():
    """
    Autentica com o Google Drive e retorna uma instância do serviço.
    Na primeira vez, abre o navegador para o usuário fazer login.
    """
    if not HAS_GOOGLE_LIBS:
        return None

    creds = None

    # Tentar carregar token existente
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception:
            creds = None

    # Se não houver credenciais válidas, fazer autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            try:
                if os.path.exists(CREDS_FILE):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
                else:
                    return None
            except Exception:
                return None

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception:
        return None


def upload_backup_to_drive(backup_filepath: str, folder_id: Optional[str] = None) -> bool:
    """
    Faz upload do arquivo de backup para a pasta do Google Drive configurada.
    - Se folder_id for fornecido, usa ele.
    - Caso contrário, lê do banco de dados (settings.drive_folder_link).
    - Se o arquivo já existir na pasta, substitui; senão, cria novo.
    Retorna True se sucesso, False caso contrário.
    """
    if not HAS_GOOGLE_LIBS:
        return False

    # Resolver folder_id
    target_folder_id = folder_id or get_configured_folder_id()
    if not target_folder_id:
        return False  # Sem pasta configurada, não faz upload

    try:
        service = get_drive_service()
        if not service:
            return False

        filename = os.path.basename(backup_filepath)

        # Buscar arquivo existente na pasta para substituir
        try:
            results = service.files().list(
                q=f"name='{filename}' and '{target_folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            existing_files = results.get('files', [])
        except Exception:
            existing_files = []

        file_metadata = {'name': filename}
        media = MediaFileUpload(backup_filepath, mimetype='application/json')

        if existing_files:
            # Substituir arquivo existente
            file_id = existing_files[0]['id']
            service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        else:
            # Criar novo arquivo na pasta
            file_metadata['parents'] = [target_folder_id]
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

        return True
    except Exception:
        return False


def test_drive_connection(folder_id: Optional[str] = None) -> bool:
    """
    Testa se consegue conectar ao Google Drive e acessar a pasta configurada.
    """
    if not HAS_GOOGLE_LIBS:
        return False

    target_folder_id = folder_id or get_configured_folder_id()
    if not target_folder_id:
        return False

    try:
        service = get_drive_service()
        if not service:
            return False

        # Tentar acessar a pasta
        service.files().get(
            fileId=target_folder_id,
            fields='id, name'
        ).execute()
        return True
    except Exception:
        return False
