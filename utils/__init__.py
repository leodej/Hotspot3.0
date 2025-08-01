"""
Utilitários do sistema
"""

try:
    from .charts import generate_chart
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    def generate_chart(*args, **kwargs):
        return None

from .helpers import (
    check_system_date,
    initialize_default_data,
    get_selected_company,
    format_bytes,
    calculate_percentage,
    get_system_info,
    validate_ip_address,
    generate_random_password,
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
    rate_limit,
    cache_result,
    log_action,
    validate_json,
    handle_errors,
    require_permissions,
    audit_trail
)

__all__ = [
    'generate_chart',
    'CHARTS_AVAILABLE',
    'check_system_date',
    'initialize_default_data',
    'get_selected_company',
    'format_bytes',
    'calculate_percentage',
    'get_system_info',
    'validate_ip_address',
    'generate_random_password',
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
    'rate_limit',
    'cache_result',
    'log_action',
    'validate_json',
    'handle_errors',
    'require_permissions',
    'audit_trail'
]
