"""Analytics package - Geração de gráficos e análises."""

from .charts import (
    create_profit_vs_cost_chart,
    create_profit_evolution_chart,
    create_pie_chart,
    create_quotes_by_status_chart,
    save_all_charts,
)

__all__ = [
    'create_profit_vs_cost_chart',
    'create_profit_evolution_chart',
    'create_pie_chart',
    'create_quotes_by_status_chart',
    'save_all_charts',
]
