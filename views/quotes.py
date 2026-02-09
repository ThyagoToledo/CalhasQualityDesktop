# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Orçamentos
Criar, visualizar, editar orçamentos, gerar PDF e gerenciar status.
"""

import customtkinter as ctk
import os
import subprocess
from database import db
from components.cards import COLORS, StatusBadge, create_header, create_search_bar
from components.dialogs import ConfirmDialog, format_currency, format_date, DateEntry


STATUS_OPTIONS = ["Todos", "Rascunho", "Enviado", "Aprovado", "Concluído"]
STATUS_MAP = {
    "Todos": "", "Rascunho": "draft", "Enviado": "sent",
    "Aprovado": "approved", "Concluído": "completed",
}
STATUS_COLORS = {
    "draft": ("#9ca3af", "Rascunho"),
    "sent": ("#3b82f6", "Enviado"),
    "approved": ("#22c55e", "Aprovado"),
    "completed": ("#a855f7", "Concluído"),
}


class QuotesView(ctk.CTkFrame):
    """View de gestão de orçamentos."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_text = ""
        self.status_filter = ""
        self._build_list()

    def _build_list(self):
        """Constrói a view de listagem."""
        # Limpar
        for w in self.winfo_children():
            w.destroy()

        # Cabeçalho
        header = create_header(
            self, "Orçamentos", "Gerencie seus orçamentos",
            action_text="Novo Orçamento", action_command=self._open_create_form
        )
        header.pack(fill="x", pady=(0, 15))

        # Pesquisa + Filtro
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))

        search_frame, self.search_entry = create_search_bar(
            filter_frame, "Pesquisar cliente...", self._on_search
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.filter_var = ctk.StringVar(value="Todos")
        ctk.CTkSegmentedButton(
            filter_frame,
            values=STATUS_OPTIONS,
            variable=self.filter_var,
            command=self._on_filter,
            font=ctk.CTkFont(size=12),
            height=38,
        ).pack(side="right")

        # Lista
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self._load_quotes()

    def _on_search(self, text):
        self.search_text = text
        self._load_quotes()

    def _on_filter(self, value):
        self.status_filter = STATUS_MAP.get(value, "")
        self._load_quotes()

    def _load_quotes(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        quotes = db.get_all_quotes(search=self.search_text, status_filter=self.status_filter)

        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(quotes)} orçamento(s)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        if not quotes:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhum orçamento encontrado.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
            ).pack(pady=40)
            return

        for quote in quotes:
            self._create_quote_card(quote)

    def _create_quote_card(self, quote):
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

        # Info
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(anchor="w")

        ctk.CTkLabel(
            top_row,
            text=f"#{quote['id']:05d}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=f"  {quote['client_name']}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        StatusBadge(top_row, quote.get("status", "draft")).pack(side="left", padx=(10, 0))

        details = f"{format_date(quote.get('created_at', ''))}  •  {format_currency(quote.get('total', 0))}"
        if quote.get("profit") and quote["profit"] > 0:
            details += f"  •  Lucro: {format_currency(quote['profit'])}"
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
            right, text="👁️ Ver", font=ctk.CTkFont(size=12),
            fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
            hover_color=COLORS["primary_hover_light"],
            width=70, height=32, corner_radius=8,
            command=lambda q=quote: self._show_detail(q["id"]),
        ).pack(side="left", padx=3)

        status = quote.get("status", "draft")
        if status in ("draft", "sent"):
            ctk.CTkButton(
                right, text="✏️", font=ctk.CTkFont(size=12),
                fg_color=COLORS["warning_light"], text_color=COLORS["warning"],
                hover_color=COLORS["warning_hover_light"],
                width=36, height=32, corner_radius=8,
                command=lambda q=quote: self._open_edit_form(q["id"]),
            ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="📄 PDF", font=ctk.CTkFont(size=12),
            fg_color=COLORS["success_light"], text_color=COLORS["success"],
            hover_color=COLORS["success_hover_light"],
            width=70, height=32, corner_radius=8,
            command=lambda q=quote: self._generate_pdf(q["id"]),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="🗑️", font=ctk.CTkFont(size=12),
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=36, height=32, corner_radius=8,
            command=lambda q=quote: self._confirm_delete(q),
        ).pack(side="left", padx=3)

    # ========== Detalhes do Orçamento ==========

    def _show_detail(self, quote_id):
        quote = db.get_quote_by_id(quote_id)
        if not quote:
            self.app.show_toast("Orçamento não encontrado.", "error")
            return

        # Limpar e construir view de detalhes
        for w in self.winfo_children():
            w.destroy()

        # Header com botão de voltar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            header, text="← Voltar", font=ctk.CTkFont(size=13),
            fg_color="transparent", text_color=COLORS["primary"],
            hover_color=COLORS["border"], height=32, width=80,
            command=self._build_list,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"Orçamento #{quote['id']:05d}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=15)

        StatusBadge(header, quote.get("status", "draft")).pack(side="left")

        # Scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Ações de status
        action_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                     border_width=1, border_color=COLORS["border"])
        action_frame.pack(fill="x", pady=(0, 15))

        action_inner = ctk.CTkFrame(action_frame, fg_color="transparent")
        action_inner.pack(padx=15, pady=12)

        status = quote.get("status", "draft")
        transitions = {
            "draft": [("Enviar", "sent", COLORS["primary"])],
            "sent": [("Aprovar", "approved", COLORS["success"])],
            "approved": [("Completar", "completed", "#a855f7")],
        }

        for label, new_status, color in transitions.get(status, []):
            ctk.CTkButton(
                action_inner, text=label, font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=color, hover_color=color,
                height=36, corner_radius=8,
                command=lambda ns=new_status, qid=quote["id"]: self._change_status(qid, ns),
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_inner, text="📄 Gerar PDF", font=ctk.CTkFont(size=13),
            fg_color=COLORS["success"], hover_color="#059669",
            height=36, corner_radius=8,
            command=lambda: self._generate_pdf(quote["id"]),
        ).pack(side="left", padx=5)

        if status in ("draft", "sent"):
            ctk.CTkButton(
                action_inner, text="✏️ Editar", font=ctk.CTkFont(size=13),
                fg_color=COLORS["warning"], hover_color="#d97706",
                height=36, corner_radius=8,
                command=lambda: self._open_edit_form(quote["id"]),
            ).pack(side="left", padx=5)

        # Info do cliente
        client_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                    border_width=1, border_color=COLORS["border"])
        client_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            client_card, text="👤 Dados do Cliente",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
            anchor="w",
        ).pack(padx=15, pady=(12, 5), anchor="w")

        info_lines = [
            f"Nome: {quote.get('client_name', '-')}",
            f"Telefone: {quote.get('client_phone', '-') or '-'}",
            f"Endereço: {quote.get('client_address', '-') or '-'}",
            f"Data: {format_date(quote.get('created_at', ''))}",
        ]
        if quote.get("scheduled_date"):
            info_lines.append(f"Agendamento: {format_date(quote['scheduled_date'])}")

        for line in info_lines:
            ctk.CTkLabel(
                client_card, text=line, font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"], anchor="w",
            ).pack(padx=15, pady=1, anchor="w")

        ctk.CTkFrame(client_card, height=8, fg_color="transparent").pack()

        # Itens do orçamento
        items_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                   border_width=1, border_color=COLORS["border"])
        items_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            items_card, text="📦 Itens do Orçamento",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
            anchor="w",
        ).pack(padx=15, pady=(12, 5), anchor="w")

        items = quote.get("items", [])
        if items:
            # Cabeçalho da tabela
            table_header = ctk.CTkFrame(items_card, fg_color=COLORS["primary_lighter"],
                                         corner_radius=6)
            table_header.pack(fill="x", padx=12, pady=(5, 2))

            cols = [("Produto", 3), ("Medida", 1), ("Metros", 1), ("Preço/m", 1), ("Subtotal", 1)]
            for text, weight in cols:
                ctk.CTkLabel(
                    table_header, text=text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=COLORS["primary"],
                ).pack(side="left", expand=(weight > 1), fill="x", padx=5, pady=6)

            for item in items:
                row = ctk.CTkFrame(items_card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)

                vals = [
                    (item.get("product_name", "-"), 3),
                    (f"{item.get('measure', 0)}cm", 1),
                    (f"{item.get('meters', 0):.2f}m", 1),
                    (format_currency(item.get("price_per_meter", 0)), 1),
                    (format_currency(item.get("total", 0)), 1),
                ]
                for text, weight in vals:
                    ctk.CTkLabel(
                        row, text=text, font=ctk.CTkFont(size=12),
                        text_color=COLORS["text"],
                    ).pack(side="left", expand=(weight > 1), fill="x", padx=5, pady=4)

                sep = ctk.CTkFrame(items_card, height=1, fg_color=COLORS["border"])
                sep.pack(fill="x", padx=12)
        else:
            ctk.CTkLabel(
                items_card, text="Nenhum item adicionado.",
                font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"],
            ).pack(padx=15, pady=10)

        # Totais
        totals = ctk.CTkFrame(items_card, fg_color=COLORS["primary_lighter"], corner_radius=8)
        totals.pack(fill="x", padx=12, pady=10)

        total_lines = [
            ("Total:", format_currency(quote.get("total", 0)), True),
            ("Custo:", format_currency(quote.get("cost_total", 0)), False),
            ("Lucro:", format_currency(quote.get("profit", 0)), False),
            ("Margem:", f"{quote.get('profitability', 0):.1f}%", False),
        ]
        for label, value, bold in total_lines:
            row = ctk.CTkFrame(totals, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont(size=13, weight="bold" if bold else "normal"),
                text_color=COLORS["text"],
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=value,
                font=ctk.CTkFont(size=13, weight="bold" if bold else "normal"),
                text_color=COLORS["primary"] if bold else COLORS["text"],
            ).pack(side="right")

        # Notas técnicas
        if quote.get("technical_notes"):
            notes_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                       border_width=1, border_color=COLORS["border"])
            notes_card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                notes_card, text="📝 Notas Técnicas",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
                anchor="w",
            ).pack(padx=15, pady=(12, 5), anchor="w")
            ctk.CTkLabel(
                notes_card, text=quote["technical_notes"],
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
                anchor="w", wraplength=600, justify="left",
            ).pack(padx=15, pady=(0, 12), anchor="w")

        # Métodos de pagamento
        if quote.get("payment_methods"):
            pay_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                     border_width=1, border_color=COLORS["border"])
            pay_card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                pay_card, text="💳 Métodos de Pagamento",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
                anchor="w",
            ).pack(padx=15, pady=(12, 5), anchor="w")

            pay_labels = {
                'pix': '🔲 Pix', 'debito': '💳 Débito', 'credito': '💳 Crédito',
                'dinheiro': '💵 Dinheiro', 'transferencia': '🔄 Transferência', 'boleto': '📄 Boleto',
            }
            methods_frame = ctk.CTkFrame(pay_card, fg_color="transparent")
            methods_frame.pack(padx=15, pady=(0, 12), anchor="w")

            for method in quote["payment_methods"].split(","):
                method = method.strip()
                if method:
                    label = pay_labels.get(method, method)
                    badge = ctk.CTkLabel(
                        methods_frame, text=f" {label} ",
                        font=ctk.CTkFont(size=12),
                        fg_color=COLORS["primary_light"],
                        text_color=COLORS["primary"],
                        corner_radius=6, height=28,
                    )
                    badge.pack(side="left", padx=(0, 6), pady=2)

        # Termos do contrato
        if quote.get("contract_terms"):
            terms_card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                       border_width=1, border_color=COLORS["border"])
            terms_card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                terms_card, text="📋 Condições de Contrato",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
                anchor="w",
            ).pack(padx=15, pady=(12, 5), anchor="w")
            ctk.CTkLabel(
                terms_card, text=quote["contract_terms"],
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
                anchor="w", wraplength=600, justify="left",
            ).pack(padx=15, pady=(0, 12), anchor="w")

    # ========== Formulário de Criação/Edição ==========

    def _open_create_form(self):
        self._open_quote_form()

    def _open_edit_form(self, quote_id):
        quote = db.get_quote_by_id(quote_id)
        if quote:
            self._open_quote_form(quote)

    def _open_quote_form(self, existing_quote=None):
        """Abre formulário de orçamento em nova janela."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Orçamento" if existing_quote else "Novo Orçamento")
        dialog.geometry("700x650")
        dialog.grab_set()
        dialog.transient(self.app)

        # Centralizar
        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 700) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 650) // 2
        dialog.geometry(f"+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Dados do cliente ---
        ctk.CTkLabel(
            scroll, text="👤 Dados do Cliente",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(0, 8))

        fields_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        fields_frame.pack(fill="x", pady=(0, 15))
        fields_frame.grid_columnconfigure((0, 1), weight=1)

        # Nome
        ctk.CTkLabel(fields_frame, text="Nome do Cliente *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w", padx=(0, 10))
        name_entry = ctk.CTkEntry(fields_frame, height=35, font=ctk.CTkFont(size=13))
        name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))

        # Telefone
        ctk.CTkLabel(fields_frame, text="Telefone", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=0, column=1, sticky="w")
        phone_entry = ctk.CTkEntry(fields_frame, height=35, font=ctk.CTkFont(size=13))
        phone_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))

        # Endereço
        ctk.CTkLabel(fields_frame, text="Endereço", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=2, column=0, columnspan=2, sticky="w")
        addr_entry = ctk.CTkEntry(fields_frame, height=35, font=ctk.CTkFont(size=13))
        addr_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # Data de agendamento
        ctk.CTkLabel(fields_frame, text="Data Agendamento (DD/MM/AAAA)", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=4, column=0, sticky="w")
        sched_entry = DateEntry(fields_frame)
        sched_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))

        # Preencher dados se edição
        if existing_quote:
            name_entry.insert(0, existing_quote.get("client_name", ""))
            phone_entry.insert(0, existing_quote.get("client_phone", "") or "")
            addr_entry.insert(0, existing_quote.get("client_address", "") or "")
            if existing_quote.get("scheduled_date"):
                sched_entry.set(str(existing_quote["scheduled_date"])[:10])

        # --- Itens ---
        ctk.CTkLabel(
            scroll, text="📦 Itens do Orçamento",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(10, 8))

        # Lista de itens existentes
        items_container = ctk.CTkFrame(scroll, fg_color="transparent")
        items_container.pack(fill="x", pady=(0, 10))

        items_list = []  # Lista de dicts dos itens adicionados
        total_var = ctk.StringVar(value="R$ 0,00")

        if existing_quote and existing_quote.get("items"):
            for item in existing_quote["items"]:
                items_list.append({
                    "id": item.get("id"),
                    "product_id": item.get("product_id"),
                    "product_name": item.get("product_name", ""),
                    "measure": item.get("measure", 0),
                    "meters": item.get("meters", 0),
                    "price_per_meter": item.get("price_per_meter", 0),
                    "total": item.get("total", 0),
                })

        def refresh_items_display():
            for w in items_container.winfo_children():
                w.destroy()
            total = sum(it["total"] for it in items_list)
            total_var.set(format_currency(total))

            for idx, item in enumerate(items_list):
                row = ctk.CTkFrame(items_container, fg_color=COLORS["card"],
                                    corner_radius=8, border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", pady=2)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)

                ctk.CTkLabel(
                    inner, text=item["product_name"],
                    font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"],
                ).pack(side="left")

                ctk.CTkLabel(
                    inner, text=f"  {item['meters']:.2f}m × {format_currency(item['price_per_meter'])}/m = {format_currency(item['total'])}",
                    font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
                ).pack(side="left", padx=8)

                ctk.CTkButton(
                    inner, text="✕", width=28, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda i=idx: remove_item(i),
                ).pack(side="right")

        def remove_item(idx):
            items_list.pop(idx)
            refresh_items_display()

        refresh_items_display()

        # Adicionar item
        add_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                  border_width=1, border_color=COLORS["border"])
        add_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            add_frame, text="Adicionar Item",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
        ).pack(padx=12, pady=(10, 5), anchor="w")

        products = db.get_all_products()
        dobra_value = db.get_dobra_value()
        product_names = []
        for p in products:
            label = f"{p['name']} ({p['type']}, {p['measure']}cm) - {format_currency(p['price_per_meter'])}/m"
            if p.get('has_dobra'):
                label += f" [+Dobra {format_currency(dobra_value)}/m]"
            product_names.append(label)
        product_map = {name: p for name, p in zip(product_names, products)}

        add_inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_inner.pack(fill="x", padx=12, pady=(0, 10))
        add_inner.grid_columnconfigure(0, weight=3)
        add_inner.grid_columnconfigure(1, weight=1)
        add_inner.grid_columnconfigure(2, weight=1)

        product_var = ctk.StringVar(value=product_names[0] if product_names else "")
        if product_names:
            prod_menu = ctk.CTkOptionMenu(
                add_inner, values=product_names, variable=product_var,
                font=ctk.CTkFont(size=12), height=35,
            )
            prod_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        else:
            ctk.CTkLabel(
                add_inner, text="Nenhum produto cadastrado",
                font=ctk.CTkFont(size=12), text_color=COLORS["error"],
            ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(add_inner, text="Metros:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=1, sticky="e", padx=(0, 5))
        meters_entry = ctk.CTkEntry(add_inner, width=80, height=35, font=ctk.CTkFont(size=13))
        meters_entry.grid(row=0, column=2, sticky="w", padx=(0, 8))
        meters_entry.insert(0, "1")

        def add_item():
            sel = product_var.get()
            product = product_map.get(sel)
            if not product:
                self.app.show_toast("Selecione um produto.", "warning")
                return
            try:
                meters = float(meters_entry.get() or 0)
                if meters <= 0:
                    self.app.show_toast("Metros deve ser maior que zero.", "warning")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido para metros.", "warning")
                return

            total = meters * product["price_per_meter"]
            effective_price = product["price_per_meter"]
            if product.get("has_dobra"):
                effective_price += dobra_value
                total = meters * effective_price
            items_list.append({
                "id": None,
                "product_id": product["id"],
                "product_name": product["name"] + (" (c/ dobra)" if product.get("has_dobra") else ""),
                "measure": product["measure"],
                "meters": meters,
                "price_per_meter": effective_price,
                "total": total,
            })
            refresh_items_display()
            meters_entry.delete(0, "end")
            meters_entry.insert(0, "1")

        ctk.CTkButton(
            add_inner, text="+ Adicionar", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            height=35, width=100, corner_radius=8,
            command=add_item,
        ).grid(row=0, column=3, padx=(8, 0))

        # Notas e termos
        ctk.CTkLabel(scroll, text="Notas Técnicas", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(10, 2))
        notes_text = ctk.CTkTextbox(scroll, height=60, font=ctk.CTkFont(size=12))
        notes_text.pack(fill="x", pady=(0, 8))
        if existing_quote and existing_quote.get("technical_notes"):
            notes_text.insert("1.0", existing_quote["technical_notes"])

        ctk.CTkLabel(scroll, text="Termos do Contrato", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 2))
        terms_text = ctk.CTkTextbox(scroll, height=60, font=ctk.CTkFont(size=12))
        terms_text.pack(fill="x", pady=(0, 8))
        if existing_quote and existing_quote.get("contract_terms"):
            terms_text.insert("1.0", existing_quote["contract_terms"])

        # --- Métodos de Pagamento ---
        ctk.CTkLabel(
            scroll, text="💳 Métodos de Pagamento",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(10, 8))

        payment_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                      border_width=1, border_color=COLORS["border"])
        payment_frame.pack(fill="x", pady=(0, 10))

        payment_inner = ctk.CTkFrame(payment_frame, fg_color="transparent")
        payment_inner.pack(padx=15, pady=12)

        payment_methods_list = [
            ("pix", "Pix"),
            ("debito", "Débito"),
            ("credito", "Crédito"),
            ("dinheiro", "Dinheiro"),
            ("transferencia", "Transferência"),
            ("boleto", "Boleto"),
        ]

        payment_vars = {}
        existing_methods = []
        if existing_quote and existing_quote.get("payment_methods"):
            existing_methods = existing_quote["payment_methods"].split(",")

        for idx, (key, label) in enumerate(payment_methods_list):
            var = ctk.BooleanVar(value=key in existing_methods)
            payment_vars[key] = var
            ctk.CTkCheckBox(
                payment_inner, text=label,
                variable=var,
                font=ctk.CTkFont(size=13),
                checkbox_height=22, checkbox_width=22,
                corner_radius=6,
                border_width=2,
                fg_color=COLORS["primary"],
                hover_color="#1d4ed8",
                text_color=COLORS["text"],
            ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=(0, 25), pady=4)

        payment_inner.grid_columnconfigure((0, 1, 2), weight=1)

        # Total
        total_frame = ctk.CTkFrame(scroll, fg_color=COLORS["primary_lighter"], corner_radius=10)
        total_frame.pack(fill="x", pady=(10, 5))

        ctk.CTkLabel(
            total_frame, text="Total:", font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(
            total_frame, textvariable=total_var,
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["primary"],
        ).pack(side="right", padx=15, pady=10)

        # Botões de ação
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar", font=ctk.CTkFont(size=13),
            fg_color="#e2e8f0", text_color=COLORS["text"],
            hover_color="#cbd5e1", width=120, height=38,
            command=dialog.destroy,
        ).pack(side="left")

        def save_quote():
            client_name = name_entry.get().strip()
            if not client_name:
                self.app.show_toast("Nome do cliente é obrigatório.", "error")
                return
            if not items_list:
                self.app.show_toast("Adicione pelo menos um item.", "error")
                return

            # Coletar métodos de pagamento selecionados
            selected_payments = ",".join(
                key for key, var in payment_vars.items() if var.get()
            )

            try:
                if existing_quote:
                    # Editar
                    db.update_quote(
                        existing_quote["id"],
                        client_name=client_name,
                        client_phone=phone_entry.get().strip(),
                        client_address=addr_entry.get().strip(),
                        technical_notes=notes_text.get("1.0", "end-1c").strip(),
                        contract_terms=terms_text.get("1.0", "end-1c").strip(),
                        payment_methods=selected_payments,
                        scheduled_date=sched_entry.get_iso().strip() or None,
                    )
                    # Remover itens antigos e adicionar novos
                    old_items = existing_quote.get("items", [])
                    for old_item in old_items:
                        db.remove_quote_item(old_item["id"])
                    for item in items_list:
                        db.add_quote_item(
                            existing_quote["id"],
                            item["product_id"],
                            item["meters"],
                        )
                    self.app.show_toast("Orçamento atualizado!", "success")
                else:
                    # Criar novo
                    quote_id = db.create_quote(
                        client_name=client_name,
                        client_phone=phone_entry.get().strip(),
                        client_address=addr_entry.get().strip(),
                        technical_notes=notes_text.get("1.0", "end-1c").strip(),
                        contract_terms=terms_text.get("1.0", "end-1c").strip(),
                        payment_methods=selected_payments,
                        scheduled_date=sched_entry.get_iso().strip() or None,
                    )
                    for item in items_list:
                        db.add_quote_item(
                            quote_id,
                            item["product_id"],
                            item["meters"],
                        )
                    self.app.show_toast("Orçamento criado com sucesso!", "success")

                dialog.destroy()
                self._build_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            btn_frame, text="💾 Salvar Orçamento", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS["primary"], hover_color="#1d4ed8",
            width=180, height=38, corner_radius=10,
            command=save_quote,
        ).pack(side="right")

    # ========== Ações ==========

    def _change_status(self, quote_id, new_status):
        db.update_quote(quote_id, status=new_status)
        status_text = STATUS_COLORS.get(new_status, ("", new_status))[1]
        
        # Deduzir estoque quando orçamento é aprovado
        if new_status == "approved":
            warnings = db.deduct_stock_for_quote(quote_id)
            if warnings:
                for w in warnings:
                    self.app.show_toast(w, "warning")
                self.app.show_toast("Estoque atualizado com avisos!", "warning")
            else:
                self.app.show_toast(f"Aprovado! Estoque atualizado.", "success")
        else:
            self.app.show_toast(f"Status atualizado para: {status_text}", "success")
        
        self._show_detail(quote_id)

    def _generate_pdf(self, quote_id):
        try:
            from services.pdf_generator import generate_quote_pdf
            quote = db.get_quote_by_id(quote_id)
            settings = db.get_settings()
            if quote:
                path = generate_quote_pdf(quote, settings)
                self.app.show_toast(f"PDF gerado: {os.path.basename(path)}", "success")
                # Abrir o PDF
                if os.path.exists(path):
                    os.startfile(path)
        except Exception as e:
            self.app.show_toast(f"Erro ao gerar PDF: {e}", "error")

    def _confirm_delete(self, quote):
        ConfirmDialog(
            self.app,
            "Excluir Orçamento",
            f"Excluir orçamento #{quote['id']:05d} de {quote['client_name']}?",
            lambda qid=quote["id"]: self._delete_quote(qid),
        )

    def _delete_quote(self, quote_id):
        db.delete_quote(quote_id)
        self.app.show_toast("Orçamento excluído.", "success")
        self._load_quotes()
