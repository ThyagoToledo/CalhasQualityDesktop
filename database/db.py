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
    
    # Migração: adicionar colunas width e length se não existirem
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN width REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN length REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # Migração: adicionar coluna is_installed se não existir
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN is_installed INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    # Migração: adicionar coluna pricing_unit se não existir (metro ou unidade)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN pricing_unit TEXT DEFAULT 'metro'")
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    # Migrar dados antigos: se measure > 0 e width/length = 0, copiar measure para width
    cursor.execute("UPDATE products SET width = measure WHERE width = 0 AND measure > 0")
    
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
    
    # Migração: adicionar coluna quote_type se não existir
    try:
        cursor.execute("ALTER TABLE quotes ADD COLUMN quote_type TEXT DEFAULT 'instalado'")
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    # Migração: adicionar coluna payment_methods se não existir
    try:
        cursor.execute("ALTER TABLE quotes ADD COLUMN payment_methods TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Migração: adicionar coluna discount_total se não existir
    try:
        cursor.execute("ALTER TABLE quotes ADD COLUMN discount_total REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Migração: adicionar coluna discount_type se não existir
    try:
        cursor.execute("ALTER TABLE quotes ADD COLUMN discount_type TEXT DEFAULT 'percentage'")
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
    
    # Migração: adicionar coluna discount se não existir
    try:
        cursor.execute("ALTER TABLE quote_items ADD COLUMN discount REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    # Migração: adicionar colunas width e length a quote_items
    try:
        cursor.execute("ALTER TABLE quote_items ADD COLUMN width REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE quote_items ADD COLUMN length REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # Migrar dados antigos de quote_items
    cursor.execute("UPDATE quote_items SET width = measure WHERE width = 0 AND measure > 0")
    
    # Migração: adicionar coluna pricing_unit a quote_items
    try:
        cursor.execute("ALTER TABLE quote_items ADD COLUMN pricing_unit TEXT DEFAULT 'metro'")
    except sqlite3.OperationalError:
        pass

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
    
    # Tabela de Pagamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            notes TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de Despesas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'geral',
            amount REAL NOT NULL,
            expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de Categorias de Despesas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            color TEXT DEFAULT '#6b7280',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Popular categorias padrão se não existirem
    cursor.execute("SELECT COUNT(*) FROM expense_categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('geral', 'Geral', '#6b7280'),
            ('equipamento', 'Equipamento', '#2563eb'),
            ('material', 'Material', '#f59e0b'),
            ('transporte', 'Transporte', '#8b5cf6'),
            ('aluguel', 'Aluguel', '#ef4444'),
            ('manutencao', 'Manutenção', '#10b981'),
            ('outros', 'Outros', '#ec4899'),
        ]
        cursor.executemany(
            "INSERT INTO expense_categories (key, label, color) VALUES (?, ?, ?)",
            default_categories
        )

    # Tabela de Funcionários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            phone TEXT,
            salary REAL DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de Pagamentos de Folha (payroll)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            reference_month TEXT NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)

    # Inserir configurações padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (company_name) VALUES ('CalhaGest')")
    
    # ===== OTIMIZAÇÃO: Criar índices para melhorar performance =====
    # Índices para buscas de produtos (MUITO usado na view de produtos)
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_type ON products(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name_type ON products(name, type)")
    except sqlite3.OperationalError:
        pass  # Índices já existem
    
    # Índices para quotes (usados em filtros)
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_client_name ON quotes(client_name)")
    except sqlite3.OperationalError:
        pass
    
    # Índices para tabelas de relacionamento (product_materials, quote_items)
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_materials_product_id ON product_materials(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON quote_items(quote_id)")
    except sqlite3.OperationalError:
        pass
    
    # Índices para inventory e installations
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_installations_quote_id ON installations(quote_id)")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


def _auto_backup():
    """Dispara backup automático silencioso após operações de escrita."""
    try:
        from services.backup import trigger_backup
        trigger_backup()
    except Exception:
        pass  # Nunca interromper operação principal por falha de backup


# ===== OTIMIZAÇÃO: Cache em Memória para Produtos =====
class _ProductCache:
    """Cache simples para produtos em memória. Reduz requerys ao banco."""
    def __init__(self):
        self.all_products = None  # Lista completa de produtos
        self.last_search = {}     # Cache de buscas recentes
        self.last_types = None    # Cache de tipos de produto
    
    def invalidate(self):
        """Invalida todo o cache após escrita no BD."""
        self.all_products = None
        self.last_search = {}
        self.last_types = None
    
    def get_all_products_cached(self, search: str = "", type_filter: str = ""):
        """Retorna produtos com cache. Misses vão pro BD."""
        # Gera chave de cache
        cache_key = f"{search}|{type_filter}"
        
        # Se tiver em cache, retorna
        if cache_key in self.last_search:
            return self.last_search[cache_key]
        
        # Senão, busca no BD
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
        
        # Armazena em cache
        self.last_search[cache_key] = products
        
        # Limita cache a 10 buscas recentes para não consumir muita memória
        if len(self.last_search) > 10:
            oldest_key = next(iter(self.last_search))
            del self.last_search[oldest_key]
        
        return products

_product_cache = _ProductCache()


# ============== CRUD de Produtos ==============

def create_product(name: str, type: str, measure: float, price_per_meter: float, 
                   cost: float = 0, description: str = "",
                   width: float = 0, length: float = 0,
                   is_installed: int = 1, pricing_unit: str = "metro") -> int:
    """Cria um novo produto e retorna o ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, type, measure, price_per_meter, cost, description, width, length, is_installed, pricing_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, type, measure, price_per_meter, cost, description, width, length, is_installed, pricing_unit))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    _product_cache.invalidate()  # Invalida cache após criar novo produto
    return product_id


def get_all_products(search: str = "", type_filter: str = "") -> List[Dict]:
    """Retorna todos os produtos com filtros opcionais. Usa cache para performance."""
    return _product_cache.get_all_products_cached(search, type_filter)


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
        if key in ['name', 'type', 'measure', 'price_per_meter', 'cost', 'has_dobra', 'description', 'width', 'length', 'is_installed', 'pricing_unit']:
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
        _product_cache.invalidate()  # Invalida cache após atualizar produto
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
        _product_cache.invalidate()  # Invalida cache após deletar produto
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
                      'scheduled_date', 'total', 'cost_total', 'profit', 'profitability',
                      'discount_total', 'discount_type', 'quote_type']
    
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
    
    # Buscar desconto total e tipo de desconto do orçamento
    cursor.execute("SELECT discount_total, discount_type FROM quotes WHERE id = ?", (quote_id,))
    row_quote = cursor.fetchone()
    discount_total = row_quote['discount_total'] if row_quote else 0
    discount_type = row_quote['discount_type'] if row_quote else 'percentage'
    
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) as total, 
               COALESCE(SUM(cost_total), 0) as cost_total 
        FROM quote_items WHERE quote_id = ?
    """, (quote_id,))
    
    row = cursor.fetchone()
    subtotal = row['total']  # Total antes do desconto geral
    cost_total = row['cost_total']
    
    # Aplicar desconto total sobre o subtotal (% ou valor fixo)
    if discount_type == 'value':
        discount_amount = discount_total if discount_total > 0 else 0
    else:  # percentage
        discount_amount = subtotal * (discount_total / 100) if discount_total > 0 else 0
    
    total = subtotal - discount_amount
    
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
                   custom_price: float = None, discount: float = 0) -> int:
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
    # Aplicar acréscimo de dobra se ativado no produto (apenas se NÃO usar preço customizado)
    if not custom_price and product['has_dobra']:
        dobra = get_dobra_value()
        price_per_meter += dobra
    
    # Desconto é aplicado no preço unitário (por metro/unidade)
    discount_amount = discount if discount > 0 else 0
    final_price_per_meter = price_per_meter - discount_amount
    if final_price_per_meter < 0:
        final_price_per_meter = 0
    total = meters * final_price_per_meter
    
    cost_per_meter = product['cost'] or 0
    cost_total = meters * cost_per_meter
    
    # Acessar width/length com segurança (sqlite3.Row não tem .get())
    try:
        p_width = product['width'] or 0
    except (IndexError, KeyError):
        p_width = 0
    try:
        p_length = product['length'] or 0
    except (IndexError, KeyError):
        p_length = 0
    
    # Acessar pricing_unit com segurança
    try:
        p_pricing_unit = product['pricing_unit'] or 'metro'
    except (IndexError, KeyError):
        p_pricing_unit = 'metro'

    cursor.execute("""
        INSERT INTO quote_items (quote_id, product_id, product_name, measure, 
                                meters, price_per_meter, total, cost_per_meter, cost_total, discount,
                                width, length, pricing_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (quote_id, product_id, product['name'], product['measure'],
          meters, final_price_per_meter, total, cost_per_meter, cost_total, discount,
          p_width, p_length, p_pricing_unit))
    
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


def update_quote_item(item_id: int, meters: float = None, 
                     custom_price: float = None, discount: float = None) -> bool:
    """Atualiza um item do orçamento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quote_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return False
    
    quote_id = item['quote_id']
    new_meters = meters if meters is not None else item['meters']
    new_price = custom_price if custom_price is not None else item['price_per_meter']
    new_discount = discount if discount is not None else item['discount']
    
    # Desconto é aplicado no preço unitário (por metro/unidade)
    discount_amount = new_discount if new_discount > 0 else 0
    final_price_per_unit = new_price - discount_amount
    if final_price_per_unit < 0:
        final_price_per_unit = 0
    new_total = new_meters * final_price_per_unit
    
    # Recalcular custo
    cost_per_meter = item['cost_per_meter'] or 0
    new_cost_total = new_meters * cost_per_meter
    
    cursor.execute("""
        UPDATE quote_items 
        SET meters = ?, price_per_meter = ?, discount = ?, total = ?, cost_total = ?
        WHERE id = ?
    """, (new_meters, final_price_per_unit, new_discount, new_total, new_cost_total, item_id))
    
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


# ============== CRUD de Pagamentos ==============

def add_payment(quote_id: int, amount: float, payment_method: str, notes: str = "", payment_date: str = None) -> int:
    """Registra um pagamento para um orçamento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if not payment_date:
        payment_date = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO payments (quote_id, amount, payment_method, notes, payment_date)
        VALUES (?, ?, ?, ?, ?)
    """, (quote_id, amount, payment_method, notes, payment_date))
    
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return payment_id


def get_payments_by_quote(quote_id: int) -> List[Dict]:
    """Retorna todos os pagamentos de um orçamento."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM payments WHERE quote_id = ? ORDER BY payment_date DESC
    """, (quote_id,))
    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return payments


def delete_payment(payment_id: int) -> bool:
    """Remove um pagamento."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def get_payment_summary(quote_id: int) -> Dict:
    """Retorna resumo financeiro de um orçamento: total, pago, saldo devedor."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT total FROM quotes WHERE id = ?", (quote_id,))
    row = cursor.fetchone()
    total = row['total'] if row else 0
    
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_paid FROM payments WHERE quote_id = ?
    """, (quote_id,))
    total_paid = cursor.fetchone()['total_paid']
    
    balance = total - total_paid
    
    conn.close()
    return {
        'total': total,
        'total_paid': total_paid,
        'balance': max(0, balance),
        'is_paid': balance <= 0,
    }


def get_all_payment_summaries() -> Dict[int, Dict]:
    """Retorna resumo de pagamentos para todos os orçamentos de uma só vez."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT q.id, q.total, COALESCE(SUM(p.amount), 0) as total_paid
        FROM quotes q
        LEFT JOIN payments p ON q.id = p.quote_id
        GROUP BY q.id
    """)
    
    summaries = {}
    for row in cursor.fetchall():
        qid = row['id']
        total = row['total']
        total_paid = row['total_paid']
        balance = total - total_paid
        summaries[qid] = {
            'total': total,
            'total_paid': total_paid,
            'balance': max(0, balance),
            'is_paid': balance <= 0,
        }
    
    conn.close()
    return summaries


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
    
    # Total recebido (pagamentos)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
    stats['total_received'] = cursor.fetchone()[0]
    
    # Total devedor (total dos orçamentos aprovados/completados - pagamentos)
    cursor.execute("""
        SELECT COALESCE(SUM(q.total), 0) - COALESCE((
            SELECT SUM(p.amount) FROM payments p 
            WHERE p.quote_id IN (SELECT id FROM quotes WHERE status IN ('approved', 'completed'))
        ), 0)
        FROM quotes q WHERE q.status IN ('approved', 'completed')
    """)
    stats['total_pending'] = max(0, cursor.fetchone()[0])
    
    # Orçamentos quitados
    cursor.execute("""
        SELECT COUNT(*) FROM quotes q
        WHERE q.status IN ('approved', 'completed')
        AND q.total > 0
        AND q.total <= (SELECT COALESCE(SUM(p.amount), 0) FROM payments p WHERE p.quote_id = q.id)
    """)
    stats['paid_quotes'] = cursor.fetchone()[0]
    
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


# ============== CRUD de Despesas ==============

def create_expense(description: str, category: str, amount: float,
                   expense_date: str = None, notes: str = "") -> int:
    """Cria uma nova despesa."""
    conn = get_connection()
    cursor = conn.cursor()
    if not expense_date:
        expense_date = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO expenses (description, category, amount, expense_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (description, category, amount, expense_date, notes))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return expense_id


def get_all_expenses(search: str = "", category_filter: str = "") -> List[Dict]:
    """Retorna todas as despesas."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if search:
        query += " AND description LIKE ?"
        params.append(f"%{search}%")
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY expense_date DESC"
    cursor.execute(query, params)
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return expenses


def update_expense(expense_id: int, **kwargs) -> bool:
    """Atualiza uma despesa existente."""
    conn = get_connection()
    cursor = conn.cursor()
    allowed = ['description', 'category', 'amount', 'expense_date', 'notes']
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(expense_id)
    cursor.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_expense(expense_id: int) -> bool:
    """Exclui uma despesa."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def get_expenses_summary() -> Dict:
    """Retorna resumo de despesas."""
    conn = get_connection()
    cursor = conn.cursor()
    # Total geral
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
    total = cursor.fetchone()[0]
    # Total mês atual
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE strftime('%Y-%m', expense_date) = strftime('%Y-%m', 'now')
    """)
    month_total = cursor.fetchone()[0]
    # Por categoria
    cursor.execute("""
        SELECT category, COALESCE(SUM(amount), 0) as total
        FROM expenses GROUP BY category ORDER BY total DESC
    """)
    by_category = {row['category']: row['total'] for row in cursor.fetchall()}
    # Mensal (últimos 12 meses)
    cursor.execute("""
        SELECT strftime('%Y-%m', expense_date) as month, COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE expense_date >= date('now', '-12 months')
        GROUP BY month ORDER BY month DESC
    """)
    monthly = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {
        'total': total,
        'month_total': month_total,
        'by_category': by_category,
        'monthly': monthly,
    }


# ============== CRUD de Categorias de Despesas ==============

def get_all_expense_categories() -> List[Dict]:
    """Retorna todas as categorias de despesas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, key, label, color, created_at
        FROM expense_categories
        ORDER BY label
    """)
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories


def create_expense_category(key: str, label: str, color: str = '#6b7280') -> int:
    """Cria uma nova categoria de despesa."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO expense_categories (key, label, color)
            VALUES (?, ?, ?)
        """, (key, label, color))
        cat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        _auto_backup()
        return cat_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Já existe uma categoria com esta chave.")


def update_expense_category(cat_id: int, label: str, color: str) -> bool:
    """Atualiza uma categoria de despesa."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expense_categories
        SET label = ?, color = ?
        WHERE id = ?
    """, (label, color, cat_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_expense_category(cat_id: int) -> bool:
    """Exclui uma categoria de despesa se não estiver em uso."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar se a categoria está em uso
    cursor.execute("SELECT key FROM expense_categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    category_key = row['key']
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (category_key,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        raise ValueError(f"Não é possível excluir. Existem {count} despesa(s) usando esta categoria.")
    
    cursor.execute("DELETE FROM expense_categories WHERE id = ?", (cat_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Funcionários ==============

def create_employee(name: str, role: str = "", phone: str = "", salary: float = 0) -> int:
    """Cria um novo funcionário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, role, phone, salary) VALUES (?, ?, ?, ?)
    """, (name, role, phone, salary))
    emp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return emp_id


def get_all_employees(active_only: bool = True) -> List[Dict]:
    """Retorna todos os funcionários."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM employees"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY name"
    cursor.execute(query)
    employees = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return employees


def update_employee(employee_id: int, **kwargs) -> bool:
    """Atualiza um funcionário."""
    conn = get_connection()
    cursor = conn.cursor()
    allowed = ['name', 'role', 'phone', 'salary', 'active']
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(employee_id)
    cursor.execute(f"UPDATE employees SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def delete_employee(employee_id: int) -> bool:
    """Exclui um funcionário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


# ============== CRUD de Folha de Pagamento ==============

def add_payroll(employee_id: int, amount: float, reference_month: str,
                payment_date: str = None, notes: str = "") -> int:
    """Registra um pagamento de folha."""
    conn = get_connection()
    cursor = conn.cursor()
    if not payment_date:
        payment_date = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO payroll (employee_id, amount, reference_month, payment_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, amount, reference_month, payment_date, notes))
    pay_id = cursor.lastrowid
    conn.commit()
    conn.close()
    _auto_backup()
    return pay_id


def get_payroll_by_employee(employee_id: int) -> List[Dict]:
    """Retorna todos os pagamentos de folha de um funcionário."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, e.name as employee_name FROM payroll p
        JOIN employees e ON p.employee_id = e.id
        WHERE p.employee_id = ? ORDER BY p.reference_month DESC
    """, (employee_id,))
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def get_all_payroll(month_filter: str = "") -> List[Dict]:
    """Retorna todos os pagamentos de folha."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.*, e.name as employee_name, e.role as employee_role
        FROM payroll p
        JOIN employees e ON p.employee_id = e.id
    """
    params = []
    if month_filter:
        query += " WHERE p.reference_month = ?"
        params.append(month_filter)
    query += " ORDER BY p.reference_month DESC, e.name"
    cursor.execute(query, params)
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def delete_payroll(payroll_id: int) -> bool:
    """Remove um pagamento de folha."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payroll WHERE id = ?", (payroll_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    if success:
        _auto_backup()
    return success


def get_payroll_summary() -> Dict:
    """Retorna resumo da folha de pagamento."""
    conn = get_connection()
    cursor = conn.cursor()
    # Total geral pago
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payroll")
    total = cursor.fetchone()[0]
    # Total mês atual
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM payroll
        WHERE reference_month = strftime('%Y-%m', 'now')
    """)
    month_total = cursor.fetchone()[0]
    # Total de funcionários ativos
    cursor.execute("SELECT COUNT(*) FROM employees WHERE active = 1")
    active_employees = cursor.fetchone()[0]
    # Folha mensal prevista (soma dos salários dos ativos)
    cursor.execute("SELECT COALESCE(SUM(salary), 0) FROM employees WHERE active = 1")
    expected_monthly = cursor.fetchone()[0]
    conn.close()
    return {
        'total_paid': total,
        'month_total': month_total,
        'active_employees': active_employees,
        'expected_monthly': expected_monthly,
    }


def get_financial_overview() -> Dict:
    """Retorna visão geral financeira combinando receitas, despesas e folha."""
    stats = get_dashboard_stats()
    expenses_summary = get_expenses_summary()
    payroll_summary = get_payroll_summary()
    
    total_income = stats.get('total_received', 0)
    total_expenses = expenses_summary.get('total', 0)
    total_payroll = payroll_summary.get('total_paid', 0)
    total_outflow = total_expenses + total_payroll
    balance = total_income - total_outflow
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_payroll': total_payroll,
        'total_outflow': total_outflow,
        'balance': balance,
        'pending_receivables': stats.get('total_pending', 0),
        'expenses_by_category': expenses_summary.get('by_category', {}),
        'expenses_month': expenses_summary.get('month_total', 0),
        'payroll_month': payroll_summary.get('month_total', 0),
    }


# Inicializar banco ao importar o módulo
init_database()
