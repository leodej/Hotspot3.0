from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, BooleanField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from models import User, Company

# Formulário para adicionar usuário hotspot
class HotspotUserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=4)])
    profile = StringField('Perfil', validators=[DataRequired(), Length(max=100)], default='default')
    comment = TextAreaField('Comentário', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Cadastrar')

# Formulário para login
class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Entrar')

# Formulário para registro de novo admin (usuário do sistema)
class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired()])
    hotspot_username = StringField('Usuário Hotspot', validators=[Optional(), Length(max=80)])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está em uso.')
    
    def validate_confirm_password(self, confirm_password):
        if self.password.data != confirm_password.data:
            raise ValidationError('As senhas não coincidem.')

# Formulário para gerenciar usuários do sistema (administradores e usuários comuns)
class AdminUserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)]) # Senha opcional para edição
    # Adicionado confirm_password para AdminUserForm
    confirm_password = PasswordField('Confirmar Senha', validators=[
        Optional(), # Opcional para edição, mas DataRequired para criação
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    role = SelectField('Função', choices=[('admin', 'Administrador'), ('user', 'Usuário')], validators=[DataRequired()])
    hotspot_username = StringField('Usuário Hotspot', validators=[Optional(), Length(max=80)]) # NEW FIELD
    companies = SelectMultipleField('Acesso às Empresas', 
                                    coerce=int, 
                                    option_widget=CheckboxInput(), 
                                    widget=ListWidget(), 
                                    validators=[Optional()])
    submit = SubmitField('Salvar')

# Formulário para gerenciar empresas
class CompanyForm(FlaskForm):
    name = StringField('Nome da Empresa', validators=[DataRequired(), Length(min=2, max=100)])
    mikrotik_ip = StringField('IP do MikroTik', validators=[DataRequired(), Length(max=15)])
    mikrotik_username = StringField('Usuário MikroTik', validators=[DataRequired(), Length(max=50)])
    mikrotik_password = PasswordField('Senha MikroTik', validators=[DataRequired(), Length(max=100)])
    mikrotik_port = IntegerField('Porta', validators=[Optional(), NumberRange(min=1, max=65535)], default=8728)
    daily_limit_mb = IntegerField('Limite Diário (MB)', validators=[Optional(), NumberRange(min=0)], default=1000)
    daily_time_limit = IntegerField('Limite de Tempo (segundos)', validators=[Optional(), NumberRange(min=0)], default=3600)
    is_active = BooleanField('Ativa', default=True)
    submit = SubmitField('Salvar')

# NEW: Formulário para alteração de senha do usuário final
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired()])
    
    def validate_confirm_password(self, confirm_password):
        if self.new_password.data != confirm_password.data:
            raise ValidationError('As senhas não coincidem.')

class HotspotClassForm(FlaskForm):
    name = StringField('Nome da Turma', validators=[DataRequired(), Length(min=2, max=50)])
    daily_limit_mb = IntegerField('Limite Diário (MB)', validators=[DataRequired(), NumberRange(min=1)], default=1000)
    time_limit_hours = IntegerField('Limite de Tempo (horas)', validators=[DataRequired(), NumberRange(min=1)], default=24)
    speed_limit_up = StringField('Limite Upload', validators=[DataRequired(), Length(max=20)], default='1M')
    speed_limit_down = StringField('Limite Download', validators=[DataRequired(), Length(max=20)], default='1M')
    is_active = BooleanField('Ativa', default=False)
    submit = SubmitField('Salvar')

class CreditForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    data_credit_mb = FloatField('Crédito de Dados (MB)', validators=[Optional(), NumberRange(min=0)], default=0)
    time_credit_seconds = IntegerField('Crédito de Tempo (segundos)', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Adicionar Crédito')

class UserEditForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Função', choices=[('user', 'Usuário'), ('admin', 'Administrador')], validators=[DataRequired()])
    hotspot_username = StringField('Usuário Hotspot', validators=[Optional(), Length(max=80)])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')

class SearchForm(FlaskForm):
    query = StringField('Buscar', validators=[Optional(), Length(max=100)])
    filter_type = SelectField('Filtro', choices=[
        ('all', 'Todos'),
        ('username', 'Usuário'),
        ('email', 'Email'),
        ('company', 'Empresa')
    ], default='all')
    submit = SubmitField('Buscar')

class ReportForm(FlaskForm):
    period = SelectField('Período', choices=[
        ('today', 'Hoje'),
        ('yesterday', 'Ontem'),
        ('week', 'Última Semana'),
        ('month', 'Último Mês'),
        ('custom', 'Personalizado')
    ], default='today')
    username = StringField('Usuário Específico', validators=[Optional(), Length(max=80)])
    export_format = SelectField('Formato de Exportação', choices=[
        ('html', 'HTML'),
        ('json', 'JSON'),
        ('csv', 'CSV')
    ], default='html')
    submit = SubmitField('Gerar Relatório')
