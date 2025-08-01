# ADICIONE ESTA FUN��O AO SEU APP.PY

def get_correct_consumption(username, company_id, date=None):
    """
    Obt�m o consumo correto de um usu�rio em uma data espec�fica
    Usa a view correct_daily_consumption para dados precisos
    
    Args:
        username (str): Nome do usu�rio
        company_id (int): ID da empresa
        date (date, optional): Data espec�fica. Se None, usa a data atual.
        
    Returns:
        tuple: (bytes_in, bytes_out, total_bytes, total_mb)
    """
    from datetime import datetime
    
    if date is None:
        date = get_current_datetime().date()
    
    if isinstance(date, datetime):
        date = date.date()
    
    date_str = date.strftime('%Y-%m-%d')
    
    # Usar SQL direto para acessar a view
    result = db.session.execute(
        """
        SELECT 
            total_bytes_in, 
            total_bytes_out, 
            total_bytes,
            total_mb
        FROM correct_daily_consumption
        WHERE username = :username 
          AND company_id = :company_id
          AND date = :date
        """,
        {
            'username': username,
            'company_id': company_id,
            'date': date_str
        }
    ).fetchone()
    
    if result:
        return result[0], result[1], result[2], result[3]
    else:
        return 0, 0, 0, 0

# EXEMPLO DE USO:
# bytes_in, bytes_out, total_bytes, total_mb = get_correct_consumption('username', company.id)
# print(f"Consumo: {total_mb:.2f} MB")
