"""Views package - Telas da aplicação."""

from .dashboard import DashboardView
from .products import ProductsView
from .quotes import QuotesView
from .installations import InstallationsView
from .inventory import InventoryView
from .analytics import AnalyticsView
from .settings import SettingsView
from .expenses import ExpensesView
from .payroll import PayrollView

__all__ = [
    'DashboardView',
    'ProductsView',
    'QuotesView',
    'InstallationsView',
    'InventoryView',
    'AnalyticsView',
    'SettingsView',
    'ExpensesView',
    'PayrollView',
]
