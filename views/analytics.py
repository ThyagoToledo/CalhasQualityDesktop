# -*- coding: utf-8 -*-
"""
CalhaGest - Relatórios e Analytics
Gráficos financeiros com abas de seleção e visuais melhorados.
"""

import customtkinter as ctk
import os
import tempfile
from database import db
from components.cards import create_header
from theme import get_color, COLORS
from components.dialogs import format_currency


class AnalyticsView(ctk.CTkFrame):
    """View de relatórios com abas para cada tipo de gráfico."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._chart_images = []
        self._temp_dir = tempfile.mkdtemp()
        self._build()

    def _build(self):
        # Cabeçalho
        header = create_header(self, "Relatórios", "Análise financeira e métricas")
        header.pack(fill="x", pady=(0, 15))

        # Estatísticas resumidas
        stats = db.get_dashboard_stats()

        # Cards resumo
        summary = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                border_width=1, border_color=COLORS["border"])
        summary.pack(fill="x", pady=(0, 15))

        stats_grid = ctk.CTkFrame(summary, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=15)
        stats_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stat_items = [
            ("📋 Orçamentos", str(stats.get("total_quotes", 0)), COLORS["primary"]),
            ("✅ Aprovados", str(stats.get("approved_quotes", 0)), COLORS["success"]),
            ("💰 Faturamento", format_currency(stats.get("total_revenue", 0)), COLORS["warning"]),
            ("📈 Lucro", format_currency(stats.get("total_profit", 0)), COLORS["success"]),
        ]

        for col, (label, value, color) in enumerate(stat_items):
            cell = ctk.CTkFrame(stats_grid, fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, sticky="nsew")

            # Barra de cor no topo
            ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack()
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=color).pack(pady=(2, 0))

        # Cards de pagamentos (segunda linha)
        pay_grid = ctk.CTkFrame(summary, fg_color="transparent")
        pay_grid.pack(fill="x", padx=15, pady=(0, 15))
        pay_grid.grid_columnconfigure((0, 1, 2), weight=1)

        pay_items = [
            ("💵 Recebido", format_currency(stats.get("total_received", 0)), COLORS["success"]),
            ("📛 Saldo Devedor", format_currency(stats.get("total_pending", 0)), COLORS["error"]),
            ("🏷️ Quitados", str(stats.get("paid_quotes", 0)), COLORS["primary"]),
        ]

        for col, (label, value, color) in enumerate(pay_items):
            cell = ctk.CTkFrame(pay_grid, fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, sticky="nsew")

            ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack()
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=color).pack(pady=(2, 0))

        # Cards financeiros (terceira linha)
        try:
            fin = db.get_financial_overview()
            fin_grid = ctk.CTkFrame(summary, fg_color="transparent")
            fin_grid.pack(fill="x", padx=15, pady=(0, 15))
            fin_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

            fin_items = [
                ("💸 Despesas", format_currency(fin.get("total_expenses", 0)), COLORS["error"]),
                ("👥 Folha Pgto", format_currency(fin.get("total_payroll", 0)), COLORS["warning"]),
                ("📊 Balanço", format_currency(fin.get("balance", 0)),
                 COLORS["success"] if fin.get("balance", 0) >= 0 else COLORS["error"]),
                ("📛 Pendentes", format_currency(fin.get("pending_receivables", 0)), COLORS["primary"]),
            ]
            for col, (label, value, color) in enumerate(fin_items):
                cell = ctk.CTkFrame(fin_grid, fg_color="transparent")
                cell.grid(row=0, column=col, padx=8, sticky="nsew")
                ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))
                ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                             text_color=COLORS["text_secondary"]).pack()
                ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=color).pack(pady=(2, 0))
        except Exception:
            pass

        # Filtro de período
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            filter_frame, text="Período:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(0, 8))

        self.period_var = ctk.StringVar(value="Mensal")
        ctk.CTkSegmentedButton(
            filter_frame,
            values=["Diário", "Semanal", "Mensal", "Anual"],
            variable=self.period_var,
            command=self._on_period_change,
            font=ctk.CTkFont(size=11),
            height=32,
        ).pack(side="left")

        # Tabview com abas de gráficos
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            segmented_button_fg_color=get_color("border"),
            segmented_button_selected_color=get_color("primary"),
            segmented_button_selected_hover_color=get_color("primary_hover"),
            segmented_button_unselected_color=get_color("border"),
            segmented_button_unselected_hover_color=get_color("border_hover"),
            text_color=COLORS["text"],
            text_color_disabled=COLORS["text_secondary"],
        )
        self.tabview.pack(fill="both", expand=True)
        
        # Override tab button text colors
        self.tabview._segmented_button.configure(
            text_color=COLORS["text"],
            text_color_disabled=COLORS["text_secondary"]
        )

        # Criar abas
        tab_revenue = self.tabview.add("💰 Faturamento vs Custo")
        tab_evolution = self.tabview.add("📈 Evolução Financeira")
        tab_status = self.tabview.add("📋 Orçamentos por Status")
        tab_financial = self.tabview.add("🥧 Visão Financeira")
        tab_payments = self.tabview.add("💵 Pagamentos")
        tab_overview = self.tabview.add("📊 Visão Geral")

        # Carregar dados
        analytics = db.get_monthly_analytics()
        quotes_by_status = self._get_quotes_by_status()

        # Preencher abas
        if analytics:
            self._fill_revenue_tab(tab_revenue, analytics)
            self._fill_evolution_tab(tab_evolution, analytics)
        else:
            self._show_no_data(tab_revenue)
            self._show_no_data(tab_evolution)

        if quotes_by_status:
            self._fill_status_tab(tab_status, quotes_by_status)
        else:
            self._show_no_data(tab_status)

        self._fill_financial_tab(tab_financial)
        self._fill_payments_tab(tab_payments, stats)
        self._fill_overview_tab(tab_overview, analytics, quotes_by_status, stats)

    def _on_period_change(self, value):
        """Atualiza os gráficos quando o período muda."""
        from datetime import datetime, timedelta
        
        # Calcular intervalo de datas baseado no período
        today = datetime.now()
        
        if value == "Diário":
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            date_format = "%Y-%m-%d"
            months_back = 0
        elif value == "Semanal":
            start_date = today - timedelta(days=7)
            date_format = "%Y-%m"
            months_back = 0
        elif value == "Mensal":
            start_date = today - timedelta(days=30)
            date_format = "%Y-%m"
            months_back = 0
        else:  # Anual
            start_date = today - timedelta(days=365)
            date_format = "%Y-%m"
            months_back = 12
        
        # Recarregar dados
        analytics = db.get_monthly_analytics()
        quotes_by_status = self._get_quotes_by_status()
        
        # Filtrar analytics por período
        if value != "Mensal":  # Mensal já carrega últimos 12 meses por padrão
            filtered_analytics = []
            for item in analytics:
                try:
                    item_date = datetime.strptime(item["month"], "%Y-%m")
                    if item_date >= start_date:
                        filtered_analytics.append(item)
                except:
                    continue
            analytics = filtered_analytics
        
        # Limpar e reconstruir abas
        self._rebuild_tabs(analytics, quotes_by_status)
        self.app.show_toast(f"📊 Relatório atualizado: {value}", "success")

    def _rebuild_tabs(self, analytics, quotes_by_status):
        """Reconstrói todas as abas com novos dados."""
        stats = db.get_dashboard_stats()

        # Remover todas as abas existentes
        for tab_name in ["💰 Faturamento vs Custo", "📈 Evolução Financeira", 
                         "📋 Orçamentos por Status", "🥧 Visão Financeira",
                         "💵 Pagamentos", "📊 Visão Geral"]:
            try:
                self.tabview.delete(tab_name)
            except:
                pass
        
        # Recriar abas
        tab_revenue = self.tabview.add("💰 Faturamento vs Custo")
        tab_evolution = self.tabview.add("📈 Evolução Financeira")
        tab_status = self.tabview.add("📋 Orçamentos por Status")
        tab_financial = self.tabview.add("🥧 Visão Financeira")
        tab_payments = self.tabview.add("💵 Pagamentos")
        tab_overview = self.tabview.add("📊 Visão Geral")
        
        # Preencher com novos dados
        if analytics:
            self._fill_revenue_tab(tab_revenue, analytics)
            self._fill_evolution_tab(tab_evolution, analytics)
        else:
            self._show_no_data(tab_revenue)
            self._show_no_data(tab_evolution)
        
        if quotes_by_status:
            self._fill_status_tab(tab_status, quotes_by_status)
        else:
            self._show_no_data(tab_status)
        
        self._fill_financial_tab(tab_financial)
        self._fill_payments_tab(tab_payments, stats)
        self._fill_overview_tab(tab_overview, analytics, quotes_by_status, stats)

    def _show_no_data(self, parent):
        """Mostra mensagem de dados insuficientes."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)
        ctk.CTkLabel(
            wrapper,
            text="📈 Dados insuficientes para este gráfico.\nCrie alguns orçamentos para ver os relatórios.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
            justify="center",
        ).pack(expand=True)

    def _fill_revenue_tab(self, parent, analytics_data):
        """Aba de Faturamento vs Custo."""
        try:
            from analytics.charts import create_profit_vs_cost_chart

            scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            # Descrição
            ctk.CTkLabel(
                scroll,
                text="Comparação mensal entre faturamento e custos",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=10, pady=(10, 8))

            path = os.path.join(self._temp_dir, "profit_vs_cost.png")
            create_profit_vs_cost_chart(analytics_data, path)
            if os.path.exists(path):
                self._display_chart_image(scroll, path)

            # Tabela de dados
            self._add_data_table(scroll, analytics_data, ["month", "revenue", "cost", "profit"],
                                 ["Mês", "Faturamento", "Custo", "Lucro"])
        except Exception as e:
            ctk.CTkLabel(parent, text=f"Erro: {e}", text_color=COLORS["error"]).pack(pady=10)

    def _fill_evolution_tab(self, parent, analytics_data):
        """Aba de Evolução Financeira."""
        try:
            from analytics.charts import create_profit_evolution_chart

            scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            ctk.CTkLabel(
                scroll,
                text="Evolução do faturamento e lucro ao longo dos meses",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=10, pady=(10, 8))

            path = os.path.join(self._temp_dir, "profit_evolution.png")
            create_profit_evolution_chart(analytics_data, path)
            if os.path.exists(path):
                self._display_chart_image(scroll, path)

        except Exception as e:
            ctk.CTkLabel(parent, text=f"Erro: {e}", text_color=COLORS["error"]).pack(pady=10)

    def _fill_status_tab(self, parent, quotes_data):
        """Aba de Orçamentos por Status."""
        try:
            from analytics.charts import create_quotes_by_status_chart

            scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            ctk.CTkLabel(
                scroll,
                text="Distribuição dos orçamentos por status atual",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=10, pady=(10, 8))

            path = os.path.join(self._temp_dir, "quotes_status.png")
            create_quotes_by_status_chart(quotes_data, path)
            if os.path.exists(path):
                self._display_chart_image(scroll, path)

            # Status cards
            status_labels = {
                'draft': ('Rascunho', '#9ca3af'),
                'sent': ('Enviado', '#3b82f6'),
                'approved': ('Aprovado', '#22c55e'),
                'completed': ('Concluído', '#a855f7'),
            }

            cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            cards_frame.pack(fill="x", padx=10, pady=(15, 10))
            cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            for col, (key, count) in enumerate(quotes_data.items()):
                label, color = status_labels.get(key, (key, "#6b7280"))
                cell = ctk.CTkFrame(cards_frame, fg_color=COLORS["card"], corner_radius=10,
                                     border_width=1, border_color=COLORS["border"])
                cell.grid(row=0, column=col, padx=4, sticky="nsew")

                ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", padx=8, pady=(8, 4))
                ctk.CTkLabel(cell, text=str(count), font=ctk.CTkFont(size=22, weight="bold"),
                             text_color=color).pack(pady=(4, 0))
                ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                             text_color=COLORS["text_secondary"]).pack(pady=(0, 8))

        except Exception as e:
            ctk.CTkLabel(parent, text=f"Erro: {e}", text_color=COLORS["error"]).pack(pady=10)

    def _fill_financial_tab(self, parent):
        """Aba de visão financeira com painel de seleção de gráficos."""
        try:
            from analytics.charts import create_pie_chart

            scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            overview = db.get_financial_overview()

            # Cards resumo financeiro
            summary_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                          border_width=1, border_color=COLORS["border"])
            summary_frame.pack(fill="x", padx=10, pady=(10, 15))

            sgrid = ctk.CTkFrame(summary_frame, fg_color="transparent")
            sgrid.pack(fill="x", padx=15, pady=15)
            sgrid.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            fin_stats = [
                ("💵 Recebido", format_currency(overview.get("total_income", 0)), COLORS["success"]),
                ("💸 Despesas", format_currency(overview.get("total_expenses", 0)), COLORS["error"]),
                ("👥 Folha", format_currency(overview.get("total_payroll", 0)), COLORS["warning"]),
                ("📊 Balanço", format_currency(overview.get("balance", 0)),
                 COLORS["success"] if overview.get("balance", 0) >= 0 else COLORS["error"]),
                ("📛 Pendentes", format_currency(overview.get("pending_receivables", 0)), COLORS["primary"]),
            ]
            for col, (label, value, color) in enumerate(fin_stats):
                cell = ctk.CTkFrame(sgrid, fg_color="transparent")
                cell.grid(row=0, column=col, padx=6, sticky="nsew")
                ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 6))
                ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=10),
                             text_color=COLORS["text_secondary"]).pack()
                ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=15, weight="bold"),
                             text_color=color).pack(pady=(2, 0))

            # Painel de seleção de gráficos
            ctk.CTkLabel(
                scroll, text="📊 Galeria de Gráficos",
                font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
            ).pack(anchor="w", padx=10, pady=(20, 10))

            ctk.CTkLabel(
                scroll, text="Clique em um card para visualizar o gráfico em tela cheia",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=10, pady=(0, 15))

            # Grid de cards de gráficos
            charts_grid = ctk.CTkFrame(scroll, fg_color="transparent")
            charts_grid.pack(fill="x", padx=10, pady=(0, 15))
            charts_grid.grid_columnconfigure((0, 1), weight=1)

            # Lista de gráficos disponíveis
            available_charts = []

            # Gráfico: Distribuição de saídas (Despesas vs Folha)
            total_expenses = overview.get("total_expenses", 0)
            total_payroll = overview.get("total_payroll", 0)
            if total_expenses > 0 or total_payroll > 0:
                path_outflow = os.path.join(self._temp_dir, "outflow_pie.png")
                create_pie_chart(
                    ["Despesas", "Folha de Pagamento"],
                    [total_expenses, total_payroll],
                    title="Saídas: Despesas vs Folha",
                    output_path=path_outflow,
                )
                available_charts.append({
                    "title": "Distribuição de Saídas",
                    "description": "Despesas vs Folha de Pagamento",
                    "icon": "💸",
                    "path": path_outflow,
                    "color": COLORS["error"],
                })

            # Gráfico: Receita vs Saídas
            total_income = overview.get("total_income", 0)
            total_outflow = overview.get("total_outflow", 0)
            if total_income > 0 or total_outflow > 0:
                path_balance = os.path.join(self._temp_dir, "balance_pie.png")
                create_pie_chart(
                    ["Receita Recebida", "Despesas + Folha"],
                    [total_income, total_outflow],
                    title="Receita vs Total de Saídas",
                    output_path=path_balance,
                )
                available_charts.append({
                    "title": "Receita vs Saídas",
                    "description": "Balanço geral do negócio",
                    "icon": "💰",
                    "path": path_balance,
                    "color": COLORS["success"],
                })

            # Gráfico: Despesas por categoria
            expenses_by_cat = overview.get("expenses_by_category", {})
            if expenses_by_cat:
                cat_labels_map = {
                    "geral": "Geral", "equipamento": "Equipamento", "material": "Material",
                    "transporte": "Transporte", "aluguel": "Aluguel", "manutencao": "Manutenção",
                    "outros": "Outros",
                }
                cat_labels = [cat_labels_map.get(k, k) for k in expenses_by_cat.keys()]
                cat_values = list(expenses_by_cat.values())

                path_cat = os.path.join(self._temp_dir, "expenses_category_pie.png")
                create_pie_chart(
                    cat_labels, cat_values,
                    title="Despesas por Categoria",
                    output_path=path_cat,
                )
                available_charts.append({
                    "title": "Despesas por Categoria",
                    "description": f"{len(expenses_by_cat)} categorias diferentes",
                    "icon": "📂",
                    "path": path_cat,
                    "color": COLORS["warning"],
                })

            # Gráfico: Orçamentos por status
            quotes_by_status = self._get_quotes_by_status()
            if quotes_by_status:
                status_labels_map = {
                    'draft': 'Rascunho', 'sent': 'Enviado',
                    'approved': 'Aprovado', 'completed': 'Concluído',
                }
                s_labels = [status_labels_map.get(k, k) for k in quotes_by_status.keys()]
                s_values = list(quotes_by_status.values())

                path_status = os.path.join(self._temp_dir, "status_pie.png")
                create_pie_chart(
                    s_labels, s_values,
                    title="Orçamentos por Status",
                    output_path=path_status,
                )
                available_charts.append({
                    "title": "Orçamentos por Status",
                    "description": f"{sum(s_values)} orçamentos no total",
                    "icon": "📋",
                    "path": path_status,
                    "color": COLORS["primary"],
                })

            # Criar cards clicáveis para cada gráfico
            for idx, chart in enumerate(available_charts):
                row = idx // 2
                col = idx % 2

                card = ctk.CTkButton(
                    charts_grid,
                    text="",
                    fg_color=COLORS["card"],
                    hover_color=COLORS["border_hover"],
                    corner_radius=12,
                    border_width=2,
                    border_color=chart["color"],
                    height=120,
                    command=lambda p=chart["path"], t=chart["title"]: self._expand_chart(p, t),
                )
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

                # Conteúdo do card
                card_content = ctk.CTkFrame(card, fg_color="transparent")
                card_content.place(relx=0.5, rely=0.5, anchor="center")

                # Ícone grande
                ctk.CTkLabel(
                    card_content, text=chart["icon"],
                    font=ctk.CTkFont(size=40),
                ).pack(pady=(0, 8))

                # Título
                ctk.CTkLabel(
                    card_content, text=chart["title"],
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLORS["text"],
                ).pack()

                # Descrição
                ctk.CTkLabel(
                    card_content, text=chart["description"],
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"],
                ).pack(pady=(2, 0))

                # Indicador de clique
                ctk.CTkLabel(
                    card_content, text="🔍 Clique para ampliar",
                    font=ctk.CTkFont(size=10),
                    text_color=chart["color"],
                ).pack(pady=(8, 0))

            if not available_charts:
                ctk.CTkLabel(
                    scroll, text="Nenhum gráfico disponível. Registre despesas, folha e orçamentos.",
                    font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"],
                ).pack(pady=30)

            # Resumo mensal: Este mês
            ctk.CTkLabel(
                scroll, text="Resumo do Mês Atual",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
            ).pack(anchor="w", padx=10, pady=(15, 5))

            month_metrics = [
                ("Despesas do Mês", format_currency(overview.get("expenses_month", 0)), COLORS["error"]),
                ("Folha do Mês", format_currency(overview.get("payroll_month", 0)), COLORS["warning"]),
            ]
            for label, value, color in month_metrics:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8,
                                    border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", padx=10, pady=2)
                ri = ctk.CTkFrame(row, fg_color="transparent")
                ri.pack(fill="x", padx=15, pady=8)
                ctk.CTkFrame(ri, width=4, height=25, corner_radius=2,
                             fg_color=color).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                             text_color=COLORS["text"]).pack(side="left")
                ctk.CTkLabel(ri, text=value, font=ctk.CTkFont(size=14, weight="bold"),
                             text_color=color).pack(side="right")

        except Exception as e:
            ctk.CTkLabel(parent, text=f"Erro: {e}", text_color=COLORS["error"]).pack(pady=10)

    def _fill_overview_tab(self, parent, analytics_data, quotes_data, stats=None):
        """Aba de visão geral com todos os dados resumidos."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="Resumo completo do período",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=10, pady=(10, 12))

        metrics = []

        if analytics_data:
            total_revenue = sum(d.get("revenue", 0) for d in analytics_data)
            total_cost = sum(d.get("cost", 0) for d in analytics_data)
            total_profit = sum(d.get("profit", 0) for d in analytics_data)
            margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

            metrics += [
                ("Faturamento Total", format_currency(total_revenue), COLORS["primary"]),
                ("Custo Total", format_currency(total_cost), COLORS["error"]),
                ("Lucro Total", format_currency(total_profit), COLORS["success"]),
                ("Margem Média", f"{margin:.1f}%", COLORS["warning"]),
                ("Meses Analisados", str(len(analytics_data)), COLORS["primary"]),
            ]

        # Adicionar métricas de pagamento
        if stats is None:
            stats = db.get_dashboard_stats()

        metrics += [
            ("💵 Total Recebido", format_currency(stats.get("total_received", 0)), COLORS["success"]),
            ("📛 Saldo Devedor Total", format_currency(stats.get("total_pending", 0)), COLORS["error"]),
            ("✅ Orçamentos Quitados", str(stats.get("paid_quotes", 0)), COLORS["primary"]),
        ]

        # Adicionar métricas financeiras (despesas e folha)
        try:
            fin = db.get_financial_overview()
            metrics += [
                ("💸 Total Despesas", format_currency(fin.get("total_expenses", 0)), COLORS["error"]),
                ("👥 Total Folha", format_currency(fin.get("total_payroll", 0)), COLORS["warning"]),
                ("📊 Balanço Geral", format_currency(fin.get("balance", 0)),
                 COLORS["success"] if fin.get("balance", 0) >= 0 else COLORS["error"]),
            ]
        except Exception:
            pass

        if metrics:
            for label, value, color in metrics:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8,
                                    border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", padx=10, pady=3)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=15, pady=10)

                ctk.CTkFrame(inner, width=4, height=30, corner_radius=2,
                             fg_color=color).pack(side="left", padx=(0, 12))
                ctk.CTkLabel(inner, text=label, font=ctk.CTkFont(size=13),
                             text_color=COLORS["text"]).pack(side="left")
                ctk.CTkLabel(inner, text=value, font=ctk.CTkFont(size=15, weight="bold"),
                             text_color=color).pack(side="right")
        else:
            ctk.CTkLabel(
                scroll, text="Sem dados financeiros disponíveis.",
                font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"],
            ).pack(padx=10, pady=20)

    def _fill_payments_tab(self, parent, stats):
        """Aba de pagamentos com detalhes de recebimentos e devedores."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="Detalhamento de pagamentos por orçamento",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=10, pady=(10, 12))

        # Resumo geral de pagamentos
        summary_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                      border_width=1, border_color=COLORS["border"])
        summary_frame.pack(fill="x", padx=10, pady=(0, 15))

        summary_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_grid.pack(fill="x", padx=15, pady=15)
        summary_grid.grid_columnconfigure((0, 1, 2), weight=1)

        total_received = stats.get("total_received", 0)
        total_pending = stats.get("total_pending", 0)
        paid_count = stats.get("paid_quotes", 0)

        pay_items = [
            ("💵 Total Recebido", format_currency(total_received), COLORS["success"]),
            ("📛 Saldo Devedor", format_currency(total_pending), COLORS["error"]),
            ("✅ Quitados", str(paid_count), COLORS["primary"]),
        ]

        for col, (label, value, color) in enumerate(pay_items):
            cell = ctk.CTkFrame(summary_grid, fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, sticky="nsew")
            ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack()
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=color).pack(pady=(2, 0))

        # Lista de orçamentos com saldo
        all_quotes = db.get_all_quotes()
        summaries = db.get_all_payment_summaries()

        # Seção: Orçamentos com saldo devedor
        ctk.CTkLabel(
            scroll, text="📛 Orçamentos com Saldo Devedor",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["error"],
        ).pack(anchor="w", padx=10, pady=(10, 5))

        pending_found = False
        for q in all_quotes:
            qid = q.get("id")
            if q.get("status") not in ("approved", "completed"):
                continue
            summary = summaries.get(qid, {})
            balance = summary.get("balance", q.get("total", 0))
            if balance <= 0:
                continue
            pending_found = True
            self._create_payment_quote_row(scroll, q, summary)

        if not pending_found:
            ctk.CTkLabel(
                scroll, text="Nenhum orçamento com saldo devedor.",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=20, pady=5)

        # Seção: Orçamentos quitados
        ctk.CTkLabel(
            scroll, text="✅ Orçamentos Quitados",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"],
        ).pack(anchor="w", padx=10, pady=(15, 5))

        paid_found = False
        for q in all_quotes:
            qid = q.get("id")
            if q.get("status") not in ("approved", "completed"):
                continue
            summary = summaries.get(qid, {})
            balance = summary.get("balance", q.get("total", 0))
            total_paid = summary.get("total_paid", 0)
            if balance > 0 or total_paid <= 0:
                continue
            paid_found = True
            self._create_payment_quote_row(scroll, q, summary)

        if not paid_found:
            ctk.CTkLabel(
                scroll, text="Nenhum orçamento quitado ainda.",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=20, pady=5)

    def _create_payment_quote_row(self, parent, quote, summary):
        """Cria uma linha de orçamento na aba de pagamentos."""
        row = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8,
                            border_width=1, border_color=COLORS["border"])
        row.pack(fill="x", padx=10, pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        # Info do orçamento
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        client = quote.get("client_name", "Sem nome")
        qid = quote.get("id", "")
        ctk.CTkLabel(left, text=f"#{qid} — {client}",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")

        total = summary.get("total", quote.get("total", 0))
        paid = summary.get("total_paid", 0)
        balance = summary.get("balance", total)
        is_paid = balance <= 0 and paid > 0

        detail_text = f"Total: {format_currency(total)}  |  Pago: {format_currency(paid)}  |  Saldo: {format_currency(max(balance, 0))}"
        ctk.CTkLabel(left, text=detail_text, font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(2, 0))

        # Badge de status
        badge_color = COLORS["success"] if is_paid else COLORS["error"]
        badge_text = "QUITADO" if is_paid else "DEVEDOR"
        badge = ctk.CTkLabel(inner, text=badge_text,
                             font=ctk.CTkFont(size=10, weight="bold"),
                             text_color="#FFFFFF",
                             fg_color=badge_color,
                             corner_radius=6, width=70, height=24)
        badge.pack(side="right", padx=(10, 0))

    def _add_data_table(self, parent, data, keys, headers):
        """Adiciona tabela resumida de dados."""
        table_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10,
                                    border_width=1, border_color=COLORS["border"])
        table_frame.pack(fill="x", padx=10, pady=(15, 10))

        # Header
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["primary_lighter"], corner_radius=6)
        header_row.pack(fill="x", padx=8, pady=(8, 2))

        for h in headers:
            ctk.CTkLabel(header_row, text=h, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLORS["primary"]).pack(side="left", expand=True, padx=4, pady=6)

        # Linhas de dados (últimas 6)
        for item in data[:6]:
            row = ctk.CTkFrame(table_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=1)

            for key in keys:
                val = item.get(key, 0)
                if isinstance(val, (int, float)) and key != "month":
                    text = format_currency(val)
                else:
                    text = str(val)
                ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11),
                             text_color=COLORS["text"]).pack(side="left", expand=True, padx=4, pady=4)

            sep = ctk.CTkFrame(table_frame, height=1, fg_color=COLORS["border"])
            sep.pack(fill="x", padx=8)

        ctk.CTkFrame(table_frame, height=6, fg_color="transparent").pack()

    def _display_chart_image(self, parent, image_path):
        """Exibe uma imagem de gráfico com CTkImage."""
        try:
            from PIL import Image
            img = Image.open(image_path)

            max_width = 750
            ratio = max_width / img.width
            new_height = int(img.height * ratio)

            ctk_img = ctk.CTkImage(img, size=(max_width, new_height))
            self._chart_images.append(ctk_img)

            chart_container = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10,
                                            border_width=1, border_color=COLORS["border"])
            chart_container.pack(padx=10, pady=5)

            # Header com botão expandir
            header_frame = ctk.CTkFrame(chart_container, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=(10, 5))

            ctk.CTkButton(
                header_frame, text="🔍 Expandir Gráfico",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
                height=28, width=140, corner_radius=6,
                command=lambda path=image_path: self._expand_chart(path),
            ).pack(side="right")

            label = ctk.CTkLabel(chart_container, image=ctk_img, text="")
            label.pack(padx=10, pady=(5, 10))
        except Exception:
            pass

    def _expand_chart(self, image_path, chart_title=None):
        """Abre o gráfico em uma janela maximizada."""
        try:
            from PIL import Image
            
            dialog = ctk.CTkToplevel(self.app)
            dialog.title(chart_title or "Visualização de Gráfico")
            dialog.attributes('-topmost', True)
            
            # Obter dimensões da tela
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            
            # Definir tamanho da janela (90% da tela)
            window_width = int(screen_width * 0.9)
            window_height = int(screen_height * 0.9)
            
            # Centralizar
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg"])
            main_frame.pack(fill="both", expand=True)
            
            # Header com botão fechar
            header = ctk.CTkFrame(main_frame, fg_color=COLORS["card"], height=50)
            header.pack(fill="x", padx=10, pady=(10, 5))
            header.pack_propagate(False)
            
            title_text = f"📊 {chart_title}" if chart_title else "📊 Visualização em Tela Cheia"
            ctk.CTkLabel(
                header, text=title_text,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text"],
            ).pack(side="left", padx=15)
            
            ctk.CTkButton(
                header, text="✕ Fechar", 
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=COLORS["error"], hover_color=COLORS["error_hover"],
                height=32, width=100, corner_radius=6,
                command=dialog.destroy,
            ).pack(side="right", padx=15)
            
            # Container do gráfico com scroll
            scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
            
            # Carregar e exibir imagem em alta resolução
            img = Image.open(image_path)
            
            # Calcular tamanho máximo mantendo aspect ratio
            available_width = window_width - 60
            available_height = window_height - 150
            
            ratio = min(available_width / img.width, available_height / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            # Criar imagem CTk em alta resolução
            ctk_img_large = ctk.CTkImage(img, size=(new_width, new_height))
            
            # Container centralizado para a imagem
            img_container = ctk.CTkFrame(scroll_frame, fg_color=COLORS["card"],
                                          corner_radius=12, border_width=1,
                                          border_color=COLORS["border"])
            img_container.pack(expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(img_container, image=ctk_img_large, text="")
            label.pack(padx=20, pady=20)
            
            # Manter referência da imagem
            label._img_ref = ctk_img_large
            
            # Atalho ESC para fechar
            dialog.bind('<Escape>', lambda e: dialog.destroy())
            
        except Exception as e:
            self.app.show_toast(f"Erro ao expandir gráfico: {e}", "error")

    def _get_quotes_by_status(self):
        """Obtém contagem de orçamentos por status."""
        try:
            all_quotes = db.get_all_quotes()
            status_count = {}
            for q in all_quotes:
                s = q.get("status", "draft")
                status_count[s] = status_count.get(s, 0) + 1
            return status_count if status_count else None
        except Exception:
            return None
