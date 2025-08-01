"""
Módulo para geração de gráficos e visualizações
"""

import io
import base64
from datetime import datetime, timedelta

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    np = None

def generate_chart(data, chart_type='line', title='Gráfico', xlabel='X', ylabel='Y', width=10, height=6):
    """
    Gera um gráfico usando matplotlib ou fallback para HTML/CSS
    
    Args:
        data: Dados para o gráfico (lista de tuplas ou dicionário)
        chart_type: Tipo do gráfico ('line', 'bar', 'pie')
        title: Título do gráfico
        xlabel: Label do eixo X
        ylabel: Label do eixo Y
        width: Largura do gráfico
        height: Altura do gráfico
    
    Returns:
        String com HTML do gráfico (base64 se matplotlib disponível, CSS caso contrário)
    """
    
    if not MATPLOTLIB_AVAILABLE:
        return generate_simple_chart_html(data, chart_type, title)
    
    try:
        # Configurar matplotlib
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Processar dados
        if isinstance(data, dict):
            x_data = list(data.keys())
            y_data = list(data.values())
        elif isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], tuple):
                x_data = [item[0] for item in data]
                y_data = [item[1] for item in data]
            else:
                x_data = list(range(len(data)))
                y_data = data
        else:
            return "<div class='alert alert-warning'>Dados inválidos para o gráfico</div>"
        
        # Gerar gráfico baseado no tipo
        if chart_type == 'line':
            ax.plot(x_data, y_data, marker='o', linewidth=2, markersize=6)
            ax.grid(True, alpha=0.3)
            
        elif chart_type == 'bar':
            bars = ax.bar(x_data, y_data, alpha=0.8, color='#007bff')
            # Adicionar valores nas barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
                       
        elif chart_type == 'pie':
            wedges, texts, autotexts = ax.pie(y_data, labels=x_data, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            
        else:
            return f"<div class='alert alert-error'>Tipo de gráfico '{chart_type}' não suportado</div>"
        
        # Configurar título e labels
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        if chart_type != 'pie':
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
        
        # Melhorar aparência
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close(fig)
        
        return f'<img src="data:image/png;base64,{img_base64}" class="img-fluid" alt="{title}">'
        
    except Exception as e:
        return f"<div class='alert alert-error'>Erro ao gerar gráfico: {str(e)}</div>"

def generate_simple_chart_html(data, chart_type, title):
    """
    Gera um gráfico simples usando HTML/CSS quando matplotlib não está disponível
    """
    
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], tuple):
            items = data
        else:
            items = [(f"Item {i+1}", val) for i, val in enumerate(data)]
    else:
        return "<div class='alert alert-warning'>Dados inválidos para o gráfico</div>"
    
    if not items:
        return "<div class='alert alert-info'>Nenhum dado disponível para o gráfico</div>"
    
    max_value = max([item[1] for item in items]) if items else 1
    
    html = f"""
    <div class="simple-chart">
        <h4 class="chart-title">{title}</h4>
        <div class="chart-container">
    """
    
    if chart_type == 'bar':
        for label, value in items:
            percentage = (value / max_value) * 100 if max_value > 0 else 0
            html += f"""
            <div class="chart-bar-item">
                <div class="chart-label">{label}</div>
                <div class="chart-bar-container">
                    <div class="chart-bar" style="width: {percentage}%"></div>
                    <span class="chart-value">{value}</span>
                </div>
            </div>
            """
    
    elif chart_type == 'pie':
        total = sum([item[1] for item in items])
        html += '<div class="pie-chart-legend">'
        for i, (label, value) in enumerate(items):
            percentage = (value / total) * 100 if total > 0 else 0
            color = f"hsl({i * 360 / len(items)}, 70%, 50%)"
            html += f"""
            <div class="pie-item">
                <div class="pie-color" style="background-color: {color}"></div>
                <span>{label}: {value} ({percentage:.1f}%)</span>
            </div>
            """
        html += '</div>'
    
    else:  # line chart fallback to bar
        for label, value in items:
            percentage = (value / max_value) * 100 if max_value > 0 else 0
            html += f"""
            <div class="chart-line-item">
                <span class="chart-label">{label}</span>
                <span class="chart-value">{value}</span>
            </div>
            """
    
    html += """
        </div>
    </div>
    <style>
    .simple-chart {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    }
    .chart-title {
        text-align: center;
        margin-bottom: 20px;
        color: #333;
    }
    .chart-bar-item {
        margin-bottom: 10px;
    }
    .chart-label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .chart-bar-container {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .chart-bar {
        height: 25px;
        background: linear-gradient(90deg, #007bff, #0056b3);
        border-radius: 3px;
        min-width: 2px;
    }
    .chart-value {
        font-weight: bold;
        color: #333;
    }
    .pie-chart-legend {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .pie-item {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pie-color {
        width: 20px;
        height: 20px;
        border-radius: 50%;
    }
    .chart-line-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    </style>
    """
    
    return html

def generate_usage_chart(usage_data, period='daily'):
    """
    Gera gráfico específico para dados de uso
    """
    if not usage_data:
        return "<div class='alert alert-info'>Nenhum dado de uso disponível</div>"
    
    # Processar dados de uso
    chart_data = {}
    for record in usage_data:
        date_key = record.get('date', 'N/A')
        usage_mb = record.get('usage_bytes', 0) / (1024 * 1024)  # Convert to MB
        chart_data[date_key] = usage_mb
    
    title = f"Uso de Dados - {period.title()}"
    return generate_chart(chart_data, 'line', title, 'Data', 'Uso (MB)')

def generate_user_stats_chart(user_stats):
    """
    Gera gráfico de estatísticas de usuários
    """
    if not user_stats:
        return "<div class='alert alert-info'>Nenhuma estatística de usuário disponível</div>"
    
    return generate_chart(user_stats, 'bar', 'Estatísticas de Usuários', 'Categoria', 'Quantidade')

def generate_company_comparison_chart(company_data):
    """
    Gera gráfico de comparação entre empresas
    """
    if not company_data:
        return "<div class='alert alert-info'>Nenhum dado de empresa disponível</div>"
    
    return generate_chart(company_data, 'pie', 'Distribuição por Empresa')
