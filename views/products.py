# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Produtos
CRUD completo de produtos com pesquisa, filtro, tipos dinâmicos e materiais vinculados.
"""

import customtkinter as ctk
from database import db
from components.cards import (
    COLORS, StatusBadge, create_header, create_search_bar
)
from components.dialogs import ConfirmDialog, FormDialog, format_currency


def _get_product_types_map():
    """Retorna mapa de tipos dinâmico do banco."""
    types = db.get_all_product_types()
    return {t["key"]: t["label"] for t in types}


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
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        left = ctk.CTkFrame(header_frame, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left, text="Produtos",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Gerencie seu catálogo de produtos",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="  + Novo Tipo  ",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["warning"], hover_color="#d97706",
            height=36, corner_radius=10,
            command=self._open_add_type_dialog,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="  + Novo Produto  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=38, corner_radius=10,
            command=self._open_add_dialog,
        ).pack(side="left")

        # Barra de pesquisa + filtro
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        search_frame, self.search_entry = create_search_bar(
            filter_frame, "Pesquisar produto...", self._on_search
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Filtro por tipo (dinâmico)
        self._build_type_filter(filter_frame)

        # Lista de produtos (scrollable)
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self._load_products()

    def _build_type_filter(self, parent):
        """Constrói o filtro de tipos dinâmico."""
        types_map = _get_product_types_map()
        filter_values = ["Todos"] + list(types_map.values())
        self._type_key_map = {"Todos": ""}
        for k, v in types_map.items():
            self._type_key_map[v] = k

        self.filter_var = ctk.StringVar(value="Todos")
        self.type_seg = ctk.CTkSegmentedButton(
            parent,
            values=filter_values,
            variable=self.filter_var,
            command=self._on_filter,
            font=ctk.CTkFont(size=12),
            height=38,
        )
        self.type_seg.pack(side="right")

    def _on_search(self, text):
        self.search_text = text
        self._load_products()

    def _on_filter(self, value):
        self.type_filter = self._type_key_map.get(value, "")
        self._load_products()

    def _load_products(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        products = db.get_all_products(search=self.search_text, type_filter=self.type_filter)
        types_map = _get_product_types_map()

        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(products)} produto(s) encontrado(s)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"], anchor="w",
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
            self._create_product_card(product, types_map)

    def _create_product_card(self, product, types_map):
        card = ctk.CTkFrame(
            self.list_frame, fg_color=COLORS["card"],
            corner_radius=10, border_width=1, border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=4)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        name_frame = ctk.CTkFrame(left, fg_color="transparent")
        name_frame.pack(anchor="w")

        ctk.CTkLabel(
            name_frame, text=product["name"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        type_text = types_map.get(product["type"], product["type"])
        ctk.CTkLabel(
            name_frame, text=f"  {type_text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
            corner_radius=4,
        ).pack(side="left", padx=(8, 0))

        # Mostrar materiais vinculados
        materials = db.get_product_materials(product["id"])
        if materials:
            ctk.CTkLabel(
                name_frame, text=f"  📦 {len(materials)}  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=COLORS["success_light"], text_color=COLORS["success"],
                corner_radius=4,
            ).pack(side="left", padx=(5, 0))

        details = f"Medida: {product['measure']}cm  •  Preço: {format_currency(product['price_per_meter'])}/m"
        if product.get("cost") and product["cost"] > 0:
            details += f"  •  Custo: {format_currency(product['cost'])}/m"
        if product.get("has_dobra"):
            dobra_val = db.get_dobra_value()
            details += f"  •  Dobra: +{format_currency(dobra_val)}/m"
        ctk.CTkLabel(
            left, text=details,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        if materials:
            mat_text = "Materiais: " + ", ".join(
                f"{m['inventory_name']} ({m['quantity_per_unit']} por {m['unit_type']})"
                for m in materials
            )
            ctk.CTkLabel(
                left, text=mat_text,
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"], anchor="w",
            ).pack(anchor="w", pady=(2, 0))

        # Botões
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right")

        # Dobra toggle
        has_dobra = bool(product.get("has_dobra", 0))
        dobra_text = "Com" if has_dobra else "Sem"
        dobra_fg = COLORS["success"] if has_dobra else COLORS["error"]
        dobra_hover = COLORS.get("success_hover", "#16a34a") if has_dobra else COLORS.get("error_hover", "#dc2626")

        ctk.CTkButton(
            right, text=f"✂ {dobra_text}", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=dobra_fg, hover_color=dobra_hover,
            text_color="white",
            width=70, height=32, corner_radius=8,
            command=lambda p=product: self._toggle_dobra(p),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            right, text="📦 Material", font=ctk.CTkFont(size=11),
            fg_color=COLORS["success_light"], text_color=COLORS["success"],
            hover_color=COLORS["success_hover_light"],
            width=90, height=32, corner_radius=8,
            command=lambda p=product: self._open_materials_dialog(p),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            right, text="✏️ Editar", font=ctk.CTkFont(size=12),
            fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
            hover_color=COLORS["primary_hover_light"],
            width=80, height=32, corner_radius=8,
            command=lambda p=product: self._open_edit_dialog(p),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            right, text="🗑️", font=ctk.CTkFont(size=12),
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=40, height=32, corner_radius=8,
            command=lambda p=product: self._confirm_delete(p),
        ).pack(side="left", padx=4)

    def _toggle_dobra(self, product):
        """Alterna o estado de dobra do produto."""
        new_val = 0 if product.get("has_dobra", 0) else 1
        db.update_product(product["id"], has_dobra=new_val)
        status = "ativada" if new_val else "desativada"
        self.app.show_toast(f"Dobra {status} para {product['name']}.", "success")
        self._load_products()

    # ========== Tipos de Produto ==========

    def _open_add_type_dialog(self):
        """Dialog para adicionar/gerenciar tipos de produto."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Gerenciar Tipos de Produto")
        dialog.geometry("450x500")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 450) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog, text="Tipos de Produto",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=20, pady=(15, 5))

        ctk.CTkLabel(
            dialog, text="Adicione ou remova tipos de produto",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(padx=20, pady=(0, 10))

        # Form para novo tipo
        add_frame = ctk.CTkFrame(dialog, fg_color=COLORS["card"], corner_radius=10,
                                  border_width=1, border_color=COLORS["border"])
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        add_inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(add_inner, text="Nome do Tipo:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).pack(anchor="w")

        entry_frame = ctk.CTkFrame(add_inner, fg_color="transparent")
        entry_frame.pack(fill="x", pady=(4, 0))

        type_entry = ctk.CTkEntry(entry_frame, height=35, font=ctk.CTkFont(size=13),
                                   placeholder_text="Ex: Coifa, Calha Americana...")
        type_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def add_type():
            label = type_entry.get().strip()
            if not label:
                self.app.show_toast("Nome do tipo é obrigatório.", "error")
                return
            key = label.lower().replace(" ", "_")
            try:
                db.create_product_type(key, label)
                self.app.show_toast(f"Tipo '{label}' adicionado!", "success")
                type_entry.delete(0, "end")
                refresh_types_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            entry_frame, text="+ Adicionar", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=35, width=100, corner_radius=8,
            command=add_type,
        ).pack(side="right")

        # Lista de tipos existentes
        types_list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        types_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def refresh_types_list():
            for w in types_list_frame.winfo_children():
                w.destroy()
            types = db.get_all_product_types()
            for t in types:
                row = ctk.CTkFrame(types_list_frame, fg_color=COLORS["card"],
                                    corner_radius=8, border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)

                ctk.CTkLabel(
                    inner, text=t["label"],
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS["text"],
                ).pack(side="left")

                ctk.CTkLabel(
                    inner, text=f"({t['key']})",
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"],
                ).pack(side="left", padx=(8, 0))

                ctk.CTkButton(
                    inner, text="✕", width=28, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda tid=t["id"]: delete_type(tid),
                ).pack(side="right")

        def delete_type(tid):
            db.delete_product_type(tid)
            self.app.show_toast("Tipo removido.", "success")
            refresh_types_list()

        refresh_types_list()

        ctk.CTkButton(
            dialog, text="Fechar", font=ctk.CTkFont(size=13),
            fg_color="#e2e8f0", text_color=COLORS["text"],
            hover_color="#cbd5e1", height=36,
            command=lambda: self._close_type_dialog(dialog),
        ).pack(padx=20, pady=(0, 15), fill="x")

    def _close_type_dialog(self, dialog):
        dialog.destroy()
        # Rebuild view para atualizar filtros
        for w in self.winfo_children():
            w.destroy()
        self._build()

    # ========== Materiais do Produto ==========

    def _open_materials_dialog(self, product):
        """Dialog para vincular materiais do estoque a um produto."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Materiais - {product['name']}")
        dialog.geometry("550x500")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 550) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog, text=f"Materiais de: {product['name']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=20, pady=(15, 3))

        ctk.CTkLabel(
            dialog,
            text="Vincule materiais do estoque que serão consumidos ao aprovar um orçamento",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=500,
        ).pack(padx=20, pady=(0, 10))

        # Formulário para adicionar material
        add_frame = ctk.CTkFrame(dialog, fg_color=COLORS["card"], corner_radius=10,
                                  border_width=1, border_color=COLORS["border"])
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            add_frame, text="Adicionar Material",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=12, pady=(10, 5), anchor="w")

        add_inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_inner.pack(fill="x", padx=12, pady=(0, 10))
        add_inner.grid_columnconfigure(0, weight=3)
        add_inner.grid_columnconfigure(1, weight=1)
        add_inner.grid_columnconfigure(2, weight=1)

        inventory_items = db.get_all_inventory()
        inv_names = [f"{i['name']} ({i['quantity']:.0f} {i['unit']})" for i in inventory_items]
        inv_map = {name: i for name, i in zip(inv_names, inventory_items)}

        inv_var = ctk.StringVar(value=inv_names[0] if inv_names else "")
        if inv_names:
            ctk.CTkOptionMenu(
                add_inner, values=inv_names, variable=inv_var,
                font=ctk.CTkFont(size=11), height=33,
            ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        else:
            ctk.CTkLabel(
                add_inner, text="Nenhum material no estoque",
                font=ctk.CTkFont(size=11), text_color=COLORS["error"],
            ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        qty_entry = ctk.CTkEntry(add_inner, width=70, height=33, font=ctk.CTkFont(size=12),
                                  placeholder_text="Qtd")
        qty_entry.grid(row=0, column=1, padx=(0, 5))
        qty_entry.insert(0, "1")

        unit_var = ctk.StringVar(value="metro")
        ctk.CTkOptionMenu(
            add_inner, values=["metro", "cm", "unidade"], variable=unit_var,
            font=ctk.CTkFont(size=11), height=33, width=90,
        ).grid(row=0, column=2, padx=(0, 5))

        def add_material():
            sel = inv_var.get()
            inv_item = inv_map.get(sel)
            if not inv_item:
                self.app.show_toast("Selecione um material do estoque.", "warning")
                return
            try:
                qty = float(qty_entry.get() or 1)
                if qty <= 0:
                    self.app.show_toast("Quantidade deve ser maior que zero.", "warning")
                    return
                db.add_product_material(
                    product["id"], inv_item["id"], qty, unit_var.get()
                )
                self.app.show_toast("Material vinculado!", "success")
                refresh_materials_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            add_inner, text="+", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=33, width=40, corner_radius=8,
            command=add_material,
        ).grid(row=0, column=3, padx=(5, 0))

        # Lista de materiais vinculados
        materials_list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        materials_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        unit_labels = {"metro": "por metro", "cm": "por cm", "unidade": "por unidade"}

        def refresh_materials_list():
            for w in materials_list_frame.winfo_children():
                w.destroy()
            materials = db.get_product_materials(product["id"])

            if not materials:
                ctk.CTkLabel(
                    materials_list_frame,
                    text="Nenhum material vinculado.\nAdicione materiais para que o estoque seja atualizado automaticamente.",
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS["text_secondary"],
                    justify="center",
                ).pack(pady=20)
                return

            for mat in materials:
                row = ctk.CTkFrame(materials_list_frame, fg_color=COLORS["card"],
                                    corner_radius=8, border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=8)

                ctk.CTkLabel(
                    inner, text=mat["inventory_name"],
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS["text"],
                ).pack(side="left")

                unit_label = unit_labels.get(mat["unit_type"], mat["unit_type"])
                ctk.CTkLabel(
                    inner,
                    text=f"  {mat['quantity_per_unit']} {unit_label}  ",
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["primary_light"],
                    text_color=COLORS["primary"],
                    corner_radius=4,
                ).pack(side="left", padx=(8, 0))

                ctk.CTkLabel(
                    inner,
                    text=f"  Estoque: {mat['inventory_quantity']:.0f} {mat['inventory_unit']}  ",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS["text_secondary"],
                ).pack(side="left", padx=(5, 0))

                ctk.CTkButton(
                    inner, text="✕", width=28, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda mid=mat["id"]: remove_material(mid),
                ).pack(side="right")

        def remove_material(mid):
            db.remove_product_material(mid)
            self.app.show_toast("Material removido.", "success")
            refresh_materials_list()

        refresh_materials_list()

        ctk.CTkButton(
            dialog, text="Fechar", font=ctk.CTkFont(size=13),
            fg_color="#e2e8f0", text_color=COLORS["text"],
            hover_color="#cbd5e1", height=36,
            command=lambda: (dialog.destroy(), self._load_products()),
        ).pack(padx=20, pady=(0, 15), fill="x")

    # ========== CRUD de Produtos ==========

    def _get_form_fields(self):
        types = db.get_all_product_types()
        type_keys = [t["key"] for t in types]
        return [
            {"key": "name", "label": "Nome do Produto", "type": "entry", "required": True},
            {"key": "type", "label": "Tipo", "type": "option",
             "options": type_keys, "required": True},
            {"key": "measure", "label": "Medida (cm)", "type": "number", "required": True},
            {"key": "price_per_meter", "label": "Preço por metro (R$)", "type": "number", "required": True},
            {"key": "cost", "label": "Custo por metro (R$)", "type": "number"},
            {"key": "has_dobra", "label": "Dobra", "type": "option", "options": ["0", "1"],
             "option_labels": {"0": "Sem Dobra", "1": "Com Dobra"}},
            {"key": "description", "label": "Descrição", "type": "text"},
        ]

    def _open_add_dialog(self):
        FormDialog(
            self.app, "Novo Produto",
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
            has_dobra = int(data.get("has_dobra", 0) or 0)
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
            # Atualizar dobra separadamente
            products = db.get_all_products(search=name)
            if products:
                db.update_product(products[-1]["id"], has_dobra=has_dobra)
            self.app.show_toast("Produto criado com sucesso!", "success")
            self._load_products()
        except Exception as e:
            self.app.show_toast(f"Erro ao criar produto: {e}", "error")

    def _open_edit_dialog(self, product):
        FormDialog(
            self.app, "Editar Produto",
            self._get_form_fields(),
            lambda data, pid=product["id"]: self._save_edit_product(pid, data),
            initial_data=product,
        )

    def _save_edit_product(self, product_id, data):
        try:
            price = float(data.get("price_per_meter", 0) or 0)
            measure = float(data.get("measure", 0) or 0)
            cost = float(data.get("cost", 0) or 0)
            has_dobra = int(data.get("has_dobra", 0) or 0)
            db.update_product(
                product_id,
                name=data.get("name", ""),
                type=data.get("type", "calha"),
                measure=measure,
                price_per_meter=price,
                cost=cost,
                has_dobra=has_dobra,
                description=data.get("description", ""),
            )
            self.app.show_toast("Produto atualizado!", "success")
            self._load_products()
        except Exception as e:
            self.app.show_toast(f"Erro: {e}", "error")

    def _confirm_delete(self, product):
        ConfirmDialog(
            self.app, "Excluir Produto",
            f"Tem certeza que deseja excluir '{product['name']}'?",
            lambda pid=product["id"]: self._delete_product(pid),
        )

    def _delete_product(self, product_id):
        db.delete_product(product_id)
        self.app.show_toast("Produto excluído.", "success")
        self._load_products()
