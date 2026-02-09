# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Produtos
CRUD completo de produtos com pesquisa e filtro.
"""

import customtkinter as ctk
from database import db
from components.cards import (
    COLORS, StatusBadge, create_header, create_search_bar
)
from components.dialogs import ConfirmDialog, FormDialog, format_currency


PRODUCT_TYPES = {
    "calha": "Calha",
    "rufo": "Rufo",
    "pingadeira": "Pingadeira",
}


class ProductsView(ctk.CTkFrame):
    """View de gestão de produtos."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_text = ""
        self.type_filter = ""
        self._build()

    def _build(self):
        # Cabeçalho
        header = create_header(
            self, "Produtos", "Gerencie seu catálogo de produtos",
            action_text="Novo Produto", action_command=self._open_add_dialog
        )
        header.pack(fill="x", pady=(0, 15))

        # Barra de pesquisa + filtro
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        search_frame, self.search_entry = create_search_bar(
            filter_frame, "Pesquisar produto...", self._on_search
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Filtro por tipo
        filter_values = ["Todos", "Calha", "Rufo", "Pingadeira"]
        self.filter_var = ctk.StringVar(value="Todos")
        ctk.CTkSegmentedButton(
            filter_frame,
            values=filter_values,
            variable=self.filter_var,
            command=self._on_filter,
            font=ctk.CTkFont(size=12),
            height=38,
        ).pack(side="right")

        # Lista de produtos (scrollable)
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent"
        )
        self.list_frame.pack(fill="both", expand=True)

        self._load_products()

    def _on_search(self, text):
        self.search_text = text
        self._load_products()

    def _on_filter(self, value):
        type_map = {"Todos": "", "Calha": "calha", "Rufo": "rufo", "Pingadeira": "pingadeira"}
        self.type_filter = type_map.get(value, "")
        self._load_products()

    def _load_products(self):
        # Limpar lista
        for w in self.list_frame.winfo_children():
            w.destroy()

        products = db.get_all_products(search=self.search_text, type_filter=self.type_filter)

        # Contador
        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(products)} produto(s) encontrado(s)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        if not products:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhum produto encontrado.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
            ).pack(pady=40)
            return

        for product in products:
            self._create_product_card(product)

    def _create_product_card(self, product):
        card = ctk.CTkFrame(
            self.list_frame,
            fg_color=COLORS["card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=4)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        # Esquerda: info do produto
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        name_frame = ctk.CTkFrame(left, fg_color="transparent")
        name_frame.pack(anchor="w")

        ctk.CTkLabel(
            name_frame,
            text=product["name"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        type_text = PRODUCT_TYPES.get(product["type"], product["type"])
        ctk.CTkLabel(
            name_frame,
            text=f"  {type_text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS["primary_light"],
            text_color=COLORS["primary"],
            corner_radius=4,
        ).pack(side="left", padx=(8, 0))

        details = f"Medida: {product['measure']}cm  •  Preço: {format_currency(product['price_per_meter'])}/m"
        if product.get("cost") and product["cost"] > 0:
            details += f"  •  Custo: {format_currency(product['cost'])}/m"
        ctk.CTkLabel(
            left,
            text=details,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        # Direita: botões
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right,
            text="✏️ Editar",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["primary_light"],
            text_color=COLORS["primary"],
            hover_color=COLORS["primary_hover_light"],
            width=80,
            height=32,
            corner_radius=8,
            command=lambda p=product: self._open_edit_dialog(p),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            right,
            text="🗑️",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["error_light"],
            text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=40,
            height=32,
            corner_radius=8,
            command=lambda p=product: self._confirm_delete(p),
        ).pack(side="left", padx=4)

    def _get_form_fields(self):
        return [
            {"key": "name", "label": "Nome do Produto", "type": "entry", "required": True},
            {"key": "type", "label": "Tipo", "type": "option",
             "options": ["calha", "rufo", "pingadeira"], "required": True},
            {"key": "measure", "label": "Medida (cm)", "type": "number", "required": True},
            {"key": "price_per_meter", "label": "Preço por metro (R$)", "type": "number", "required": True},
            {"key": "cost", "label": "Custo por metro (R$)", "type": "number"},
            {"key": "description", "label": "Descrição", "type": "text"},
        ]

    def _open_add_dialog(self):
        FormDialog(
            self.app,
            "Novo Produto",
            self._get_form_fields(),
            self._save_new_product,
        )

    def _save_new_product(self, data):
        name = data.get("name", "").strip()
        if not name:
            self.app.show_toast("Nome do produto é obrigatório.", "error")
            return
        try:
            price = float(data.get("price_per_meter", 0) or 0)
            measure = float(data.get("measure", 0) or 0)
            cost = float(data.get("cost", 0) or 0)
            if price <= 0 or measure <= 0:
                self.app.show_toast("Preço e medida devem ser maiores que zero.", "error")
                return
            db.create_product(
                name=name,
                type=data.get("type", "calha"),
                measure=measure,
                price_per_meter=price,
                cost=cost,
                description=data.get("description", ""),
            )
            self.app.show_toast("Produto criado com sucesso!", "success")
            self._load_products()
        except Exception as e:
            self.app.show_toast(f"Erro ao criar produto: {e}", "error")

    def _open_edit_dialog(self, product):
        FormDialog(
            self.app,
            "Editar Produto",
            self._get_form_fields(),
            lambda data, pid=product["id"]: self._save_edit_product(pid, data),
            initial_data=product,
        )

    def _save_edit_product(self, product_id, data):
        try:
            price = float(data.get("price_per_meter", 0) or 0)
            measure = float(data.get("measure", 0) or 0)
            cost = float(data.get("cost", 0) or 0)
            db.update_product(
                product_id,
                name=data.get("name", ""),
                type=data.get("type", "calha"),
                measure=measure,
                price_per_meter=price,
                cost=cost,
                description=data.get("description", ""),
            )
            self.app.show_toast("Produto atualizado!", "success")
            self._load_products()
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")

    def _confirm_delete(self, product):
        ConfirmDialog(
            self.app,
            "Excluir Produto",
            f"Tem certeza que deseja excluir '{product['name']}'?",
            lambda pid=product["id"]: self._delete_product(pid),
        )

    def _delete_product(self, product_id):
        db.delete_product(product_id)
        self.app.show_toast("Produto excluído.", "success")
        self._load_products()
