"""
Utilitários do sistema MikroTik Manager
"""

try:
    from .charts import generate_chart
    CHARTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Charts module not available: {e}")
    CHARTS_AVAILABLE = False
    
    def generate_chart(*args, **kwargs):
        """Fallback function when charts are not available"""
        return "<div class='alert alert-warning'>Gráficos não disponíveis - matplotlib não instalado</div>"

from .helpers import (
    check_system_date,
    initialize_default_data,
    get_selected_company,
    format_bytes,
    format_duration,
    calculate_percentage,
    get_system_info,
    backup_database,
    restore_database
)

from .decorators import (
    login_required,
    admin_required,
    company_required,
    rate_limit
)

__all__ = [
    'generate_chart',
    'CHARTS_AVAILABLE',
    'check_system_date',
    'initialize_default_data',
    'get_selected_company',
    'format_bytes',
    'format_duration',
    'calculate_percentage',
    'get_system_info',
    'backup_database',
    'restore_database',
    'login_required',
    'admin_required',
    'company_required',
    'rate_limit'
]
