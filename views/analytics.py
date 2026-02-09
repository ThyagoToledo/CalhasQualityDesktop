# -*- coding: utf-8 -*-
"""
CalhaGest - Relatórios e Analytics
Gráficos financeiros com abas de seleção e visuais melhorados.
"""

import customtkinter as ctk
import os
import tempfile
from database import db
from components.cards import COLORS, create_header
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
            segmented_button_fg_color="#e2e8f0",
            segmented_button_selected_color=COLORS["primary"],
            segmented_button_selected_hover_color="#1d4ed8",
            segmented_button_unselected_color="#e2e8f0",
            segmented_button_unselected_hover_color="#cbd5e1",
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

        self._fill_overview_tab(tab_overview, analytics, quotes_by_status)

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
        # Remover todas as abas existentes
        for tab_name in ["💰 Faturamento vs Custo", "📈 Evolução Financeira", 
                         "📋 Orçamentos por Status", "📊 Visão Geral"]:
            try:
                self.tabview.delete(tab_name)
            except:
                pass
        
        # Recriar abas
        tab_revenue = self.tabview.add("💰 Faturamento vs Custo")
        tab_evolution = self.tabview.add("📈 Evolução Financeira")
        tab_status = self.tabview.add("📋 Orçamentos por Status")
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
        
        self._fill_overview_tab(tab_overview, analytics, quotes_by_status)

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

    def _fill_overview_tab(self, parent, analytics_data, quotes_data):
        """Aba de visão geral com todos os dados resumidos."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="Resumo completo do período",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=10, pady=(10, 12))

        if analytics_data:
            total_revenue = sum(d.get("revenue", 0) for d in analytics_data)
            total_cost = sum(d.get("cost", 0) for d in analytics_data)
            total_profit = sum(d.get("profit", 0) for d in analytics_data)
            margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

            metrics = [
                ("Faturamento Total", format_currency(total_revenue), COLORS["primary"]),
                ("Custo Total", format_currency(total_cost), COLORS["error"]),
                ("Lucro Total", format_currency(total_profit), COLORS["success"]),
                ("Margem Média", f"{margin:.1f}%", COLORS["warning"]),
                ("Meses Analisados", str(len(analytics_data)), COLORS["primary"]),
            ]

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

            label = ctk.CTkLabel(chart_container, image=ctk_img, text="")
            label.pack(padx=10, pady=10)
        except Exception:
            pass

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

    def _get_quotes_by_status(self):
        """Retorna contagem de orçamentos por status."""
        all_quotes = db.get_all_quotes()
        status_count = {}
        for q in all_quotes:
            s = q.get("status", "draft")
            status_count[s] = status_count.get(s, 0) + 1
        return status_count if status_count else None
