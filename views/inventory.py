# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Estoque/Inventário
Controle de materiais com alertas de estoque baixo.
"""

import customtkinter as ctk
from database import db
from components.cards import create_header, create_search_bar
from theme import get_color, COLORS
from components.dialogs import ConfirmDialog, FormDialog, parse_decimal


class InventoryView(ctk.CTkFrame):
    """View de gestão de estoque."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_text = ""
        self.type_filter = ""
        self._build()

    def _build(self):
        # Cabeçalho
        header = create_header(
            self, "Estoque", "Controle de materiais",
            action_text="Novo Material", action_command=self._open_add_dialog
        )
        header.pack(fill="x", pady=(0, 15))

        # Pesquisa
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        search_frame, self.search_entry = create_search_bar(
            filter_frame, "Pesquisar material...", self._on_search
        )
        search_frame.pack(side="left", fill="x", expand=True)

        # Alerta de estoque baixo
        low_stock = db.get_low_stock_items()
        if low_stock:
            alert = ctk.CTkFrame(self, fg_color=COLORS["error_lighter"], corner_radius=8)
            alert.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                alert,
                text=f"⚠️ {len(low_stock)} item(ns) com estoque abaixo do mínimo!",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["error"],
            ).pack(padx=15, pady=10)

        # Lista
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self._load_items()

    def _on_search(self, text):
        self.search_text = text
        self._load_items()

    def _load_items(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        items = db.get_all_inventory(search=self.search_text, type_filter=self.type_filter)

        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(items)} material(is)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        if not items:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhum material cadastrado.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
            ).pack(pady=40)
            return

        for item in items:
            self._create_item_card(item)

    def _create_item_card(self, item):
        is_low = item["quantity"] < item.get("min_stock", 0) and item.get("min_stock", 0) > 0
        border_color = COLORS["error"] if is_low else COLORS["border"]

        card = ctk.CTkFrame(
            self.list_frame,
            fg_color=COLORS["card"],
            corner_radius=10,
            border_width=2 if is_low else 1,
            border_color=border_color,
        )
        card.pack(fill="x", pady=4)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Info
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        name_row = ctk.CTkFrame(left, fg_color="transparent")
        name_row.pack(anchor="w")

        ctk.CTkLabel(
            name_row,
            text=item["name"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        ctk.CTkLabel(
            name_row,
            text=f"  {item['type']}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS["primary_light"],
            text_color=COLORS["primary"],
            corner_radius=4,
        ).pack(side="left", padx=(8, 0))

        if is_low:
            ctk.CTkLabel(
                name_row,
                text="  ⚠️ Baixo  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=COLORS["error_light"],
                text_color=COLORS["error"],
                corner_radius=4,
            ).pack(side="left", padx=(5, 0))

        details = f"Quantidade: {item['quantity']:.0f} {item['unit']}  •  Mínimo: {item.get('min_stock', 0):.0f}"
        ctk.CTkLabel(
            left,
            text=details,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        # Botões
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right, text="+ Entrada", font=ctk.CTkFont(size=11),
            fg_color=COLORS["success_light"], text_color=COLORS["success"],
            hover_color=COLORS["success_hover_light"],
            width=80, height=30, corner_radius=8,
            command=lambda i=item: self._adjust_stock(i, "add"),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="- Saída", font=ctk.CTkFont(size=11),
            fg_color=COLORS["warning_light"], text_color=COLORS["warning"],
            hover_color=COLORS["warning_hover_light"],
            width=80, height=30, corner_radius=8,
            command=lambda i=item: self._adjust_stock(i, "remove"),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="🗑️", font=ctk.CTkFont(size=11),
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=36, height=30, corner_radius=8,
            command=lambda i=item: self._confirm_delete(i),
        ).pack(side="left", padx=3)

    def _open_add_dialog(self):
        fields = [
            {"key": "name", "label": "Nome do Material", "type": "entry", "required": True},
            {"key": "type", "label": "Tipo", "type": "entry", "required": True},
            {"key": "quantity", "label": "Quantidade Inicial", "type": "number", "required": True},
            {"key": "unit", "label": "Unidade", "type": "option",
             "options": ["unidades", "tubos", "rolos", "peças", "metros", "kg"]},
            {"key": "min_stock", "label": "Estoque Mínimo", "type": "number"},
        ]
        FormDialog(self.app, "Novo Material", fields, self._save_new_item)

    def _save_new_item(self, data):
        name = data.get("name", "").strip()
        if not name:
            self.app.show_toast("Nome é obrigatório.", "error")
            return
        try:
            qty = float(data.get("quantity", 0) or 0)
            min_stock = float(data.get("min_stock", 0) or 0)
            db.create_inventory_item(
                name=name,
                type=data.get("type", "").strip() or "geral",
                quantity=qty,
                unit=data.get("unit", "unidades"),
                min_stock=min_stock,
            )
            self.app.show_toast("Material adicionado!", "success")
            self._load_items()
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")

    def _adjust_stock(self, item, operation):
        """Abre diálogo para ajustar estoque."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Entrada de Estoque" if operation == "add" else "Saída de Estoque")
        dialog.geometry("350x180")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 350) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text=f"{'Adicionar' if operation == 'add' else 'Remover'} de: {item['name']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=20, pady=(20, 5))

        ctk.CTkLabel(
            dialog,
            text=f"Atual: {item['quantity']:.0f} {item['unit']}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(padx=20, pady=(0, 10))

        qty_entry = ctk.CTkEntry(dialog, height=35, font=ctk.CTkFont(size=13),
                                  placeholder_text="Quantidade")
        qty_entry.pack(padx=20, fill="x")
        qty_entry.focus()

        def confirm():
            try:
                qty = parse_decimal(qty_entry.get() or "0")
                if qty <= 0:
                    return
                db.update_inventory_quantity(item["id"], qty, operation)
                dialog.destroy()
                self.app.show_toast(
                    f"Estoque {'atualizado' if operation == 'add' else 'reduzido'}!",
                    "success"
                )
                self._load_items()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            dialog, text="Confirmar", font=ctk.CTkFont(size=13),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=36, command=confirm,
        ).pack(padx=20, pady=15, fill="x")

    def _confirm_delete(self, item):
        ConfirmDialog(
            self.app, "Excluir Material",
            f"Excluir '{item['name']}' do estoque?",
            lambda iid=item["id"]: self._delete_item(iid),
        )

    def _delete_item(self, item_id):
        db.delete_inventory_item(item_id)
        self.app.show_toast("Material excluído.", "success")
        self._load_items()
