def get_corrected_daily_consumption(username, company_id, date):
    """
    Calcula consumo di�rio corrigido para um usu�rio
    Evita duplica��o entre snapshots e incrementos
    """
    from datetime import datetime, timedelta
    
    # Converter data para datetime range
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    start_time = datetime.combine(date, datetime.min.time())
    end_time = start_time + timedelta(days=1)
    
    # Buscar todos os registros do usu�rio no dia
    usage_records = UsageData.query.filter(
        UsageData.username == username,
        UsageData.company_id == company_id,
        UsageData.timestamp >= start_time,
        UsageData.timestamp < end_time,
        UsageData.bytes_in >= 0,  # Excluir negativos
        UsageData.bytes_out >= 0
    ).all()
    
    if not usage_records:
        return 0, 0, 0
    
    # Separar snapshots e incrementos
    snapshots = [r for r in usage_records if not r.is_incremental]
    incrementals = [r for r in usage_records if r.is_incremental]
    
    # Calcular bytes_in
    max_snapshot_in = max([s.bytes_in for s in snapshots], default=0)
    sum_incremental_in = sum([i.bytes_in for i in incrementals if i.bytes_in > 0])
    total_bytes_in = max(max_snapshot_in, sum_incremental_in)
    
    # Calcular bytes_out
    max_snapshot_out = max([s.bytes_out for s in snapshots], default=0)
    sum_incremental_out = sum([i.bytes_out for i in incrementals if i.bytes_out > 0])
    total_bytes_out = max(max_snapshot_out, sum_incremental_out)
    
    total_bytes = total_bytes_in + total_bytes_out
    
    return total_bytes_in, total_bytes_out, total_bytes

def get_corrected_monthly_consumption(username, company_id, year, month):
    """Calcula consumo mensal corrigido"""
    from calendar import monthrange
    
    # Calcular todos os dias do m�s
    days_in_month = monthrange(year, month)[1]
    total_in = 0
    total_out = 0
    
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day).date()
        day_in, day_out, _ = get_corrected_daily_consumption(username, company_id, date)
        total_in += day_in
        total_out += day_out
    
    return total_in, total_out, total_in + total_out
