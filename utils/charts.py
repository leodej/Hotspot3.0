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

import io
import base64
from datetime import datetime, timedelta

def generate_chart(data, title, xlabel, ylabel, chart_type='bar'):
    """Gera gráfico básico"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        plt.figure(figsize=(10, 6))
        
        if isinstance(data, dict):
            x_values = list(data.keys())
            y_values = list(data.values())
        else:
            x_values = range(len(data))
            y_values = data
        
        if chart_type == 'bar':
            plt.bar(x_values, y_values)
        elif chart_type == 'line':
            plt.plot(x_values, y_values, marker='o')
        elif chart_type == 'pie':
            plt.pie(y_values, labels=x_values, autopct='%1.1f%%')
            plt.axis('equal')
        
        plt.title(title)
        if chart_type != 'pie':
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        return None

def generate_usage_chart(usage_records, username):
    """Gera gráfico de uso específico"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        # Agrupar dados por dia
        daily_data = {}
        for record in usage_records:
            date_key = record.timestamp.date()
            if date_key not in daily_data:
                daily_data[date_key] = 0
            daily_data[date_key] += (record.bytes_in + record.bytes_out) / (1024 * 1024)  # MB
        
        # Ordenar por data
        sorted_dates = sorted(daily_data.keys())
        dates = [date.strftime('%d/%m') for date in sorted_dates]
        usage_mb = [daily_data[date] for date in sorted_dates]
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, usage_mb, marker='o', linewidth=2, markersize=6)
        plt.title(f'Consumo Diário - {username}')
        plt.xlabel('Data')
        plt.ylabel('Consumo (MB)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar gráfico de uso: {e}")
        return None

def generate_comparison_chart(data1, data2, labels, title):
    """Gera gráfico de comparação"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        x = np.arange(len(labels))
        width = 0.35
        
        plt.figure(figsize=(10, 6))
        plt.bar(x - width/2, data1, width, label='Série 1')
        plt.bar(x + width/2, data2, width, label='Série 2')
        
        plt.title(title)
        plt.xlabel('Categorias')
        plt.ylabel('Valores')
        plt.xticks(x, labels, rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar gráfico de comparação: {e}")
        return None

def generate_pie_chart(data, title):
    """Gera gráfico de pizza"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        if isinstance(data, dict):
            labels = list(data.keys())
            sizes = list(data.values())
        else:
            labels = [f"Item {i+1}" for i in range(len(data))]
            sizes = data
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title(title)
        plt.axis('equal')
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar gráfico de pizza: {e}")
        return None

def generate_time_series_chart(timestamps, values, title, ylabel):
    """Gera gráfico de série temporal"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, values, marker='o', linewidth=2)
        plt.title(title)
        plt.xlabel('Tempo')
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar gráfico de série temporal: {e}")
        return None

def generate_heatmap(data, title, xlabel, ylabel):
    """Gera mapa de calor"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib não disponível. Gráficos desabilitados.")
        return None
        
    try:
        plt.figure(figsize=(10, 8))
        plt.imshow(data, cmap='YlOrRd', aspect='auto')
        plt.colorbar()
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.tight_layout()
        
        # Converter para base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao gerar mapa de calor: {e}")
        return None

def generate_simple_chart_html(data, title, chart_type='bar'):
    """Gera gráfico simples em HTML/CSS quando matplotlib não está disponível"""
    if isinstance(data, dict):
        labels = list(data.keys())
        values = list(data.values())
    else:
        labels = [f"Item {i+1}" for i in range(len(data))]
        values = data
    
    if not values:
        return f"<div class='chart-placeholder'>Sem dados para exibir em {title}</div>"
    
    max_value = max(values) if values else 1
    
    html = f"""
    <div class="simple-chart">
        <h3>{title}</h3>
        <div class="chart-bars">
    """
    
    for i, (label, value) in enumerate(zip(labels, values)):
        height = (value / max_value) * 100 if max_value > 0 else 0
        html += f"""
            <div class="chart-bar">
                <div class="bar" style="height: {height}%"></div>
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
        """
    
    html += """
        </div>
    </div>
    <style>
    .simple-chart {
        margin: 20px 0;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .chart-bars {
        display: flex;
        align-items: flex-end;
        height: 200px;
        gap: 10px;
    }
    .chart-bar {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
    }
    .bar {
        background: #007bff;
        width: 30px;
        min-height: 5px;
        margin-bottom: 5px;
    }
    .label {
        font-size: 12px;
        text-align: center;
        margin-top: 5px;
    }
    .value {
        font-size: 11px;
        color: #666;
    }
    .chart-placeholder {
        padding: 40px;
        text-align: center;
        color: #666;
        border: 2px dashed #ddd;
        border-radius: 5px;
    }
    </style>
    """
    
    return html
