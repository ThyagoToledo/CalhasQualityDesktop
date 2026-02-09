"""
CalhaGest - Banco de Dados SQLite
Gerencia conexão e operações CRUD para todas as entidades do sistema.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "calhagest.db")


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db_path() -> str:
    """Retorna o caminho do arquivo do banco de dados."""
    return DB_PATH


def init_database():
    """Inicializa o banco de dados com todas as tabelas necessárias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT DEFAULT 'CalhaGest',
            company_phone TEXT,
            company_email TEXT,
            company_address TEXT,
            company_cnpj TEXT,
            company_logo BLOB,
            dobra_value REAL DEFAULT 5.0,
            backup_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração: adicionar coluna dobra_value se não existir
    try:
        cursor.execute("ALTER TABLE settings ADD COLUMN dobra_value REAL DEFAULT 5.0")
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    # Migração: adicionar coluna backup_path se não existir
    try:
        cursor.execute("ALTER TABLE settings ADD COLUMN backup_path TEXT")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Tabela de Tipos de Produto (dinâmica)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir tipos padrão se tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM product_types")
    if cursor.fetchone()[0] == 0:
        default_types = [
            ('calha', 'Calha'),
            ('rufo', 'Rufo'),
            ('pingadeira', 'Pingadeira'),
        ]
        cursor.executemany(
            "INSERT INTO product_types (key, label) VALUES (?, ?)",
            default_types
        )
    
    # Tabela de Produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            measure REAL NOT NULL,
            price_per_meter REAL NOT NULL,
            cost REAL DEFAULT 0,
            has_dobra INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração: adicionar coluna has_dobra se não existir
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN has_dobra INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Tabela de Materiais vinculados a Produtos (para descontar estoque)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            inventory_id INTEGER NOT NULL,
            quantity_per_unit REAL NOT NULL DEFAULT 1,
            unit_type TEXT NOT NULL DEFAULT 'metro' CHECK(unit_type IN ('metro', 'cm', 'unidade')),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de Orçamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_phone TEXT,
            client_address TEXT,
            total REAL DEFAULT 0,
            cost_total REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            profitability REAL DEFAULT 0,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'approved', 'completed')),
            technical_notes TEXT,
            contract_terms TEXT,
            payment_methods TEXT DEFAULT '',
            scheduled_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migração: adicionar coluna payment_methods se não existir
    try:
        cursor.execute("ALTER TABLE quotes ADD COLUMN payment_methods TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Migração: remover CHECK constraint de produtos (tipo dinâmico)
    # SQLite não permite ALTER TABLE para remover constraints,
    # mas como criamos a tabela sem o CHECK, novas databases já ficam OK.
    # Para databases existentes, o CHECK não impede inserção de novos tipos
    # se a tabela foi recriada sem ele.
    
    # Tabela de Itens do Orçamento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quote_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            measure REAL NOT NULL,
            meters REAL NOT NULL,
            price_per_meter REAL NOT NULL,
            total REAL NOT NULL,
            cost_per_meter REAL DEFAULT 0,
            cost_total REAL DEFAULT 0,
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    """)
    
    # Tabela de Inventário/Estoque
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'unidades',
            min_stock REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de Instalações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS installations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            address TEXT NOT NULL,
            scheduled_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in-progress', 'completed', 'cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
        )
    """)
    
    # Inserir configurações padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (company_name) VALUES ('CalhaGest')")
    
    conn.commit()
    conn.close()


def _auto_backup():
    """Dispara backup automático silencioso após operações de escrita."""
    try:
        from services.backup import trigger_backup
        trigger_backup()
    except Exception:
        pass  # Nunca interromper operação principal por falha de backup


# ============== CRUD de Produtos ==============

def create_product(name: str, type: str, measure: float, price_per_meter: float, 
                   cost: float = 0, description: str = "") -> int:
    """Cria um novo produto e retorna o ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, type, measure, price_per_meter, cost, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, type, measure, price_per_meter, cost, description))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return product_id


def get_all_products(search: str = "", type_filter: str = "") -> List[Dict]:
    """Retorna todos os produtos com filtros opcionais."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    if type_filter:
        query += " AND type = ?"
        params.append(type_filter)
    
    query += " ORDER BY name"
    cursor.execute(query, params)
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Retorna um produto pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_product(product_id: int, **kwargs) -> bool:
    """Atualiza um produto existente."""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['name', 'type', 'measure', 'price_per_meter', 'cost', 'has_dobra', 'description']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
    
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(product_id)
    
    cursor.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_product(product_id: int) -> bool:
    """Exclui um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Orçamentos ==============

def create_quote(client_name: str, client_phone: str = "", client_address: str = "",
                 technical_notes: str = "", contract_terms: str = "", 
                 payment_methods: str = "", scheduled_date: str = None) -> int:
    """Cria um novo orçamento e retorna o ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quotes (client_name, client_phone, client_address, 
                           technical_notes, contract_terms, payment_methods, scheduled_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (client_name, client_phone, client_address, technical_notes, 
          contract_terms, payment_methods, scheduled_date))
    quote_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return quote_id


def get_all_quotes(search: str = "", status_filter: str = "") -> List[Dict]:
    """Retorna todos os orçamentos com filtros opcionais."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM quotes WHERE 1=1"
    params = []
    
    if search:
        query += " AND (client_name LIKE ? OR client_address LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    quotes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return quotes


def get_quote_by_id(quote_id: int) -> Optional[Dict]:
    """Retorna um orçamento pelo ID com seus itens."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    quote = dict(row)
    
    cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))
    quote['items'] = [dict(item) for item in cursor.fetchall()]
    
    conn.close()
    return quote


def update_quote(quote_id: int, **kwargs) -> bool:
    """Atualiza um orçamento existente."""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['client_name', 'client_phone', 'client_address', 'status',
                      'technical_notes', 'contract_terms', 'payment_methods',
                      'scheduled_date', 'total', 'cost_total', 'profit', 'profitability']
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
    
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(quote_id)
    
    cursor.execute(f"UPDATE quotes SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_quote(quote_id: int) -> bool:
    """Exclui um orçamento e seus itens."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def recalculate_quote_totals(quote_id: int):
    """Recalcula os totais do orçamento baseado nos itens."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) as total, 
               COALESCE(SUM(cost_total), 0) as cost_total 
        FROM quote_items WHERE quote_id = ?
    """, (quote_id,))
    
    row = cursor.fetchone()
    total = row['total']
    cost_total = row['cost_total']
    profit = total - cost_total
    profitability = (profit / total * 100) if total > 0 else 0
    
    cursor.execute("""
        UPDATE quotes SET total = ?, cost_total = ?, profit = ?, profitability = ?,
                         updated_at = ? WHERE id = ?
    """, (total, cost_total, profit, profitability, datetime.now().isoformat(), quote_id))
    
    conn.commit()
    conn.close()


# ============== CRUD de Itens do Orçamento ==============

def get_dobra_value() -> float:
    """Retorna o valor da dobra configurado nas settings."""
    settings = get_settings()
    return float(settings.get('dobra_value', 5.0) or 5.0)


def add_quote_item(quote_id: int, product_id: int, meters: float, 
                   custom_price: float = None) -> int:
    """Adiciona um item ao orçamento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar dados do produto
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        raise ValueError("Produto não encontrado")
    
    price_per_meter = custom_price if custom_price else product['price_per_meter']
    # Aplicar acréscimo de dobra se ativado no produto
    if product['has_dobra']:
        dobra = get_dobra_value()
        price_per_meter += dobra
    total = meters * price_per_meter
    cost_per_meter = product['cost'] or 0
    cost_total = meters * cost_per_meter
    
    cursor.execute("""
        INSERT INTO quote_items (quote_id, product_id, product_name, measure, 
                                meters, price_per_meter, total, cost_per_meter, cost_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (quote_id, product_id, product['name'], product['measure'],
          meters, price_per_meter, total, cost_per_meter, cost_total))
    
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    recalculate_quote_totals(quote_id)
    _auto_backup()
    return item_id


def remove_quote_item(item_id: int) -> bool:
    """Remove um item do orçamento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT quote_id FROM quote_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    quote_id = row['quote_id']
    cursor.execute("DELETE FROM quote_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    recalculate_quote_totals(quote_id)
    _auto_backup()
    return True


# ============== CRUD de Inventário ==============

def create_inventory_item(name: str, type: str, quantity: float, 
                          unit: str = "unidades", min_stock: float = 0) -> int:
    """Cria um novo item no inventário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inventory (name, type, quantity, unit, min_stock)
        VALUES (?, ?, ?, ?, ?)
    """, (name, type, quantity, unit, min_stock))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return item_id


def get_all_inventory(search: str = "", type_filter: str = "") -> List[Dict]:
    """Retorna todos os itens do inventário."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM inventory WHERE 1=1"
    params = []
    
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    
    if type_filter:
        query += " AND type = ?"
        params.append(type_filter)
    
    query += " ORDER BY name"
    cursor.execute(query, params)
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


def get_low_stock_items() -> List[Dict]:
    """Retorna itens com estoque abaixo do mínimo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE quantity < min_stock AND min_stock > 0")
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


def update_inventory_quantity(item_id: int, quantity_change: float, 
                              operation: str = "add") -> bool:
    """Atualiza a quantidade de um item (add/remove/set)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if operation == "add":
        cursor.execute("""
            UPDATE inventory SET quantity = quantity + ?, updated_at = ? WHERE id = ?
        """, (quantity_change, datetime.now().isoformat(), item_id))
    elif operation == "remove":
        cursor.execute("""
            UPDATE inventory SET quantity = MAX(0, quantity - ?), updated_at = ? WHERE id = ?
        """, (quantity_change, datetime.now().isoformat(), item_id))
    elif operation == "set":
        cursor.execute("""
            UPDATE inventory SET quantity = ?, updated_at = ? WHERE id = ?
        """, (quantity_change, datetime.now().isoformat(), item_id))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_inventory_item(item_id: int) -> bool:
    """Exclui um item do inventário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Instalações ==============

def create_installation(quote_id: int, scheduled_date: str, notes: str = "") -> int:
    """Cria uma nova instalação vinculada a um orçamento aprovado."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar dados do orçamento
    cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
    quote = cursor.fetchone()
    if not quote:
        conn.close()
        raise ValueError("Orçamento não encontrado")
    
    if quote['status'] not in ['approved', 'completed']:
        conn.close()
        raise ValueError("Orçamento precisa estar aprovado")
    
    cursor.execute("""
        INSERT INTO installations (quote_id, client_name, address, scheduled_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (quote_id, quote['client_name'], quote['client_address'] or "", 
          scheduled_date, notes))
    
    installation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return installation_id


def get_all_installations(status_filter: str = "") -> List[Dict]:
    """Retorna todas as instalações."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM installations WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY scheduled_date ASC"
    cursor.execute(query, params)
    installations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return installations


def update_installation_status(installation_id: int, status: str) -> bool:
    """Atualiza o status de uma instalação."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE installations SET status = ?, updated_at = ? WHERE id = ?
    """, (status, datetime.now().isoformat(), installation_id))
    
    # Se completou a instalação, atualizar o orçamento também
    if status == "completed":
        cursor.execute("SELECT quote_id FROM installations WHERE id = ?", (installation_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE quotes SET status = 'completed', updated_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), row['quote_id']))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_installation(installation_id: int) -> bool:
    """Exclui uma instalação."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM installations WHERE id = ?", (installation_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== Configurações ==============

def get_settings() -> Dict:
    """Retorna as configurações do sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def update_settings(**kwargs) -> bool:
    """Atualiza as configurações do sistema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['company_name', 'company_phone', 'company_email',
                      'company_address', 'company_cnpj', 'company_logo',
                      'dobra_value', 'backup_path']
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
    
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    
    cursor.execute(f"UPDATE settings SET {', '.join(fields)} WHERE id = 1", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Tipos de Produto ==============

def get_all_product_types() -> List[Dict]:
    """Retorna todos os tipos de produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_types ORDER BY label")
    types = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return types


def create_product_type(key: str, label: str) -> int:
    """Cria um novo tipo de produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO product_types (key, label) VALUES (?, ?)",
        (key.lower().strip(), label.strip())
    )
    type_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return type_id


def delete_product_type(type_id: int) -> bool:
    """Exclui um tipo de produto (não permite excluir os padrão)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_types WHERE id = ?", (type_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Materiais do Produto ==============

def get_product_materials(product_id: int) -> List[Dict]:
    """Retorna os materiais vinculados a um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pm.*, i.name as inventory_name, i.unit as inventory_unit, i.quantity as inventory_quantity
        FROM product_materials pm
        JOIN inventory i ON pm.inventory_id = i.id
        WHERE pm.product_id = ?
    """, (product_id,))
    materials = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return materials


def add_product_material(product_id: int, inventory_id: int, 
                         quantity_per_unit: float, unit_type: str = "metro") -> int:
    """Vincula um material do estoque a um produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO product_materials (product_id, inventory_id, quantity_per_unit, unit_type)
        VALUES (?, ?, ?, ?)
    """, (product_id, inventory_id, quantity_per_unit, unit_type))
    mat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return mat_id


def remove_product_material(material_id: int) -> bool:
    """Remove um vínculo material-produto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_materials WHERE id = ?", (material_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== Lógica de Estoque por Orçamento ==============

def deduct_stock_for_quote(quote_id: int) -> List[str]:
    """
    Deduz o estoque para todos os itens de um orçamento aprovado.
    Retorna lista de avisos (ex: estoque insuficiente).
    """
    conn = get_connection()
    cursor = conn.cursor()
    warnings = []
    
    # Buscar itens do orçamento
    cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))
    quote_items = [dict(row) for row in cursor.fetchall()]
    
    for qi in quote_items:
        product_id = qi.get("product_id")
        meters = qi.get("meters", 0)
        
        if not product_id:
            continue
        
        # Buscar materiais vinculados ao produto
        cursor.execute("""
            SELECT pm.*, i.name as inv_name, i.quantity as inv_qty, i.unit as inv_unit
            FROM product_materials pm
            JOIN inventory i ON pm.inventory_id = i.id
            WHERE pm.product_id = ?
        """, (product_id,))
        materials = [dict(row) for row in cursor.fetchall()]
        
        for mat in materials:
            unit_type = mat.get("unit_type", "metro")
            qty_per_unit = mat.get("quantity_per_unit", 0)
            
            # Calcular quantidade a deduzir
            if unit_type == "metro":
                deduct = meters * qty_per_unit
            elif unit_type == "cm":
                deduct = (meters * 100) * qty_per_unit
            else:  # unidade
                deduct = qty_per_unit
            
            inv_id = mat["inventory_id"]
            inv_name = mat.get("inv_name", "?")
            inv_qty = mat.get("inv_qty", 0)
            
            if inv_qty < deduct:
                warnings.append(
                    f"Estoque insuficiente: {inv_name} "
                    f"(disponível: {inv_qty:.1f}, necessário: {deduct:.1f})"
                )
            
            # Deduzir mesmo assim (vai para 0 no mínimo)
            cursor.execute("""
                UPDATE inventory SET quantity = MAX(0, quantity - ?), updated_at = ? WHERE id = ?
            """, (deduct, datetime.now().isoformat(), inv_id))
    
    conn.commit()
    conn.close()
    _auto_backup()
    return warnings


# ============== Analytics ==============

def get_dashboard_stats() -> Dict:
    """Retorna estatísticas para o dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total de orçamentos
    cursor.execute("SELECT COUNT(*) FROM quotes")
    stats['total_quotes'] = cursor.fetchone()[0]
    
    # Orçamentos aprovados
    cursor.execute("SELECT COUNT(*) FROM quotes WHERE status IN ('approved', 'completed')")
    stats['approved_quotes'] = cursor.fetchone()[0]
    
    # Faturamento total (orçamentos aprovados + completados)
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) FROM quotes 
        WHERE status IN ('approved', 'completed')
    """)
    stats['total_revenue'] = cursor.fetchone()[0]
    
    # Lucro total
    cursor.execute("""
        SELECT COALESCE(SUM(profit), 0) FROM quotes 
        WHERE status IN ('approved', 'completed')
    """)
    stats['total_profit'] = cursor.fetchone()[0]
    
    # Custo total
    cursor.execute("""
        SELECT COALESCE(SUM(cost_total), 0) FROM quotes 
        WHERE status IN ('approved', 'completed')
    """)
    stats['total_cost'] = cursor.fetchone()[0]
    
    # 3 orçamentos mais recentes
    cursor.execute("""
        SELECT * FROM quotes ORDER BY created_at DESC LIMIT 3
    """)
    stats['recent_quotes'] = [dict(row) for row in cursor.fetchall()]
    
    # Instalações pendentes
    cursor.execute("SELECT COUNT(*) FROM installations WHERE status = 'pending'")
    stats['pending_installations'] = cursor.fetchone()[0]
    
    # Itens com estoque baixo
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity < min_stock AND min_stock > 0")
    stats['low_stock_count'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


def get_monthly_analytics() -> List[Dict]:
    """Retorna análise mensal de faturamento e lucro."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as quote_count,
            COALESCE(SUM(CASE WHEN status IN ('approved', 'completed') THEN total ELSE 0 END), 0) as revenue,
            COALESCE(SUM(CASE WHEN status IN ('approved', 'completed') THEN cost_total ELSE 0 END), 0) as cost,
            COALESCE(SUM(CASE WHEN status IN ('approved', 'completed') THEN profit ELSE 0 END), 0) as profit
        FROM quotes
        WHERE created_at >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
    """)
    
    analytics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return analytics


# Inicializar banco ao importar o módulo
init_database()
