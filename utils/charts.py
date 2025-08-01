import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import numpy as np

def generate_chart(data, title, xlabel, ylabel, chart_type='bar'):
    """Gera gráfico básico"""
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
