# -*- coding: utf-8 -*-
"""
CalhaGest - Componentes de Cards
Cards reutilizáveis para exibição de dados.
"""

import customtkinter as ctk
from theme import get_color, ThemeManager


class StatCard(ctk.CTkFrame):
    """Card de estatística para o dashboard."""

    def __init__(self, parent, title, value, icon="📊", color=None, **kwargs):
        super().__init__(parent, fg_color=get_color("card"), corner_radius=12,
                         border_width=1, border_color=get_color("border"), **kwargs)
        accent = color or get_color("primary")

        # Barra de cor lateral
        top_bar = ctk.CTkFrame(self, height=4, fg_color=accent, corner_radius=2)
        top_bar.pack(fill="x", padx=0, pady=0, side="top")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=12)

        # Ícone e título
        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            header, text=icon, font=ctk.CTkFont(size=22)
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=get_color("text_secondary"),
        ).pack(side="left", padx=8)

        # Valor
        ctk.CTkLabel(
            body,
            text=str(value),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=get_color("text"),
            anchor="w",
        ).pack(anchor="w")


class DataCard(ctk.CTkFrame):
    """Card genérico para listagem de dados (produtos, orçamentos, etc.)."""

    def __init__(self, parent, on_click=None, **kwargs):
        super().__init__(
            parent,
            fg_color=get_color("card"),
            corner_radius=10,
            border_width=1,
            border_color=get_color("border"),
            cursor="hand2" if on_click else "",
            **kwargs
        )
        self._on_click = on_click
        if on_click:
            self.bind("<Button-1>", lambda e: on_click())
            # Bind children too
            self.bind("<Enter>", lambda e: self.configure(border_color=get_color("primary")))
            self.bind("<Leave>", lambda e: self.configure(border_color=get_color("border")))


class StatusBadge(ctk.CTkLabel):
    """Badge colorido de status com estilo pill."""

    def __init__(self, parent, status, **kwargs):
        status_colors = ThemeManager.get_status_colors()
        color, text = status_colors.get(status, ("#6b7280", status))
        super().__init__(
            parent,
            text=f"  {text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=color,
            text_color="white",
            corner_radius=12,
            height=22,
            **kwargs
        )


def create_search_bar(parent, placeholder="Pesquisar...", on_search=None):
    """Cria uma barra de pesquisa."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    entry = ctk.CTkEntry(
        frame,
        placeholder_text=placeholder,
        height=38,
        font=ctk.CTkFont(size=13),
        border_color=get_color("border"),
        fg_color=get_color("card"),
        corner_radius=10,
    )
    entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    if on_search:
        entry.bind("<Return>", lambda e: on_search(entry.get()))
        btn = ctk.CTkButton(
            frame,
            text="🔍",
            width=38,
            height=38,
            fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"),
            corner_radius=10,
            command=lambda: on_search(entry.get()),
        )
        btn.pack(side="right")

    return frame, entry


def create_header(parent, title, subtitle=None, action_text=None, action_command=None):
    """Cria cabeçalho de página com título e botão de ação opcional."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    left = ctk.CTkFrame(frame, fg_color="transparent")
    left.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        left,
        text=title,
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=get_color("text"),
        anchor="w",
    ).pack(anchor="w")

    if subtitle:
        ctk.CTkLabel(
            left,
            text=subtitle,
            font=ctk.CTkFont(size=12),
            text_color=get_color("text_secondary"),
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

    if action_text and action_command:
        ctk.CTkButton(
            frame,
            text=f"  + {action_text}  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"),            height=38,
            corner_radius=10,
            command=action_command,
        ).pack(side="right")

    return frame