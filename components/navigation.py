# -*- coding: utf-8 -*-
"""
CalhaGest - Barra de Navegação Lateral (Sidebar)
Sidebar com botões de navegação estilizados e visual moderno.
"""

import customtkinter as ctk
from theme import get_color


class Sidebar(ctk.CTkFrame):
    """Barra lateral de navegação."""

    NAV_ITEMS = [
        ("dashboard", "📊", "Dashboard"),
        ("products", "📦", "Produtos"),
        ("quotes", "📋", "Orçamentos"),
        ("inventory", "🏗️", "Estoque"),
        ("installations", "📅", "Instalações"),
        ("analytics", "📈", "Relatórios"),
    ]

    def __init__(self, parent, on_navigate, company_name="CalhaGest"):
        super().__init__(parent, width=230, corner_radius=0, fg_color=get_color("sidebar_bg"))
        self.on_navigate = on_navigate
        self.buttons = {}
        self.grid_propagate(False)

        # Logo / Nome da empresa
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(25, 0))

        # Barra de acento azul
        ctk.CTkFrame(logo_frame, width=4, height=40, fg_color=get_color("sidebar_accent"),
                     corner_radius=2).pack(side="left", padx=(0, 12))

        logo_text = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text.pack(side="left")

        self.company_label = ctk.CTkLabel(
            logo_text,
            text=company_name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=get_color("text"),
        )
        self.company_label.pack(anchor="w")

        ctk.CTkLabel(
            logo_text,
            text="Gestão de Calhas",
            font=ctk.CTkFont(size=11),
            text_color=get_color("sidebar_text"),
        ).pack(anchor="w")

        # Separador
        sep = ctk.CTkFrame(self, height=1, fg_color=get_color("border"))
        sep.pack(fill="x", padx=15, pady=(20, 15))

        # Seção de menu
        ctk.CTkLabel(
            self,
            text="MENU PRINCIPAL",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=get_color("sidebar_text"),
            anchor="w",
        ).pack(padx=25, pady=(0, 8), anchor="w")

        # Botões de navegação
        for key, icon, label in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=get_color("sidebar_text"),
                hover_color=get_color("sidebar_hover"),
                anchor="w",
                height=42,
                corner_radius=10,
                command=lambda k=key: self._on_click(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.buttons[key] = btn

        # Espaço flexível
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Separador inferior
        sep2 = ctk.CTkFrame(self, height=1, fg_color=get_color("border"))
        sep2.pack(fill="x", padx=15, pady=(0, 10))

        # Botão de configurações
        settings_btn = ctk.CTkButton(
            self,
            text="  ⚙️  Configurações",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=get_color("sidebar_text"),
            hover_color=get_color("sidebar_hover"),
            anchor="w",
            height=42,
            corner_radius=10,
            command=lambda: self._on_click("settings"),
        )
        settings_btn.pack(fill="x", padx=12, pady=(0, 20))
        self.buttons["settings"] = settings_btn

    def _on_click(self, key):
        """Callback quando um botão de navegação é clicado."""
        self.on_navigate(key)

    def set_active(self, key):
        """Define o botão ativo (destacado)."""
        for btn_key, btn in self.buttons.items():
            if btn_key == key:
                btn.configure(fg_color=get_color("sidebar_active"), text_color=get_color("text"))
            else:
                btn.configure(fg_color="transparent", text_color=get_color("sidebar_text"))
