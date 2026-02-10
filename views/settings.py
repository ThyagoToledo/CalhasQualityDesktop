# -*- coding: utf-8 -*-
"""
CalhaGest - Configurações do Sistema
Informações da empresa, backup e gestão de dados.
"""

import customtkinter as ctk
import shutil
import os
import subprocess
from tkinter import filedialog
from pathlib import Path
from database import db
from services.backup import (
    get_backup_dir, set_backup_dir, get_default_backup_dir,
    save_backup, load_backup, restore_from_backup, get_backup_filepath,
)
from components.cards import create_header
from theme import get_color, COLORS
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
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
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
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=35, width=100, corner_radius=8,
            command=self._save_dobra,
        ).pack(side="left")

        # === Backup Automático ===
        backup_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                    border_width=1, border_color=COLORS["border"])
        backup_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            backup_card, text="💾 Backup Automático",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=15, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            backup_card,
            text="O backup é salvo automaticamente em JSON a cada alteração.\n"
                 "Ao atualizar o app, seus dados são preservados neste arquivo.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            justify="left",
        ).pack(padx=15, pady=(0, 10), anchor="w")

        # Pasta de backup
        dir_frame = ctk.CTkFrame(backup_card, fg_color="transparent")
        dir_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(
            dir_frame, text="Pasta de Backup:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        path_row = ctk.CTkFrame(backup_card, fg_color="transparent")
        path_row.pack(fill="x", padx=15, pady=(0, 10))
        path_row.grid_columnconfigure(0, weight=1)

        self.backup_path_entry = ctk.CTkEntry(
            path_row, height=35, font=ctk.CTkFont(size=12),
        )
        current_backup_dir = get_backup_dir()
        self.backup_path_entry.insert(0, current_backup_dir)
        self.backup_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            path_row, text="📂 Alterar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=35, width=100, corner_radius=8,
            command=self._choose_backup_folder,
        ).grid(row=0, column=1)

        # Arquivo de backup atual
        backup_file = get_backup_filepath()
        file_exists = os.path.exists(backup_file)
        status_text = f"✅ Arquivo: {backup_file}" if file_exists else "⚠️ Nenhum backup encontrado ainda."

        self.backup_status_label = ctk.CTkLabel(
            backup_card, text=status_text,
            font=ctk.CTkFont(size=11),
            text_color=get_color("success") if file_exists else get_color("text_secondary"),
            justify="left",
        )
        self.backup_status_label.pack(padx=15, pady=(0, 10), anchor="w")

        # Botões de ação
        backup_btn_frame = ctk.CTkFrame(backup_card, fg_color="transparent")
        backup_btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            backup_btn_frame, text="📦 Fazer Backup Agora",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=38, corner_radius=10, width=200,
            command=self._manual_backup,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            backup_btn_frame, text="📥 Restaurar Backup",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            height=38, corner_radius=10, width=200,
            command=self._confirm_restore,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            backup_btn_frame, text="📂 Restaurar de Arquivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("purple"), hover_color=get_color("purple_hover"),
            height=38, corner_radius=10, width=200,
            command=self._restore_from_file,
        ).pack(side="left")

        # Segunda linha de botões
        backup_btn_frame2 = ctk.CTkFrame(backup_card, fg_color="transparent")
        backup_btn_frame2.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            backup_btn_frame2, text="📂 Abrir Pasta do Backup",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("gray"), hover_color=get_color("gray_hover"),
            height=38, corner_radius=10, width=200,
            command=self._open_backup_folder,
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
            fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"),
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
            ("Versão", "2.1.0"),
            ("Framework", "CustomTkinter 5.x"),
            ("Banco de Dados", "SQLite Local"),
            ("Plataforma", "Desktop (Windows)"),
            ("Arquivo DB", db.get_db_path()),
            ("Backup", get_backup_filepath()),
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
            btn_frame, text="�️ Limpar Todos os Dados",
            font=ctk.CTkFont(size=13),
            fg_color=get_color("error"), hover_color=get_color("error_hover"),
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

    def _choose_backup_folder(self):
        """Abre diálogo para escolher pasta de backup."""
        folder = filedialog.askdirectory(
            title="Escolher pasta de backup",
            initialdir=get_backup_dir(),
        )
        if folder:
            set_backup_dir(folder)
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, folder)
            self.app.show_toast(f"Pasta de backup alterada!", "success")
            # Salvar backup na nova pasta imediatamente
            try:
                filepath = save_backup()
                self.backup_status_label.configure(
                    text=f"✅ Arquivo: {filepath}",
                    text_color=COLORS["success"],
                )
            except Exception:
                pass

    def _manual_backup(self):
        """Faz backup manual."""
        try:
            filepath = save_backup()
            self.backup_status_label.configure(
                text=f"✅ Arquivo: {filepath}",
                text_color=COLORS["success"],
            )
            self.app.show_toast("Backup salvo com sucesso!", "success")
        except Exception as e:
            self.app.show_toast(f"Erro no backup: {e}", "error")

    def _confirm_restore(self):
        """Confirma restauração do backup padrão."""
        backup_file = get_backup_filepath()
        if not os.path.exists(backup_file):
            self.app.show_toast("Nenhum arquivo de backup encontrado.", "error")
            return
        ConfirmDialog(
            self.app,
            "Restaurar Backup",
            f"Isso substituirá TODOS os dados atuais pelos dados do backup.\n\n"
            f"Arquivo: {backup_file}\n\nDeseja continuar?",
            self._do_restore,
        )

    def _do_restore(self):
        """Executa a restauração do backup padrão."""
        try:
            summary = restore_from_backup()
            total = sum(v for k, v in summary.items() if k != "settings")
            self.app.show_toast(
                f"Backup restaurado! {total} registros recuperados.", "success"
            )
            # Recarregar view
            self.app.current_view_name = None
            self.app.show_view("settings")
        except Exception as e:
            self.app.show_toast(f"Erro na restauração: {e}", "error")

    def _restore_from_file(self):
        """Restaura a partir de um arquivo JSON escolhido pelo usuário."""
        filepath = filedialog.askopenfilename(
            title="Escolher arquivo de backup",
            initialdir=get_backup_dir(),
            filetypes=[("JSON Backup", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not filepath:
            return
        ConfirmDialog(
            self.app,
            "Restaurar de Arquivo",
            f"Isso substituirá TODOS os dados atuais pelos dados do arquivo:\n\n"
            f"{filepath}\n\nDeseja continuar?",
            lambda: self._do_restore_file(filepath),
        )

    def _do_restore_file(self, filepath):
        """Executa restauração a partir de arquivo específico."""
        try:
            summary = restore_from_backup(filepath)
            total = sum(v for k, v in summary.items() if k != "settings")
            self.app.show_toast(
                f"Backup restaurado! {total} registros recuperados.", "success"
            )
            self.app.current_view_name = None
            self.app.show_view("settings")
        except Exception as e:
            self.app.show_toast(f"Erro na restauração: {e}", "error")

    def _open_backup_folder(self):
        """Abre a pasta de backup no explorador de arquivos."""
        try:
            backup_dir = get_backup_dir()
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            subprocess.Popen(["explorer", os.path.normpath(backup_dir)])
        except Exception as e:
            self.app.show_toast(f"Erro ao abrir pasta: {e}", "error")

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
