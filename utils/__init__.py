"""
Módulo de utilitários para o MikroTik Manager
"""

# Importações seguras para charts
try:
    from .charts import (
        generate_chart,
        generate_usage_chart,
        generate_bandwidth_chart,
        generate_user_activity_chart
    )
    CHARTS_AVAILABLE = True
except ImportError as e:
    print(f"Charts não disponíveis: {e}")
    CHARTS_AVAILABLE = False
    
    # Funções dummy para charts
    def generate_chart(*args, **kwargs):
        return None
    
    def generate_usage_chart(*args, **kwargs):
        return None
    
    def generate_bandwidth_chart(*args, **kwargs):
        return None
    
    def generate_user_activity_chart(*args, **kwargs):
        return None

# Importações dos helpers
from .helpers import (
    check_system_date,
    initialize_default_data,
    get_selected_company,
    set_selected_company,
    format_bytes,
    format_time_duration,
    backup_database,
    get_system_info,
    validate_mikrotik_config,
    clean_old_logs,
    get_database_stats,
    convert_timezone,
    sanitize_filename,
    check_disk_space,
    generate_report_data
)

# Importações dos decorators
from .decorators import (
    login_required,
    admin_required,
    company_required,
    rate_limit
)

# Lista de exports
__all__ = [
    # Charts
    'generate_chart',
    'generate_usage_chart', 
    'generate_bandwidth_chart',
    'generate_user_activity_chart',
    'CHARTS_AVAILABLE',
    
    # Helpers
    'check_system_date',
    'initialize_default_data',
    'get_selected_company',
    'set_selected_company',
    'format_bytes',
    'format_time_duration',
    'backup_database',
    'get_system_info',
    'validate_mikrotik_config',
    'clean_old_logs',
    'get_database_stats',
    'convert_timezone',
    'sanitize_filename',
    'check_disk_space',
    'generate_report_data',
    
    # Decorators
    'login_required',
    'admin_required',
    'company_required',
    'rate_limit'
]
