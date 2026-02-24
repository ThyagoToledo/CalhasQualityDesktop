# -*- coding: utf-8 -*-
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
CalhaGest - Sistema de Backup Automático
Exporta/importa todos os dados do banco para um arquivo JSON em Documentos.
O backup é salvo automaticamente a cada operação de criação/edição/exclusão.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Chave usada no settings do banco para armazenar o caminho do backup
BACKUP_PATH_KEY = "backup_path"

# Nome do arquivo de backup
BACKUP_FILENAME = "calhagest_backup.json"


def get_default_backup_dir() -> str:
    """Retorna o diretório padrão de backup (Documentos/CalhaGest)."""
    docs = Path.home() / "Documents" / "CalhaGest"
    return str(docs)


def get_backup_dir() -> str:
    """Retorna o diretório configurado para backup."""
    try:
        from database import db
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT backup_path FROM settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row and row["backup_path"]:
            return row["backup_path"]
    except Exception:
        pass
    return get_default_backup_dir()


def set_backup_dir(path: str) -> bool:
    """Define o diretório de backup nas configurações."""
    from database import db
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE settings SET backup_path = ? WHERE id = 1", (path,))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception:
        success = False
    conn.close()
    return success


def get_backup_filepath() -> str:
    """Retorna o caminho completo do arquivo de backup."""
    return os.path.join(get_backup_dir(), BACKUP_FILENAME)


def export_all_data() -> Dict[str, Any]:
    """Exporta todos os dados do banco de dados para um dicionário."""
    from database import db
    conn = db.get_connection()
    cursor = conn.cursor()

    data = {
        "meta": {
            "app": "CalhaGest",
            "version": "2.0.0",
            "exported_at": datetime.now().isoformat(),
        },
        "settings": {},
        "product_types": [],
        "products": [],
        "product_materials": [],
        "quotes": [],
        "quote_items": [],
        "inventory": [],
        "installations": [],
    }

    # Settings
    cursor.execute("SELECT * FROM settings LIMIT 1")
    row = cursor.fetchone()
    if row:
        d = dict(row)
        # Remover campos binários (logo) e backup_path do export
        d.pop("company_logo", None)
        data["settings"] = d

    # Product types
    cursor.execute("SELECT * FROM product_types ORDER BY id")
    data["product_types"] = [dict(r) for r in cursor.fetchall()]

    # Products
    cursor.execute("SELECT * FROM products ORDER BY id")
    data["products"] = [dict(r) for r in cursor.fetchall()]

    # Product materials
    cursor.execute("SELECT * FROM product_materials ORDER BY id")
    data["product_materials"] = [dict(r) for r in cursor.fetchall()]

    # Quotes
    cursor.execute("SELECT * FROM quotes ORDER BY id")
    data["quotes"] = [dict(r) for r in cursor.fetchall()]

    # Quote items
    cursor.execute("SELECT * FROM quote_items ORDER BY id")
    data["quote_items"] = [dict(r) for r in cursor.fetchall()]

    # Inventory
    cursor.execute("SELECT * FROM inventory ORDER BY id")
    data["inventory"] = [dict(r) for r in cursor.fetchall()]

    # Installations
    cursor.execute("SELECT * FROM installations ORDER BY id")
    data["installations"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return data


def save_backup() -> str:
    """
    Salva o backup automático no diretório configurado (LOCAL APENAS).
    Retorna o caminho do arquivo salvo.
    """
    backup_dir = get_backup_dir()
    os.makedirs(backup_dir, exist_ok=True)

    data = export_all_data()
    filepath = os.path.join(backup_dir, BACKUP_FILENAME)

    # Escrever em arquivo temporário primeiro, depois renomear (atômico)
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Substituir arquivo antigo
        if os.path.exists(filepath):
            os.replace(tmp_path, filepath)
        else:
            os.rename(tmp_path, filepath)
    except Exception:
        # Se falhar o rename, tentar o caminho direto
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def trigger_backup():
    """
    Dispara o backup silenciosamente em background.
    Nunca lança exceção - apenas loga erros.
    """
    try:
        save_backup()
    except Exception:
        pass  # Backup silencioso - não interromper operação principal



def load_backup(filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Lê o arquivo de backup e retorna os dados.
    Se filepath não for informado, usa o caminho padrão.
    """
    if not filepath:
        filepath = get_backup_filepath()

    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def restore_from_backup(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Restaura todos os dados a partir de um arquivo de backup JSON.
    Retorna um resumo com a contagem de registros restaurados.
    """
    data = load_backup(filepath)
    if not data:
        raise FileNotFoundError("Arquivo de backup não encontrado ou vazio.")

    from database import db
    conn = db.get_connection()
    cursor = conn.cursor()

    summary = {}

    try:
        # 1. Restaurar settings (atualizar, não recriar)
        s = data.get("settings", {})
        if s:
            fields_to_restore = [
                "company_name", "company_phone", "company_email",
                "company_address", "company_cnpj", "dobra_value",
            ]
            sets = []
            vals = []
            for f in fields_to_restore:
                if f in s:
                    sets.append(f"{f} = ?")
                    vals.append(s[f])
            if sets:
                sets.append("updated_at = ?")
                vals.append(datetime.now().isoformat())
                cursor.execute(
                    f"UPDATE settings SET {', '.join(sets)} WHERE id = 1", vals
                )
            summary["settings"] = 1

        # 2. Limpar tabelas dependentes na ordem correta
        cursor.execute("DELETE FROM product_materials")
        cursor.execute("DELETE FROM quote_items")
        cursor.execute("DELETE FROM installations")
        cursor.execute("DELETE FROM quotes")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM inventory")
        cursor.execute("DELETE FROM product_types")

        # 3. Restaurar product_types
        for pt in data.get("product_types", []):
            cursor.execute(
                "INSERT INTO product_types (id, key, label, created_at) VALUES (?, ?, ?, ?)",
                (pt["id"], pt["key"], pt["label"], pt.get("created_at")),
            )
        summary["product_types"] = len(data.get("product_types", []))

        # 4. Restaurar products
        for p in data.get("products", []):
            cursor.execute(
                """INSERT INTO products (id, name, type, measure, price_per_meter,
                   cost, has_dobra, description, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["id"], p["name"], p["type"], p["measure"],
                    p["price_per_meter"], p.get("cost", 0),
                    p.get("has_dobra", 0), p.get("description", ""),
                    p.get("created_at"), p.get("updated_at"),
                ),
            )
        summary["products"] = len(data.get("products", []))

        # 5. Restaurar inventory
        for inv in data.get("inventory", []):
            cursor.execute(
                """INSERT INTO inventory (id, name, type, quantity, unit, min_stock,
                   created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    inv["id"], inv["name"], inv["type"], inv["quantity"],
                    inv.get("unit", "unidades"), inv.get("min_stock", 0),
                    inv.get("created_at"), inv.get("updated_at"),
                ),
            )
        summary["inventory"] = len(data.get("inventory", []))

        # 6. Restaurar product_materials
        for pm in data.get("product_materials", []):
            cursor.execute(
                """INSERT INTO product_materials (id, product_id, inventory_id,
                   quantity_per_unit, unit_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    pm["id"], pm["product_id"], pm["inventory_id"],
                    pm.get("quantity_per_unit", 1), pm.get("unit_type", "metro"),
                ),
            )
        summary["product_materials"] = len(data.get("product_materials", []))

        # 7. Restaurar quotes
        for q in data.get("quotes", []):
            cursor.execute(
                """INSERT INTO quotes (id, client_name, client_phone, client_address,
                   total, cost_total, profit, profitability, status,
                   technical_notes, contract_terms, payment_methods,
                   scheduled_date, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q["id"], q["client_name"], q.get("client_phone", ""),
                    q.get("client_address", ""), q.get("total", 0),
                    q.get("cost_total", 0), q.get("profit", 0),
                    q.get("profitability", 0), q.get("status", "draft"),
                    q.get("technical_notes", ""), q.get("contract_terms", ""),
                    q.get("payment_methods", ""), q.get("scheduled_date"),
                    q.get("created_at"), q.get("updated_at"),
                ),
            )
        summary["quotes"] = len(data.get("quotes", []))

        # 8. Restaurar quote_items
        for qi in data.get("quote_items", []):
            cursor.execute(
                """INSERT INTO quote_items (id, quote_id, product_id, product_name,
                   measure, meters, price_per_meter, total,
                   cost_per_meter, cost_total)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    qi["id"], qi["quote_id"], qi.get("product_id"),
                    qi["product_name"], qi["measure"], qi["meters"],
                    qi["price_per_meter"], qi["total"],
                    qi.get("cost_per_meter", 0), qi.get("cost_total", 0),
                ),
            )
        summary["quote_items"] = len(data.get("quote_items", []))

        # 9. Restaurar installations
        for inst in data.get("installations", []):
            cursor.execute(
                """INSERT INTO installations (id, quote_id, client_name, address,
                   scheduled_date, status, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    inst["id"], inst["quote_id"], inst["client_name"],
                    inst.get("address", ""), inst["scheduled_date"],
                    inst.get("status", "pending"), inst.get("notes", ""),
                    inst.get("created_at"), inst.get("updated_at"),
                ),
            )
        summary["installations"] = len(data.get("installations", []))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Salvar backup atualizado após restauração
    trigger_backup()

    return summary
