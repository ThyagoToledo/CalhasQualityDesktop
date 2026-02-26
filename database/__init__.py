"""Database package - Gerenciamento do banco de dados SQLite."""

from .db import (
    # Conexão e inicialização
    get_connection,
    get_db_path,
    init_database,
    
    # Produtos
    create_product,
    get_all_products,
    get_product_by_id,
    update_product,
    delete_product,
    
    # Orçamentos
    create_quote,
    get_all_quotes,
    get_quote_by_id,
    update_quote,
    delete_quote,
    recalculate_quote_totals,
    
    # Itens de orçamento
    add_quote_item,
    remove_quote_item,
    get_dobra_value,
    
    # Estoque
    create_inventory_item,
    get_all_inventory,
    get_low_stock_items,
)

__all__ = [
    'get_connection',
    'get_db_path',
    'init_database',
    'create_product',
    'get_all_products',
    'get_product_by_id',
    'update_product',
    'delete_product',
    'create_quote',
    'get_all_quotes',
    'get_quote_by_id',
    'update_quote',
    'delete_quote',
    'recalculate_quote_totals',
    'add_quote_item',
    'remove_quote_item',
    'get_dobra_value',
    'create_inventory_item',
    'get_all_inventory',
    'get_low_stock_items',
]
