# -*- coding: utf-8 -*-
"""
CalhaGest - Configurações do Sistema
Informações da empresa, backup e gestão de dados.
"""

import customtkinter as ctk
import shutil
import os
from pathlib import Path
from database import db
from components.cards import COLORS, create_header
from components.dialogs import ConfirmDialog


class SettingsView(ctk.CTkScrollableFrame):
    """View de configurações."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        # Cabeçalho
        header = create_header(self, "Configurações", "Personalize o sistema")
        header.pack(fill="x", pady=(0, 20))

        settings = db.get_settings()

        # === Informações da Empresa ===
        company_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                     border_width=1, border_color=COLORS["border"])
        company_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            company_card, text="🏢 Informações da Empresa",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 10), anchor="w")

        form = ctk.CTkFrame(company_card, fg_color="transparent")
        form.pack(fill="x", padx=15, pady=(0, 15))
        form.grid_columnconfigure((0, 1), weight=1)

        self.entries = {}

        fields = [
            ("company_name", "Nome da Empresa", 0, 0),
            ("company_phone", "Telefone", 0, 1),
            ("company_email", "E-mail", 1, 0),
            ("company_cnpj", "CNPJ/CPF", 1, 1),
            ("company_address", "Endereço", 2, 0),
        ]

        for key, label, row, col in fields:
            colspan = 2 if key == "company_address" else 1
            ctk.CTkLabel(
                form, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text"],
            ).grid(row=row * 2, column=col, sticky="w",
                   columnspan=colspan, padx=5, pady=(8, 2))

            entry = ctk.CTkEntry(form, height=35, font=ctk.CTkFont(size=13))
            val = settings.get(key, "") or ""
            if val:
                entry.insert(0, str(val))
            entry.grid(row=row * 2 + 1, column=col, sticky="ew",
                       columnspan=colspan, padx=5, pady=(0, 5))
            self.entries[key] = entry

        ctk.CTkButton(
            company_card, text="💾 Salvar Informações",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=38, corner_radius=10,
            command=self._save_company,
        ).pack(padx=15, pady=(0, 15), anchor="e")

        # === Configurações de Produto (Dobra) ===
        dobra_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                   border_width=1, border_color=COLORS["border"])
        dobra_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            dobra_card, text="✂️ Configuração de Dobra",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            dobra_card,
            text="Valor adicional cobrado por metro quando o produto tem dobra.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(padx=15, pady=(0, 8), anchor="w")

        dobra_inner = ctk.CTkFrame(dobra_card, fg_color="transparent")
        dobra_inner.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            dobra_inner, text="Valor da Dobra (R$/metro):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        self.dobra_entry = ctk.CTkEntry(
            dobra_inner, width=100, height=35,
            font=ctk.CTkFont(size=13),
            placeholder_text="5.00",
        )
        dobra_val = settings.get("dobra_value", 5.0) or 5.0
        self.dobra_entry.insert(0, str(float(dobra_val)))
        self.dobra_entry.pack(side="left", padx=(10, 10))

        ctk.CTkButton(
            dobra_inner, text="💾 Salvar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=35, width=100, corner_radius=8,
            command=self._save_dobra,
        ).pack(side="left")

        # === Aparência ===
        theme_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                   border_width=1, border_color=COLORS["border"])
        theme_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            theme_card, text="🎨 Aparência",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 10), anchor="w")

        theme_inner = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_inner.pack(fill="x", padx=15, pady=(0, 15))

        current_theme_text = "Tema Escuro" if self.app.current_theme == "light" else "Tema Claro"
        current_icon = "🌙" if self.app.current_theme == "light" else "☀️"
        
        ctk.CTkButton(
            theme_inner,
            text=f"{current_icon} Alternar para {current_theme_text}",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color="#1d4ed8",
            height=38,
            corner_radius=10,
            command=self.app.toggle_theme,
        ).pack(fill="x")

        # === Informações do Sistema ===
        sys_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
        sys_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            sys_card, text="ℹ️ Informações do Sistema",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 10), anchor="w")

        info_items = [
            ("Versão", "2.0.0"),
            ("Framework", "CustomTkinter 5.x"),
            ("Banco de Dados", "SQLite Local"),
            ("Plataforma", "Desktop (Windows)"),
            ("Arquivo DB", db.get_db_path()),
        ]
        for label, value in info_items:
            row_frame = ctk.CTkFrame(sys_card, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(
                row_frame, text=f"{label}:", font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text"],
            ).pack(side="left")
            ctk.CTkLabel(
                row_frame, text=value, font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"],
            ).pack(side="left", padx=8)

        ctk.CTkFrame(sys_card, height=15, fg_color="transparent").pack()

        # === Gestão de Dados ===
        data_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                  border_width=1, border_color=COLORS["border"])
        data_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            data_card, text="🗄️ Gestão de Dados",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 10), anchor="w")

        btn_frame = ctk.CTkFrame(data_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="📦 Backup do Banco",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=38, corner_radius=10, width=180,
            command=self._backup_db,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🗑️ Limpar Todos os Dados",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["error"], hover_color="#dc2626",
            height=38, corner_radius=10, width=200,
            command=self._confirm_clear_data,
        ).pack(side="right", padx=5)

    def _save_company(self):
        try:
            data = {}
            for key, entry in self.entries.items():
                data[key] = entry.get().strip()
            db.update_settings(**data)
            self.app.show_toast("Configurações salvas!", "success")
            self.app.refresh_sidebar_company()
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")

    def _save_dobra(self):
        try:
            val = float(self.dobra_entry.get() or 5.0)
            if val < 0:
                self.app.show_toast("Valor da dobra não pode ser negativo.", "error")
                return
            db.update_settings(dobra_value=val)
            self.app.show_toast(f"Valor da dobra atualizado para R$ {val:.2f}/m!", "success")
        except ValueError:
            self.app.show_toast("Valor inválido. Use um número (ex: 5.00).", "error")
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")

    def _backup_db(self):
        try:
            db_path = db.get_db_path()
            if os.path.exists(db_path):
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
                os.makedirs(backup_dir, exist_ok=True)

                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"calhagest_backup_{timestamp}.db")
                shutil.copy2(db_path, backup_path)
                self.app.show_toast(f"Backup criado: {os.path.basename(backup_path)}", "success")
            else:
                self.app.show_toast("Banco de dados não encontrado.", "error")
        except Exception as e:
            self.app.show_toast(f"Erro no backup: {e}", "error")

    def _confirm_clear_data(self):
        ConfirmDialog(
            self.app,
            "Limpar Dados",
            "ATENÇÃO: Isso apagará TODOS os dados (produtos, orçamentos, estoque, instalações). Deseja continuar?",
            self._clear_all_data,
        )

    def _clear_all_data(self):
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            tables = ["quote_items", "installations", "quotes", "products", "inventory"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()
            conn.close()
            self.app.show_toast("Todos os dados foram limpos.", "success")
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")
