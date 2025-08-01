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
    restore_database,
    format_time,
    format_speed,
    get_date_range,
    is_limit_exceeded,
    get_usage_color,
    sanitize_filename,
    generate_random_password,
    validate_ip_address,
    validate_email,
    get_client_ip,
    log_user_action,
    hash_password,
    verify_password,
    format_datetime,
    get_current_timestamp,
    safe_int,
    safe_float,
    truncate_string,
    clean_string,
    is_valid_email,
    get_file_size,
    create_backup,
    restore_backup,
    export_to_csv,
    import_from_csv
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
    'format_time',
    'format_speed',
    'get_date_range',
    'is_limit_exceeded',
    'get_usage_color',
    'sanitize_filename',
    'generate_random_password',
    'validate_ip_address',
    'validate_email',
    'get_client_ip',
    'log_user_action',
    'hash_password',
    'verify_password',
    'format_datetime',
    'get_current_timestamp',
    'safe_int',
    'safe_float',
    'truncate_string',
    'clean_string',
    'is_valid_email',
    'get_file_size',
    'create_backup',
    'restore_backup',
    'export_to_csv',
    'import_from_csv',
    'login_required',
    'admin_required',
    'company_required',
    'rate_limit'
]
