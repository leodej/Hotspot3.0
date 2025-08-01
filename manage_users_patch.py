# SUBSTITUA A ROTA /users/manage NO SEU APP.PY

@app.route('/users/manage')
@login_required
def manage_users():
    company = get_selected_company()
    if not company:
        return redirect(url_for('companies'))

    connection, api = connect_to_mikrotik(company)
    if not api:
        flash('N�o foi poss�vel conectar ao MikroTik. Verifique as configura��es.', 'danger')
        return render_template('manage_users.html', users=[], company=company, error="Falha na conex�o com o MikroTik")

    try:
        # Obter usu�rios do MikroTik
        hotspot_users = api.get_resource('/ip/hotspot/user')
        users = hotspot_users.get()
        
        # Obter turma ativa
        active_class = Class.query.filter_by(company_id=company.id, is_active=True).first()
        
        # Processar usu�rios
        for user in users:
            username = user.get('name', '')
            
            # Obter perfil do usu�rio
            user_profile = UserProfile.query.filter_by(
                username=username, 
                company_id=company.id
            ).first()
            
            if user_profile:
                user['user_profile'] = user_profile
            
            # USAR A FUN��O CORRIGIDA PARA CALCULAR CONSUMO
            today = get_current_datetime().date()
            bytes_in, bytes_out, total_bytes, total_mb = get_correct_consumption(username, company.id, today)
            
            # Adicionar dados de consumo ao usu�rio
            user['daily_usage_mb'] = round(total_mb, 2)
            
            # Obter cr�dito dispon�vel
            user_credit = UserCredit.query.filter_by(
                username=username,
                company_id=company.id,
                date=today
            ).first()
            
            if user_credit:
                user['accumulated_credit_mb'] = user_credit.accumulated_credit_mb
                user['available_credit_mb'] = user_credit.total_available_mb
            else:
                user['accumulated_credit_mb'] = 0
                user['available_credit_mb'] = company.daily_limit_mb
            
            # Verificar se est� pr�ximo ao limite ou j� atingiu
            limit_percentage = (total_mb / user['available_credit_mb']) * 100 if user['available_credit_mb'] > 0 else 0
            user['approaching_limit'] = limit_percentage >= 80 and limit_percentage < 100
            user['limit_reached'] = limit_percentage >= 100
        
        connection.disconnect()
        return render_template('manage_users.html', users=users, company=company)
        
    except Exception as e:
        if connection:
            connection.disconnect()
        error_msg = f"Erro ao obter usu�rios: {str(e)}"
        log_with_context('error', error_msg, task="manage_users", company_id=company.id, error=str(e))
        return render_template('manage_users.html', users=[], company=company, error=error_msg)
