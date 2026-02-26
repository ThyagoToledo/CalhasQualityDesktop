"""
CalhaGest - Analytics com Gráficos
Gráficos de lucro, gastos e métricas financeiras usando Matplotlib.
Estilo visual moderno com cores e tipografia aprimoradas.
"""

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo para gerar imagens
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io
import base64
from typing import List, Dict
import os


# Estilo global para todos os gráficos
CHART_STYLE = {
    "bg_color": "#fafbfc",
    "grid_color": "#e2e8f0",
    "text_color": "#1e293b",
    "label_color": "#64748b",
    "primary": "#2563eb",
    "primary_light": "#93c5fd",
    "success": "#10b981",
    "success_light": "#6ee7b7",
    "error": "#ef4444",
    "error_light": "#fca5a5",
    "warning": "#f59e0b",
    "purple": "#8b5cf6",
}


def _apply_chart_style(ax, fig):
    """Aplica estilo consistente e moderno a todos os gráficos."""
    fig.set_facecolor(CHART_STYLE["bg_color"])
    ax.set_facecolor(CHART_STYLE["bg_color"])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(CHART_STYLE["grid_color"])
    ax.spines['bottom'].set_color(CHART_STYLE["grid_color"])
    ax.tick_params(colors=CHART_STYLE["label_color"], labelsize=9)
    ax.grid(axis='y', color=CHART_STYLE["grid_color"], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


def create_profit_vs_cost_chart(analytics_data: List[Dict], output_path: str = None) -> str:
    """
    Cria gráfico de barras comparando faturamento e custos mensais.
    
    Args:
        analytics_data: Lista de dicionários com dados mensais
        output_path: Caminho para salvar a imagem (opcional)
    
    Returns:
        Caminho da imagem ou base64 da imagem
    """
    if not analytics_data:
        return None
    
    # Preparar dados
    months = [d['month'] for d in analytics_data]
    revenue = [d['revenue'] for d in analytics_data]
    cost = [d['cost'] for d in analytics_data]
    
    # Inverter para ordem cronológica
    months = months[::-1]
    revenue = revenue[::-1]
    cost = cost[::-1]
    
    # Criar figura com estilo moderno
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_chart_style(ax, fig)
    
    x = range(len(months))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], revenue, width, label='Faturamento', 
                   color=CHART_STYLE["primary"], alpha=0.85, edgecolor='white', linewidth=0.5)
    bars2 = ax.bar([i + width/2 for i in x], cost, width, label='Custo', 
                   color=CHART_STYLE["error"], alpha=0.85, edgecolor='white', linewidth=0.5)
    
    ax.set_xlabel('Mês', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_ylabel('Valor (R$)', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_title('Faturamento vs Custo por Mês', fontsize=15, fontweight='bold',
                 color=CHART_STYLE["text_color"], pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.legend(frameon=True, fancybox=True, shadow=False, edgecolor=CHART_STYLE["grid_color"],
              fontsize=10, loc='upper left')
    
    # Adicionar valores nas barras
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'R${height:,.0f}'.replace(',', '.'),
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=7)
    
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'R${height:,.0f}'.replace(',', '.'),
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=7)
    
    plt.tight_layout()
    
    # Salvar ou retornar
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.close()
        return output_path
    else:
        # Retornar base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')


def create_profit_evolution_chart(analytics_data: List[Dict], output_path: str = None) -> str:
    """
    Cria gráfico de linhas mostrando evolução do lucro ao longo do tempo.
    
    Args:
        analytics_data: Lista de dicionários com dados mensais
        output_path: Caminho para salvar a imagem (opcional)
    
    Returns:
        Caminho da imagem ou base64 da imagem
    """
    if not analytics_data:
        return None
    
    # Preparar dados
    months = [d['month'] for d in analytics_data]
    profit = [d['profit'] for d in analytics_data]
    revenue = [d['revenue'] for d in analytics_data]
    
    # Inverter para ordem cronológica
    months = months[::-1]
    profit = profit[::-1]
    revenue = revenue[::-1]
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_chart_style(ax, fig)
    
    ax.plot(months, revenue, marker='o', linewidth=2.5, markersize=8, 
            color=CHART_STYLE["primary"], label='Faturamento', markerfacecolor='white',
            markeredgewidth=2, markeredgecolor=CHART_STYLE["primary"])
    ax.plot(months, profit, marker='s', linewidth=2.5, markersize=8, 
            color=CHART_STYLE["success"], label='Lucro', markerfacecolor='white',
            markeredgewidth=2, markeredgecolor=CHART_STYLE["success"])
    
    # Preencher área do lucro
    ax.fill_between(months, profit, alpha=0.15, color=CHART_STYLE["success"])
    ax.fill_between(months, revenue, alpha=0.08, color=CHART_STYLE["primary"])
    
    ax.set_xlabel('Mês', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_ylabel('Valor (R$)', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_title('Evolução Financeira Mensal', fontsize=15, fontweight='bold',
                 color=CHART_STYLE["text_color"], pad=20)
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=False,
              edgecolor=CHART_STYLE["grid_color"], fontsize=10)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Salvar ou retornar
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        return output_path
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')


def create_pie_chart(labels: List[str], values: List[float], title: str = "Distribuição",
                     output_path: str = None) -> str:
    """
    Cria gráfico de pizza.
    
    Args:
        labels: Rótulos das fatias
        values: Valores correspondentes
        title: Título do gráfico
        output_path: Caminho para salvar a imagem (opcional)
    
    Returns:
        Caminho da imagem ou base64 da imagem
    """
    # Filtrar valores zerados
    filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not filtered_data:
        return None
    
    labels, values = zip(*filtered_data)
    
    # Cores personalizadas
    colors = [CHART_STYLE["primary"], CHART_STYLE["success"], CHART_STYLE["warning"],
              CHART_STYLE["error"], CHART_STYLE["purple"], 
              '#ec4899', '#06b6d4', '#84cc16']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.set_facecolor(CHART_STYLE["bg_color"])
    
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                       colors=colors[:len(values)], startangle=90,
                                       explode=[0.03] * len(values),
                                       shadow=False, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    
    ax.set_title(title, fontsize=15, fontweight='bold', color=CHART_STYLE["text_color"], pad=20)
    
    # Melhorar legibilidade
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
    
    plt.tight_layout()
    
    # Salvar ou retornar
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        return output_path
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')


def create_quotes_by_status_chart(quotes_data: Dict[str, int], output_path: str = None) -> str:
    """
    Cria gráfico de orçamentos por status.
    
    Args:
        quotes_data: Dicionário com contagem de orçamentos por status
        output_path: Caminho para salvar a imagem (opcional)
    
    Returns:
        Caminho da imagem ou base64 da imagem
    """
    status_labels = {
        'draft': 'Rascunho',
        'sent': 'Enviado',
        'approved': 'Aprovado',
        'completed': 'Concluído',
    }
    
    status_colors = {
        'draft': '#9ca3af',
        'sent': '#3b82f6',
        'approved': '#22c55e',
        'completed': '#a855f7',
    }
    
    labels = [status_labels.get(k, k) for k in quotes_data.keys()]
    values = list(quotes_data.values())
    colors = [status_colors.get(k, '#6b7280') for k in quotes_data.keys()]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    _apply_chart_style(ax, fig)
    
    bars = ax.bar(labels, values, color=colors, alpha=0.85, edgecolor='white', linewidth=0.5,
                  width=0.6)
    
    ax.set_xlabel('Status', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_ylabel('Quantidade', fontsize=10, color=CHART_STYLE["label_color"], fontweight='medium')
    ax.set_title('Orçamentos por Status', fontsize=15, fontweight='bold',
                 color=CHART_STYLE["text_color"], pad=20)
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    # Salvar ou retornar
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close()
        return output_path
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')


def save_all_charts(analytics_data: List[Dict], quotes_by_status: Dict[str, int],
                    output_dir: str) -> Dict[str, str]:
    """
    Gera e salva todos os gráficos em um diretório.
    
    Args:
        analytics_data: Dados de análise mensal
        quotes_by_status: Contagem de orçamentos por status
        output_dir: Diretório de saída
    
    Returns:
        Dicionário com caminhos dos gráficos gerados
    """
    os.makedirs(output_dir, exist_ok=True)
    
    charts = {}
    
    if analytics_data:
        charts['profit_vs_cost'] = create_profit_vs_cost_chart(
            analytics_data, 
            os.path.join(output_dir, 'profit_vs_cost.png')
        )
        
        charts['profit_evolution'] = create_profit_evolution_chart(
            analytics_data,
            os.path.join(output_dir, 'profit_evolution.png')
        )
    
    if quotes_by_status:
        charts['quotes_by_status'] = create_quotes_by_status_chart(
            quotes_by_status,
            os.path.join(output_dir, 'quotes_by_status.png')
        )
    
    return charts
