# -*- coding: utf-8 -*-
"""
CalhaGest - Módulo de Temas
Gerencia paletas de cores para os modos claro e escuro.
"""

# Paletas de cores por tema
THEMES = {
    "light": {
        "bg":                  "#F3F4F6",
        "card":                "#FFFFFF",
        "sidebar_bg":          "#1E3A5F",
        "sidebar_text":        "#FFFFFF",
        "sidebar_hover":       "#2D5986",
        "sidebar_active":      "#3A7BD5",
        "sidebar_accent":      "#3A7BD5",
        "primary":             "#3A7BD5",
        "primary_hover":       "#2D6BC4",
        "primary_light":       "#EBF2FF",
        "primary_hover_light": "#D6E8FF",
        "primary_lighter":     "#E6F0FE",
        "text":                "#111827",
        "text_secondary":      "#6B7280",
        "border":              "#E5E7EB",
        "border_hover":        "#D1D5DB",
        "success":             "#10B981",
        "success_hover":       "#059669",
        "success_light":       "#D1FAE5",
        "success_hover_light": "#A7F3D0",
        "warning":             "#F59E0B",
        "warning_hover":       "#D97706",
        "warning_light":       "#FEF3C7",
        "warning_hover_light": "#FDE68A",
        "error":               "#EF4444",
        "error_hover":         "#DC2626",
        "error_light":         "#FEE2E2",
        "error_hover_light":   "#FECACA",
        "purple":              "#8B5CF6",
        "purple_hover":        "#7C3AED",
        "gray":                "#9CA3AF",
        "gray_hover":          "#6B7280",
    },
    "dark": {
        "bg":                  "#0F172A",
        "card":                "#1E293B",
        "sidebar_bg":          "#0A0F1E",
        "sidebar_text":        "#E2E8F0",
        "sidebar_hover":       "#1E3A5F",
        "sidebar_active":      "#3A7BD5",
        "sidebar_accent":      "#3A7BD5",
        "primary":             "#3A7BD5",
        "primary_hover":       "#4A8BE5",
        "primary_light":       "#1E3A5F",
        "primary_hover_light": "#2D4A6F",
        "primary_lighter":     "#0F2847",
        "text":                "#E2E8F0",
        "text_secondary":      "#94A3B8",
        "border":              "#2D3748",
        "border_hover":        "#4A5568",
        "success":             "#10B981",
        "success_hover":       "#34D399",
        "success_light":       "#064E3B",
        "success_hover_light": "#047857",
        "warning":             "#F59E0B",
        "warning_hover":       "#FCD34D",
        "warning_light":       "#78350F",
        "warning_hover_light": "#A16207",
        "error":               "#EF4444",
        "error_hover":         "#F87171",
        "error_light":         "#7F1D1D",
        "error_hover_light":   "#991B1B",
        "purple":              "#8B5CF6",
        "purple_hover":        "#A78BFA",
        "gray":                "#6B7280",
        "gray_hover":          "#9CA3AF",
    },
}

# Tema ativo (referência mutável)
_current_theme = "light"

# Atalho para a paleta ativa (usado via `from theme import COLORS`)
COLORS = THEMES["light"]


class ThemeManager:
    """Gerenciador de tema global da aplicação."""

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Define o tema ativo ('light' ou 'dark')."""
        global _current_theme, COLORS
        if theme not in THEMES:
            raise ValueError(f"Tema '{theme}' desconhecido. Use 'light' ou 'dark'.")
        _current_theme = theme
        COLORS = THEMES[_current_theme]

    @classmethod
    def get_theme(cls) -> str:
        """Retorna o nome do tema atual."""
        return _current_theme

    @classmethod
    def toggle_theme(cls) -> str:
        """Alterna entre claro e escuro e retorna o novo tema."""
        new_theme = "dark" if _current_theme == "light" else "light"
        cls.set_theme(new_theme)
        return new_theme

    @classmethod
    def get_colors(cls) -> dict:
        """Retorna a paleta completa do tema atual."""
        return THEMES[_current_theme]

    @classmethod
    def get_status_colors(cls) -> dict:
        """
        Retorna um dicionário mapeando nomes de status para
        (cor_hex, texto_exibido).
        """
        return {
            # Orçamentos
            "draft":      ("#6B7280", "Rascunho"),
            "sent":       ("#3A7BD5", "Enviado"),
            "approved":   ("#10B981", "Aprovado"),
            "rejected":   ("#EF4444", "Recusado"),
            "expired":    ("#F59E0B", "Expirado"),
            # Instalações
            "pending":    ("#F59E0B", "Pendente"),
            "scheduled":  ("#3A7BD5", "Agendado"),
            "in_progress":("#8B5CF6", "Em andamento"),
            "completed":  ("#10B981", "Concluído"),
            "cancelled":  ("#EF4444", "Cancelado"),
            # Pagamentos / Despesas
            "paid":       ("#10B981", "Pago"),
            "unpaid":     ("#EF4444", "Em aberto"),
            "partial":    ("#F59E0B", "Parcial"),
            "overdue":    ("#DC2626", "Atrasado"),
            # Estoque
            "active":     ("#10B981", "Ativo"),
            "inactive":   ("#6B7280", "Inativo"),
            "low_stock":  ("#F59E0B", "Estoque baixo"),
            "out_of_stock": ("#EF4444", "Sem estoque"),
        }


def get_color(key: str) -> str:
    """Retorna a cor hexadecimal para a chave fornecida no tema atual."""
    return THEMES[_current_theme].get(key, "#000000")


def get_colors() -> dict:
    """Retorna a paleta completa do tema atual."""
    return THEMES[_current_theme]
