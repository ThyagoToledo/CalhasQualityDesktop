# -*- coding: utf-8 -*-
"""
CalhaGest - Sistema de Gestão de Calhas
Interface gráfica usando CustomTkinter (renderização CPU, sem problemas com GPU).
"""

import customtkinter as ctk
from pathlib import Path
import sys
import os

# Garantir que o diretório raiz do projeto esteja no path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from database import db
from theme import ThemeManager, get_color, get_colors


class CalhaGestApp(ctk.CTk):
    """Aplicativo principal CalhaGest."""

    def __init__(self):
        super().__init__()

        # Configuração da janela
        self.title("CalhaGest - Gestão de Calhas")
        self.geometry("1280x720")
        self.minsize(1024, 600)

        # Ícone
        self._set_icon()

        # Tema
        self.current_theme = "light"
        ThemeManager.set_theme("light")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=get_color("bg"))

        # Estado
        self.current_view_name = None

        # Layout: Sidebar + Conteúdo
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        from components.navigation import Sidebar
        settings = db.get_settings()
        company_name = settings.get("company_name", "CalhaGest")
        self.sidebar = Sidebar(self, self.show_view, company_name=company_name)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Área de conteúdo
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Toast container
        self._toast_label = None

        # Cache de views instanciadas (evita reconstrução a cada navegação)
        self._views = {}

        # Exibir dashboard
        self.show_view("dashboard")

    def _set_icon(self):
        """Define o ícone da janela."""
        try:
            icon_path = ROOT_DIR / "icon" / "CaLHAS.png"
            if icon_path.exists():
                from PIL import Image, ImageTk
                img = Image.open(str(icon_path))
                photo = ImageTk.PhotoImage(img.resize((32, 32)))
                self.iconphoto(True, photo)
                self._icon_ref = photo
        except Exception:
            pass

    def show_view(self, view_name):
        """Alterna para uma view diferente (com cache de instâncias)."""
        if view_name == self.current_view_name:
            return

        # Ocultar view atual sem destruir os widgets
        if self.current_view_name and self.current_view_name in self._views:
            self._views[self.current_view_name].pack_forget()

        # Criar view apenas se ainda não estiver em cache
        if view_name not in self._views:
            view = self._create_view(view_name)
            if view:
                self._views[view_name] = view

        # Exibir view (nova ou cacheada)
        if view_name in self._views:
            view = self._views[view_name]
            view.pack(fill="both", expand=True, padx=15, pady=15)
            # Chamar on_show() se a view suportar (para atualizar dados sem reconstruir widgets)
            if hasattr(view, "on_show"):
                view.on_show()

        self.current_view_name = view_name
        self.sidebar.set_active(view_name)

    def _create_view(self, view_name):
        """Cria e retorna uma nova instância de view (chamado apenas uma vez por view)."""
        if view_name == "dashboard":
            from views.dashboard import DashboardView
            return DashboardView(self.content_frame, self)
        elif view_name == "products":
            from views.products import ProductsView
            return ProductsView(self.content_frame, self)
        elif view_name == "quotes":
            from views.quotes import QuotesView
            return QuotesView(self.content_frame, self)
        elif view_name == "inventory":
            from views.inventory import InventoryView
            return InventoryView(self.content_frame, self)
        elif view_name == "installations":
            from views.installations import InstallationsView
            return InstallationsView(self.content_frame, self)
        elif view_name == "expenses":
            from views.expenses import ExpensesView
            return ExpensesView(self.content_frame, self)
        elif view_name == "payroll":
            from views.payroll import PayrollView
            return PayrollView(self.content_frame, self)
        elif view_name == "analytics":
            from views.analytics import AnalyticsView
            return AnalyticsView(self.content_frame, self)
        elif view_name == "settings":
            from views.settings import SettingsView
            return SettingsView(self.content_frame, self)
        return None

    def toggle_theme(self):
        """Alterna entre tema claro e escuro."""
        new_theme = ThemeManager.toggle_theme()
        self.current_theme = new_theme
        
        # Definir o appearance mode do CustomTkinter
        appearance_mode = "dark" if new_theme == "dark" else "light"
        ctk.set_appearance_mode(appearance_mode)
        
        # Atualizar fundo da janela
        self.configure(fg_color=get_color("bg"))
        
        # Exibir notificação
        if new_theme == "dark":
            self.show_toast("Tema escuro ativado 🌙", "info")
        else:
            self.show_toast("Tema claro ativado ☀️", "info")
        
        # Recarregar view atual para atualizar cores
        # Ao trocar de tema é necessário recriar os widgets — limpar o cache
        current = self.current_view_name
        self.current_view_name = None
        self._views.clear()
        self.show_view(current)

    def show_toast(self, message, type_="info"):
        """Exibe uma notificação temporária no topo."""
        colors = {
            "info": get_color("primary"),
            "success": get_color("success"),
            "warning": get_color("warning"),
            "error": get_color("error"),
        }
        bg = colors.get(type_, get_color("primary"))

        # Remover toast anterior
        if self._toast_label and self._toast_label.winfo_exists():
            self._toast_label.destroy()

        self._toast_label = ctk.CTkLabel(
            self.content_frame,
            text=f"  {message}  ",
            fg_color=bg,
            text_color="white",
            corner_radius=8,
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self._toast_label.place(relx=0.5, y=10, anchor="n")
        self._toast_label.lift()

        # Auto-remover após 3 segundos
        self.after(3000, self._hide_toast)

    def _hide_toast(self):
        if self._toast_label and self._toast_label.winfo_exists():
            self._toast_label.destroy()
            self._toast_label = None

    def refresh_sidebar_company(self):
        """Atualiza o nome da empresa na sidebar."""
        settings = db.get_settings()
        company_name = settings.get("company_name", "CalhaGest")
        self.sidebar.update_company_name(company_name)


if __name__ == "__main__":
    app = CalhaGestApp()
    app.mainloop()
