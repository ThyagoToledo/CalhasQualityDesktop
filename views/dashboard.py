# -*- coding: utf-8 -*-
"""
CalhaGest - Dashboard
Painel principal com estatísticas, orçamentos recentes e alertas.
"""

import customtkinter as ctk
from database import db
from components.cards import StatCard, StatusBadge, create_header, COLORS
from components.dialogs import format_currency, format_date


class DashboardView(ctk.CTkScrollableFrame):
    """View do dashboard."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        stats = db.get_dashboard_stats()
        settings = db.get_settings()
        company = settings.get("company_name", "CalhaGest")

        # Cabeçalho
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text=f"Bem-vindo ao {company}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left")

        # Botões de ação no header
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")

        ctk.CTkButton(
            actions_frame,
            text="🌙" if self.app.current_theme == "light" else "☀️",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS["card"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            height=32,
            width=40,
            corner_radius=8,
            command=self.app.toggle_theme,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions_frame,
            text="⚙️ Config",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["card"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            height=32,
            width=90,
            corner_radius=8,
            command=lambda: self.app.show_view("settings"),
        ).pack(side="left")

        # Cards de estatísticas
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        StatCard(
            cards_frame,
            "Total Orçamentos",
            stats.get("total_quotes", 0),
            icon="📋",
            color=COLORS["primary"],
        ).grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        StatCard(
            cards_frame,
            "Aprovados",
            stats.get("approved_quotes", 0),
            icon="✅",
            color=COLORS["success"],
        ).grid(row=0, column=1, padx=8, sticky="nsew")

        StatCard(
            cards_frame,
            "Faturamento",
            format_currency(stats.get("total_revenue", 0)),
            icon="💰",
            color=COLORS["warning"],
        ).grid(row=0, column=2, padx=8, sticky="nsew")

        StatCard(
            cards_frame,
            "Lucro Total",
            format_currency(stats.get("total_profit", 0)),
            icon="📈",
            color=COLORS["success"],
        ).grid(row=0, column=3, padx=(8, 0), sticky="nsew")

        # Seção inferior: Orçamentos Recentes + Alertas
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure(0, weight=2)
        bottom.grid_columnconfigure(1, weight=1)

        # Orçamentos recentes
        recent_frame = ctk.CTkFrame(
            bottom, fg_color=COLORS["card"], corner_radius=12,
            border_width=1, border_color=COLORS["border"]
        )
        recent_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")

        recent_header = ctk.CTkFrame(recent_frame, fg_color="transparent")
        recent_header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            recent_header,
            text="📋 Orçamentos Recentes",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        ctk.CTkButton(
            recent_header,
            text="Ver todos →",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=COLORS["primary"],
            hover_color=COLORS["border"],
            height=28,
            width=90,
            command=lambda: self.app.show_view("quotes"),
        ).pack(side="right")

        recent_quotes = stats.get("recent_quotes", [])
        if recent_quotes:
            for quote in recent_quotes:
                self._create_quote_row(recent_frame, quote)
        else:
            ctk.CTkLabel(
                recent_frame,
                text="Nenhum orçamento cadastrado ainda.",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
            ).pack(padx=15, pady=20)

        # Alertas e Ações Rápidas
        alerts_frame = ctk.CTkFrame(
            bottom, fg_color=COLORS["card"], corner_radius=12,
            border_width=1, border_color=COLORS["border"]
        )
        alerts_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")

        ctk.CTkLabel(
            alerts_frame,
            text="🔔 Alertas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(padx=15, pady=(15, 10), anchor="w")

        # Alerta de estoque baixo
        low_stock = stats.get("low_stock_count", 0)
        if low_stock > 0:
            alert_item = ctk.CTkFrame(alerts_frame, fg_color=COLORS["error_light"],
                                       corner_radius=8)
            alert_item.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                alert_item,
                text=f"⚠️ {low_stock} itens com estoque baixo",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["error"],
                anchor="w",
            ).pack(padx=10, pady=8, anchor="w")

        # Instalações pendentes
        pending = stats.get("pending_installations", 0)
        if pending > 0:
            alert_item = ctk.CTkFrame(alerts_frame, fg_color=COLORS["warning_light"],
                                       corner_radius=8)
            alert_item.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                alert_item,
                text=f"📅 {pending} instalações pendentes",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["warning"],
                anchor="w",
            ).pack(padx=10, pady=8, anchor="w")

        if low_stock == 0 and pending == 0:
            ctk.CTkLabel(
                alerts_frame,
                text="✅ Tudo em dia!",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["success"],
            ).pack(padx=15, pady=10)

        # Ações rápidas
        ctk.CTkLabel(
            alerts_frame,
            text="⚡ Ações Rápidas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(padx=15, pady=(20, 10), anchor="w")

        actions = [
            ("Novo Orçamento", "quotes"),
            ("Novo Produto", "products"),
            ("Ver Estoque", "inventory"),
            ("Ver Relatórios", "analytics"),
        ]
        for text, view in actions:
            ctk.CTkButton(
                alerts_frame,
                text=f"  {text}",
                font=ctk.CTkFont(size=12),
                fg_color=COLORS["primary_lighter"],
                text_color=COLORS["primary"],
                hover_color=COLORS["primary_hover_light"],
                height=34,
                corner_radius=8,
                anchor="w",
                command=lambda v=view: self.app.show_view(v),
            ).pack(fill="x", padx=12, pady=3)

        # Espaço final
        ctk.CTkFrame(alerts_frame, height=15, fg_color="transparent").pack()

    def _create_quote_row(self, parent, quote):
        """Cria uma linha de orçamento recente."""
        row = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=15, pady=4)
        row.bind("<Button-1>", lambda e: self.app.show_view("quotes"))

        # Separador
        sep = ctk.CTkFrame(row, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", pady=(0, 8))

        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(fill="x")

        # Info esquerda
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left,
            text=quote.get("client_name", "—"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=format_date(quote.get("created_at", "")),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(anchor="w")

        # Info direita
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkLabel(
            right,
            text=format_currency(quote.get("total", 0)),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="e")

        StatusBadge(right, quote.get("status", "draft")).pack(anchor="e", pady=(4, 0))
