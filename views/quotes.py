# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Orçamentos
Criar, visualizar, editar orçamentos, gerar PDF e gerenciar status.
"""

import customtkinter as ctk
import os
import subprocess
from database import db
from components.cards import StatusBadge, create_header, create_search_bar
from theme import get_color, COLORS
from components.dialogs import ConfirmDialog, format_currency, format_date, DateEntry
from utils import format_measure, format_dimensions


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
        self.payment_filter = ""  # "", "paid", "pending"
        self._build_list()

    def _build_list(self):
        """Constrói a view de listagem."""
        # Limpar
        for w in self.winfo_children():
            w.destroy()

        # Cabeçalho
        header = create_header(
            self, "Orçamentos", "Gerencie seus orçamentos",
            action_text="", action_command=None
        )
        header.pack(fill="x", pady=(0, 15))

        # Botões de orçamento
        btn_frame_header = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame_header.pack(side="right")

        ctk.CTkButton(
            btn_frame_header, text="  🔧 Orçamento Instalado  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=38, corner_radius=10,
            command=lambda: self._open_create_form(quote_type="instalado"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame_header, text="  📦 Orçamento Não Instalado  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("warning"), hover_color=get_color("warning_hover"),
            height=38, corner_radius=10,
            command=lambda: self._open_create_form(quote_type="nao_instalado"),
        ).pack(side="left")

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

        # Filtro de pagamento
        pay_filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        pay_filter_frame.pack(fill="x", pady=(0, 10))

        PAYMENT_FILTER_OPTIONS = ["Todos", "✅ Quitados", "💰 Devedores"]
        self.pay_filter_var = ctk.StringVar(value="Todos")
        ctk.CTkSegmentedButton(
            pay_filter_frame,
            values=PAYMENT_FILTER_OPTIONS,
            variable=self.pay_filter_var,
            command=self._on_payment_filter,
            font=ctk.CTkFont(size=12),
            height=34,
        ).pack(side="left")

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

    def _on_payment_filter(self, value):
        if value == "✅ Quitados":
            self.payment_filter = "paid"
        elif value == "💰 Devedores":
            self.payment_filter = "pending"
        else:
            self.payment_filter = ""
        self._load_quotes()

    def _load_quotes(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        quotes = db.get_all_quotes(search=self.search_text, status_filter=self.status_filter)
        payment_summaries = db.get_all_payment_summaries()

        # Filtrar por status de pagamento
        if self.payment_filter == "paid":
            quotes = [q for q in quotes if payment_summaries.get(q['id'], {}).get('is_paid', False)
                      and payment_summaries.get(q['id'], {}).get('total_paid', 0) > 0]
        elif self.payment_filter == "pending":
            quotes = [q for q in quotes if not payment_summaries.get(q['id'], {}).get('is_paid', True)
                      or payment_summaries.get(q['id'], {}).get('total_paid', 0) == 0]

        # Contar pagos vs devedores para o resumo
        total_paid_count = sum(1 for q in db.get_all_quotes() 
                                if payment_summaries.get(q['id'], {}).get('is_paid', False)
                                and payment_summaries.get(q['id'], {}).get('total_paid', 0) > 0)
        total_pending_amount = sum(payment_summaries.get(q['id'], {}).get('balance', 0) 
                                   for q in db.get_all_quotes())
        total_received_amount = sum(payment_summaries.get(q['id'], {}).get('total_paid', 0)
                                     for q in db.get_all_quotes())

        # Resumo de pagamentos
        pay_summary_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        pay_summary_frame.pack(fill="x", pady=(0, 10))
        pay_summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Recebido
        recv_box = ctk.CTkFrame(pay_summary_frame, fg_color=COLORS["success_light"], corner_radius=8)
        recv_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(recv_box, text="💵 Recebido", font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_secondary"]).pack(padx=8, pady=(6, 0))
        ctk.CTkLabel(recv_box, text=format_currency(total_received_amount),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["success"]).pack(padx=8, pady=(0, 6))

        # Devedor
        debt_box = ctk.CTkFrame(pay_summary_frame, fg_color=COLORS["error_light"], corner_radius=8)
        debt_box.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(debt_box, text="📛 Devedor", font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_secondary"]).pack(padx=8, pady=(6, 0))
        ctk.CTkLabel(debt_box, text=format_currency(total_pending_amount),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["error"]).pack(padx=8, pady=(0, 6))

        # Quitados
        paid_box = ctk.CTkFrame(pay_summary_frame, fg_color=COLORS["primary_lighter"], corner_radius=8)
        paid_box.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(paid_box, text="✅ Quitados", font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_secondary"]).pack(padx=8, pady=(6, 0))
        ctk.CTkLabel(paid_box, text=str(total_paid_count),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["primary"]).pack(padx=8, pady=(0, 6))

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
            self._create_quote_card(quote, payment_summaries)

    def _create_quote_card(self, quote, payment_summaries=None):
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

        qt = quote.get("quote_type", "instalado") or "instalado"
        qt_text = "🔧 Instalado" if qt == "instalado" else "📦 Não Instalado"
        qt_fg = COLORS["success_light"] if qt == "instalado" else COLORS["warning_light"]
        qt_tc = COLORS["success"] if qt == "instalado" else COLORS["warning"]
        ctk.CTkLabel(
            top_row, text=f"  {qt_text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=qt_fg, text_color=qt_tc,
            corner_radius=4,
        ).pack(side="left", padx=(6, 0))

        details = f"{format_date(quote.get('created_at', ''))}  •  {format_currency(quote.get('total', 0))}"
        if quote.get("profit") and quote["profit"] > 0:
            details += f"  •  Lucro: {format_currency(quote['profit'])}"
        
        # Adicionar info de pagamento
        pay_summary = (payment_summaries or {}).get(quote['id'])
        if pay_summary and pay_summary['total_paid'] > 0:
            if pay_summary['is_paid']:
                details += "  •  ✅ Quitado"
            else:
                details += f"  •  💰 Pago: {format_currency(pay_summary['total_paid'])} | Devedor: {format_currency(pay_summary['balance'])}"
        
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
        if status in ("draft", "sent", "approved"):
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
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            height=36, corner_radius=8,
            command=lambda: self._generate_pdf(quote["id"]),
        ).pack(side="left", padx=5)

        if status in ("draft", "sent", "approved"):
            ctk.CTkButton(
                action_inner, text="✏️ Editar", font=ctk.CTkFont(size=13),
                fg_color=get_color("warning"), hover_color=get_color("warning_hover"),
                height=36, corner_radius=8,
                command=lambda: self._open_edit_form(quote["id"]),
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                action_inner, text="📋 Clonar Orçamento", font=ctk.CTkFont(size=13),
                fg_color="#8b5cf6", hover_color="#7c3aed",
                height=36, corner_radius=8,
                command=lambda: self._clone_quote_dialog(quote),
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

            cols = [("Produto", 3), ("Dimensões", 1), ("Qtd", 1), ("Preço", 1), ("Subtotal", 1)]
            for text, weight in cols:
                ctk.CTkLabel(
                    table_header, text=text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=COLORS["primary"],
                ).pack(side="left", expand=(weight > 1), fill="x", padx=5, pady=6)

            for item in items:
                row = ctk.CTkFrame(items_card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)

                product_name = item.get("product_name", "-")
                item_discount = item.get("discount", 0)
                if item_discount > 0:
                    product_name += f" [-{format_currency(item_discount)}]"
                
                vals = [
                    (product_name, 3),
                    (format_dimensions(item.get('width', 0), item.get('length', 0)), 1),
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

        # Calcular subtotal e desconto
        subtotal = sum(item.get('total', 0) for item in items)
        discount_total = quote.get("discount_total", 0)
        discount_type = quote.get("discount_type", "percentage")
        
        if discount_type == "value":
            discount_amount = discount_total if discount_total > 0 else 0
            discount_label = f"Desconto (R$):"
        else:  # percentage
            discount_amount = subtotal * (discount_total / 100) if discount_total > 0 else 0
            discount_label = f"Desconto ({discount_total:.1f}%):"
        
        total_lines = []
        
        # Se houver desconto total, mostrar subtotal e desconto
        if discount_total > 0:
            total_lines.append(("Subtotal:", format_currency(subtotal), False))
            total_lines.append((discount_label, f"- {format_currency(discount_amount)}", False))
        
        total_lines.extend([
            ("Total:", format_currency(quote.get("total", 0)), True),
            ("Custo:", format_currency(quote.get("cost_total", 0)), False),
            ("Lucro:", format_currency(quote.get("profit", 0)), False),
            ("Margem:", f"{quote.get('profitability', 0):.1f}%", False),
        ])
        
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

        # === SEÇÃO DE PAGAMENTOS (Saldo Devedor / Saldo Pago) ===
        self._build_payments_section(scroll, quote)

    # ========== Seção de Pagamentos ==========

    def _build_payments_section(self, parent, quote):
        """Constrói a seção de pagamentos com saldo devedor/pago."""
        quote_id = quote["id"]
        summary = db.get_payment_summary(quote_id)
        payments = db.get_payments_by_quote(quote_id)

        PAY_LABELS = {
            'pix': 'Pix', 'debito': 'Débito', 'credito': 'Crédito',
            'dinheiro': 'Dinheiro', 'transferencia': 'Transferência', 'boleto': 'Boleto',
        }

        pay_card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
        pay_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            pay_card, text="💰 Pagamentos",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["text"],
            anchor="w",
        ).pack(padx=15, pady=(12, 8), anchor="w")

        # Resumo: Total | Pago | Saldo Devedor
        summary_frame = ctk.CTkFrame(pay_card, fg_color="transparent")
        summary_frame.pack(fill="x", padx=15, pady=(0, 10))
        summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Total do orçamento
        total_box = ctk.CTkFrame(summary_frame, fg_color=COLORS["primary_lighter"],
                                  corner_radius=8)
        total_box.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(total_box, text="Total", font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_secondary"]).pack(padx=10, pady=(8, 0))
        ctk.CTkLabel(total_box, text=format_currency(summary['total']),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["primary"]).pack(padx=10, pady=(0, 8))

        # Valor pago
        paid_box = ctk.CTkFrame(summary_frame, fg_color=COLORS["success_light"],
                                 corner_radius=8)
        paid_box.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(paid_box, text="Pago", font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_secondary"]).pack(padx=10, pady=(8, 0))
        ctk.CTkLabel(paid_box, text=format_currency(summary['total_paid']),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["success"]).pack(padx=10, pady=(0, 8))

        # Saldo devedor
        balance_color = COLORS["success"] if summary['is_paid'] else COLORS["error"]
        balance_bg = COLORS["success_light"] if summary['is_paid'] else COLORS["error_light"]
        balance_text = "Quitado" if summary['is_paid'] else "Saldo Devedor"

        balance_box = ctk.CTkFrame(summary_frame, fg_color=balance_bg,
                                    corner_radius=8)
        balance_box.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(balance_box, text=balance_text, font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_secondary"]).pack(padx=10, pady=(8, 0))
        ctk.CTkLabel(balance_box, text=format_currency(summary['balance']),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=balance_color).pack(padx=10, pady=(0, 8))

        # Formulário para registrar pagamento
        add_pay_frame = ctk.CTkFrame(pay_card, fg_color=COLORS["primary_lighter"],
                                      corner_radius=8)
        add_pay_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(add_pay_frame, text="Registrar Pagamento",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text"]).pack(padx=12, pady=(10, 6), anchor="w")

        form_inner = ctk.CTkFrame(add_pay_frame, fg_color="transparent")
        form_inner.pack(fill="x", padx=12, pady=(0, 10))
        form_inner.grid_columnconfigure(0, weight=1)
        form_inner.grid_columnconfigure(1, weight=2)
        form_inner.grid_columnconfigure(2, weight=2)
        form_inner.grid_columnconfigure(3, weight=0)

        # Valor
        ctk.CTkLabel(form_inner, text="Valor (R$):", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        pay_amount_entry = ctk.CTkEntry(form_inner, width=100, height=35,
                                         font=ctk.CTkFont(size=13),
                                         placeholder_text="0.00")
        pay_amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Preencher com saldo restante se houver
        if summary['balance'] > 0:
            pay_amount_entry.insert(0, f"{summary['balance']:.2f}")

        # Método de pagamento
        pay_methods = ['pix', 'debito', 'credito', 'dinheiro', 'transferencia', 'boleto']
        pay_method_labels = [PAY_LABELS[m] for m in pay_methods]
        pay_method_var = ctk.StringVar(value=pay_method_labels[0])

        ctk.CTkLabel(form_inner, text="Método:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=1, sticky="w", padx=(0, 5))
        ctk.CTkOptionMenu(form_inner, values=pay_method_labels, variable=pay_method_var,
                          font=ctk.CTkFont(size=12), height=35
                          ).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        # Observação
        ctk.CTkLabel(form_inner, text="Observação:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=2, sticky="w", padx=(0, 5))
        pay_notes_entry = ctk.CTkEntry(form_inner, height=35, font=ctk.CTkFont(size=12),
                                        placeholder_text="Ex: Parcela 1/3")
        pay_notes_entry.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        # Botão registrar
        def register_payment():
            try:
                amount = float(pay_amount_entry.get() or 0)
                if amount <= 0:
                    self.app.show_toast("Valor deve ser maior que zero.", "warning")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido.", "warning")
                return

            # Converter label para key
            method_label = pay_method_var.get()
            method_key = method_label
            for k, v in PAY_LABELS.items():
                if v == method_label:
                    method_key = k
                    break

            notes = pay_notes_entry.get().strip()
            db.add_payment(quote_id, amount, method_key, notes)
            self.app.show_toast(f"Pagamento de {format_currency(amount)} registrado!", "success")
            self._show_detail(quote_id)

        ctk.CTkButton(
            form_inner, text="💵 Registrar", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            height=35, width=110, corner_radius=8,
            command=register_payment,
        ).grid(row=1, column=3)

        # Lista de pagamentos registrados
        if payments:
            ctk.CTkLabel(pay_card, text="Histórico de Pagamentos",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=COLORS["text"]).pack(padx=15, pady=(0, 5), anchor="w")

            for pay in payments:
                row_frame = ctk.CTkFrame(pay_card, fg_color="transparent")
                row_frame.pack(fill="x", padx=15, pady=2)

                inner = ctk.CTkFrame(row_frame, fg_color=COLORS["primary_lighter"],
                                      corner_radius=6)
                inner.pack(fill="x")
                content = ctk.CTkFrame(inner, fg_color="transparent")
                content.pack(fill="x", padx=10, pady=6)

                # Valor
                ctk.CTkLabel(
                    content, text=format_currency(pay['amount']),
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=COLORS["success"],
                ).pack(side="left")

                # Método
                method_display = PAY_LABELS.get(pay.get('payment_method', ''), pay.get('payment_method', ''))
                ctk.CTkLabel(
                    content, text=f"  via {method_display}  ",
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["primary_light"],
                    text_color=COLORS["primary"],
                    corner_radius=4,
                ).pack(side="left", padx=(8, 0))

                # Data
                pay_date = format_date(pay.get('payment_date', ''))
                ctk.CTkLabel(
                    content, text=pay_date,
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"],
                ).pack(side="left", padx=(8, 0))

                # Observação
                if pay.get('notes'):
                    ctk.CTkLabel(
                        content, text=f"({pay['notes']})",
                        font=ctk.CTkFont(size=10),
                        text_color=COLORS["text_secondary"],
                    ).pack(side="left", padx=(8, 0))

                # Botão remover
                ctk.CTkButton(
                    content, text="✕", width=28, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda pid=pay['id']: self._remove_payment(quote_id, pid),
                ).pack(side="right")

        ctk.CTkFrame(pay_card, height=8, fg_color="transparent").pack()

    def _remove_payment(self, quote_id, payment_id):
        """Remove um pagamento com confirmação."""
        ConfirmDialog(
            self.app, "Remover Pagamento",
            "Tem certeza que deseja remover este pagamento?",
            lambda: (db.delete_payment(payment_id),
                     self.app.show_toast("Pagamento removido.", "success"),
                     self._show_detail(quote_id)),
        )

    # ========== Formulário de Criação/Edição ==========

    def _open_create_form(self, quote_type="instalado"):
        self._open_quote_form(quote_type=quote_type)

    def _open_edit_form(self, quote_id):
        quote = db.get_quote_by_id(quote_id)
        if quote:
            self._open_quote_form(quote, quote_type=quote.get("quote_type", "instalado") or "instalado")

    def _open_quote_form(self, existing_quote=None, quote_type="instalado"):
        """Abre formulário de orçamento em nova janela."""
        # Determinar tipo do orçamento
        if existing_quote:
            quote_type = existing_quote.get("quote_type", "instalado") or "instalado"

        is_installed_filter = 1 if quote_type == "instalado" else 0
        type_label = "Instalado" if quote_type == "instalado" else "Não Instalado"

        dialog = ctk.CTkToplevel(self.app)
        dialog.title(("Editar Orçamento" if existing_quote else "Novo Orçamento") + f" ({type_label})")
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
                    "width": item.get("width", 0),
                    "length": item.get("length", 0),
                    "meters": item.get("meters", 0),
                    "price_per_meter": item.get("price_per_meter", 0),
                    "discount": item.get("discount", 0),
                    "total": item.get("total", 0),
                    "pricing_unit": item.get("pricing_unit", "metro"),
                })

        def refresh_items_display():
            for w in items_container.winfo_children():
                w.destroy()
            subtotal = sum(it["total"] for it in items_list)
            try:
                discount_total = float(discount_total_entry.get() or 0) if 'discount_total_entry' in locals() else 0
                dtype = discount_type_var.get() if 'discount_type_var' in locals() else "%"
            except:
                discount_total = 0
                dtype = "%"
            
            if dtype == "R$":
                discount_amount = discount_total
            else:
                discount_amount = subtotal * (discount_total / 100)
            
            total = subtotal - discount_amount
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

                item_pu = item.get('pricing_unit', 'metro')
                item_unit = 'm' if item_pu == 'metro' else 'un'
                price_display = format_currency(item['price_per_meter'])
                if item.get("discount", 0) > 0:
                    price_display = f"{format_currency(item['price_per_meter'])} (desc -{format_currency(item['discount'])}/{item_unit})"
                item_info = f"  {item['meters']:.2f}{item_unit} × {price_display} = {format_currency(item['total'])}"
                
                ctk.CTkLabel(
                    inner, text=item_info,
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
        # Filtrar produtos por tipo instalado/não instalado
        products = [p for p in products if p.get('is_installed', 1) == is_installed_filter]
        dobra_value = db.get_dobra_value()
        product_names = []
        for p in products:
            dims = format_dimensions(p.get('width', 0), p.get('length', 0))
            pricing_unit = p.get('pricing_unit', 'metro')
            unit_label = '/m' if pricing_unit == 'metro' else '/un'
            label = f"{p['name']} ({p['type']}, {dims}) - {format_currency(p['price_per_meter'])}{unit_label}"
            if p.get('has_dobra'):
                label += f" [+Dobra {format_currency(dobra_value)}/m]"
            product_names.append(label)
        product_map = {name: p for name, p in zip(product_names, products)}

        add_inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_inner.pack(fill="x", padx=12, pady=(0, 10))
        add_inner.grid_columnconfigure(0, weight=3)
        add_inner.grid_columnconfigure(1, weight=1)
        add_inner.grid_columnconfigure(2, weight=1)
        add_inner.grid_columnconfigure(3, weight=1)

        product_var = ctk.StringVar(value="")

        # --- Searchable product dropdown ---
        search_frame_prod = ctk.CTkFrame(add_inner, fg_color="transparent")
        search_frame_prod.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        prod_search_entry = ctk.CTkEntry(
            search_frame_prod, height=35, font=ctk.CTkFont(size=12),
            placeholder_text="Pesquisar produto...",
        )
        prod_search_entry.pack(fill="x")

        # Listbox frame for suggestions
        suggestions_frame = ctk.CTkFrame(search_frame_prod, fg_color=COLORS["card"],
                                          corner_radius=8, border_width=1, border_color=COLORS["border"])
        # Don't pack yet - only show when there are suggestions

        suggestion_buttons = []

        def update_suggestions(*args):
            # Clear old suggestions
            for w in suggestions_frame.winfo_children():
                w.destroy()
            suggestion_buttons.clear()

            search_text_val = prod_search_entry.get().strip().lower()
            if not search_text_val:
                suggestions_frame.pack_forget()
                return

            filtered = [n for n in product_names if search_text_val in n.lower()]
            if not filtered:
                suggestions_frame.pack_forget()
                return

            suggestions_frame.pack(fill="x", pady=(2, 0))
            for name in filtered[:8]:  # Max 8 suggestions
                btn = ctk.CTkButton(
                    suggestions_frame, text=name,
                    font=ctk.CTkFont(size=11), height=28,
                    fg_color="transparent", text_color=COLORS["text"],
                    hover_color=COLORS["primary_light"],
                    anchor="w", corner_radius=4,
                    command=lambda n=name: select_product(n),
                )
                btn.pack(fill="x", padx=4, pady=1)
                suggestion_buttons.append(btn)

        def select_product(name):
            product_var.set(name)
            prod_search_entry.delete(0, "end")
            prod_search_entry.insert(0, name)
            suggestions_frame.pack_forget()

        prod_search_entry.bind("<KeyRelease>", update_suggestions)
        prod_search_entry.bind("<FocusIn>", update_suggestions)

        ctk.CTkLabel(add_inner, text="Qtd (m/un):", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=1, sticky="e", padx=(0, 5))
        meters_entry = ctk.CTkEntry(add_inner, width=70, height=35, font=ctk.CTkFont(size=13))
        meters_entry.grid(row=0, column=2, sticky="w", padx=(0, 8))
        meters_entry.insert(0, "1")

        ctk.CTkLabel(add_inner, text="Desc R$:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text"]).grid(row=0, column=3, sticky="e", padx=(0, 5))
        discount_entry = ctk.CTkEntry(add_inner, width=70, height=35, font=ctk.CTkFont(size=13))
        discount_entry.grid(row=0, column=4, sticky="w", padx=(0, 8))
        discount_entry.insert(0, "0")

        def add_item():
            sel = product_var.get()
            product = product_map.get(sel)
            if not product:
                self.app.show_toast("Selecione um produto da lista.", "warning")
                return
            try:
                pricing_unit = product.get('pricing_unit', 'metro')
                qty = float(meters_entry.get() or 0)
                if qty <= 0:
                    unit_name = "metros" if pricing_unit == 'metro' else "quantidade"
                    self.app.show_toast(f"{unit_name.capitalize()} deve ser maior que zero.", "warning")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido.", "warning")
                return
            
            try:
                discount = float(discount_entry.get() or 0)
                if discount < 0:
                    self.app.show_toast("Desconto não pode ser negativo.", "warning")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido para desconto.", "warning")
                return

            effective_price = product["price_per_meter"]
            if product.get("has_dobra"):
                effective_price += dobra_value
            
            # Desconto é aplicado no preço unitário (por metro/unidade)
            discount_amount = discount  # desconto em reais por metro/unidade
            if discount_amount > effective_price:
                self.app.show_toast("Desconto não pode ser maior que o preço unitário.", "warning")
                return
            final_price = effective_price - discount_amount
            total = qty * final_price
            
            unit_label = "m" if pricing_unit == 'metro' else "un"
            display_name = product["name"] + (" (c/ dobra)" if product.get("has_dobra") else "")
            
            items_list.append({
                "id": None,
                "product_id": product["id"],
                "product_name": display_name,
                "measure": product["measure"],
                "width": product.get("width", 0),
                "length": 0,
                "meters": qty,
                "price_per_meter": final_price,
                "discount": discount,
                "total": total,
                "pricing_unit": pricing_unit,
            })
            refresh_items_display()
            meters_entry.delete(0, "end")
            meters_entry.insert(0, "1")
            discount_entry.delete(0, "end")
            discount_entry.insert(0, "0")
            prod_search_entry.delete(0, "end")
            product_var.set("")

        ctk.CTkButton(
            add_inner, text="+ Adicionar", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=35, width=100, corner_radius=8,
            command=add_item,
        ).grid(row=0, column=5, padx=(8, 0))

        def open_new_product_dialog():
            """Abre dialog para criar produto rápido dentro do orçamento."""
            from views.products import _get_product_types_map
            
            prod_dialog = ctk.CTkToplevel(dialog)
            prod_dialog.title("Novo Produto")
            prod_dialog.geometry("450x600")
            prod_dialog.grab_set()
            prod_dialog.transient(dialog)
            
            prod_dialog.update_idletasks()
            px = dialog.winfo_rootx() + (dialog.winfo_width() - 450) // 2
            py = dialog.winfo_rooty() + (dialog.winfo_height() - 600) // 2
            prod_dialog.geometry(f"+{px}+{py}")
            
            pscroll = ctk.CTkScrollableFrame(prod_dialog, fg_color="transparent")
            pscroll.pack(fill="both", expand=True, padx=20, pady=10)
            
            ctk.CTkLabel(pscroll, text="Novo Produto", font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w", pady=(0, 12))
            
            # Nome
            ctk.CTkLabel(pscroll, text="Nome do Produto *", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w")
            np_name = ctk.CTkEntry(pscroll, height=35, font=ctk.CTkFont(size=13))
            np_name.pack(fill="x", pady=(2, 8))
            
            # Tipo
            types_map = _get_product_types_map()
            type_keys = list(types_map.keys())
            ctk.CTkLabel(pscroll, text="Tipo *", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w")
            np_type_var = ctk.StringVar(value=type_keys[0] if type_keys else "calha")
            ctk.CTkOptionMenu(pscroll, values=type_keys, variable=np_type_var,
                              font=ctk.CTkFont(size=12), height=35).pack(fill="x", pady=(2, 8))
            
            # Largura
            ctk.CTkLabel(pscroll, text="Largura (cm) *", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w")
            np_width = ctk.CTkEntry(pscroll, height=35, font=ctk.CTkFont(size=13))
            np_width.pack(fill="x", pady=(2, 8))
            
            # Preço e Custo
            price_frame = ctk.CTkFrame(pscroll, fg_color="transparent")
            price_frame.pack(fill="x", pady=(0, 8))
            price_frame.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkLabel(price_frame, text="Preço (R$) *", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
            np_price = ctk.CTkEntry(price_frame, height=35, font=ctk.CTkFont(size=13))
            np_price.grid(row=1, column=0, sticky="ew", padx=(0, 5))
            
            ctk.CTkLabel(price_frame, text="Custo (R$)", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
            np_cost = ctk.CTkEntry(price_frame, height=35, font=ctk.CTkFont(size=13))
            np_cost.grid(row=1, column=1, sticky="ew", padx=(5, 0))

            # Instalado e Cobrança
            opt_frame = ctk.CTkFrame(pscroll, fg_color="transparent")
            opt_frame.pack(fill="x", pady=(0, 8))
            opt_frame.grid_columnconfigure((0, 1), weight=1)

            ctk.CTkLabel(opt_frame, text="Instalado?", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
            np_installed_var = ctk.StringVar(value=str(is_installed_filter))
            ctk.CTkOptionMenu(opt_frame, values=["1", "0"], variable=np_installed_var,
                              font=ctk.CTkFont(size=12), height=35).grid(row=1, column=0, sticky="ew", padx=(0, 5))

            ctk.CTkLabel(opt_frame, text="Cobrança por", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
            np_pricing_var = ctk.StringVar(value="metro")
            ctk.CTkOptionMenu(opt_frame, values=["metro", "unidade"], variable=np_pricing_var,
                              font=ctk.CTkFont(size=12), height=35).grid(row=1, column=1, sticky="ew", padx=(5, 0))
            
            # Descrição
            ctk.CTkLabel(pscroll, text="Descrição", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w")
            np_desc = ctk.CTkTextbox(pscroll, height=50, font=ctk.CTkFont(size=12))
            np_desc.pack(fill="x", pady=(2, 12))
            
            def save_new_product():
                name = np_name.get().strip()
                if not name:
                    self.app.show_toast("Nome do produto é obrigatório.", "error")
                    return
                try:
                    p_width = float(np_width.get() or 0)
                    p_price = float(np_price.get() or 0)
                    p_cost = float(np_cost.get() or 0)
                    p_installed = int(np_installed_var.get())
                    p_pricing = np_pricing_var.get()
                    if p_price <= 0 or p_width <= 0:
                        self.app.show_toast("Preço e largura devem ser maiores que zero.", "error")
                        return
                    db.create_product(
                        name=name,
                        type=np_type_var.get(),
                        measure=p_width,
                        price_per_meter=p_price,
                        cost=p_cost,
                        description=np_desc.get("1.0", "end-1c").strip(),
                        width=p_width,
                        length=0,
                        is_installed=p_installed,
                        pricing_unit=p_pricing,
                    )
                    self.app.show_toast("Produto criado!", "success")
                    prod_dialog.destroy()
                    
                    # Atualizar lista de produtos no dropdown
                    nonlocal products, product_names, product_map
                    products = db.get_all_products()
                    products = [p for p in products if p.get('is_installed', 1) == is_installed_filter]
                    product_names.clear()
                    new_product_map = {}
                    for p in products:
                        dims = format_dimensions(p.get('width', 0), p.get('length', 0))
                        pu = p.get('pricing_unit', 'metro')
                        ul = '/m' if pu == 'metro' else '/un'
                        lbl = f"{p['name']} ({p['type']}, {dims}) - {format_currency(p['price_per_meter'])}{ul}"
                        if p.get('has_dobra'):
                            lbl += f" [+Dobra {format_currency(dobra_value)}/m]"
                        product_names.append(lbl)
                        new_product_map[lbl] = p
                    product_map.clear()
                    product_map.update(new_product_map)
                    if product_names:
                        product_var.set(product_names[-1])
                        prod_search_entry.delete(0, "end")
                        prod_search_entry.insert(0, product_names[-1])
                except Exception as e:
                    self.app.show_toast(f"Erro ao criar produto: {e}", "error")
            
            btn_f = ctk.CTkFrame(pscroll, fg_color="transparent")
            btn_f.pack(fill="x")
            ctk.CTkButton(btn_f, text="Cancelar", fg_color=get_color("border"),
                          text_color=get_color("text"), hover_color=get_color("border_hover"),
                          height=36, command=prod_dialog.destroy).pack(side="left")
            ctk.CTkButton(btn_f, text="💾 Salvar Produto", fg_color=get_color("primary"),
                          hover_color=get_color("primary_hover"), height=36,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          command=save_new_product).pack(side="right")

        ctk.CTkButton(
            add_inner, text="🆕 Novo Produto", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=get_color("warning"), hover_color=get_color("warning_hover"),
            height=35, width=120, corner_radius=8,
            command=open_new_product_dialog,
        ).grid(row=0, column=6, padx=(5, 0))

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
                fg_color=get_color("primary"),
                hover_color=get_color("primary_hover"),
                text_color=get_color("text"),
            ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=(0, 25), pady=4)

        payment_inner.grid_columnconfigure((0, 1, 2), weight=1)

        # Desconto Total
        discount_total_frame = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                             border_width=1, border_color=COLORS["border"])
        discount_total_frame.pack(fill="x", pady=(10, 5))

        discount_inner = ctk.CTkFrame(discount_total_frame, fg_color="transparent")
        discount_inner.pack(fill="x", padx=12, pady=10)
        
        # Toggle entre % e R$
        discount_type_var = ctk.StringVar(value=existing_quote.get("discount_type", "percentage") if existing_quote else "percentage")
        
        ctk.CTkLabel(
            discount_inner, text="Desconto Total:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
        ).pack(side="left")

        discount_total_entry = ctk.CTkEntry(
            discount_inner, width=100, height=35, font=ctk.CTkFont(size=14)
        )
        discount_total_entry.pack(side="left", padx=10)
        discount_total_entry.insert(0, str(existing_quote.get("discount_total", 0) if existing_quote else 0))
        
        # Segmented button para tipo de desconto
        ctk.CTkSegmentedButton(
            discount_inner,
            values=["%", "R$"],
            variable=discount_type_var,
            font=ctk.CTkFont(size=12),
            height=35,
            width=100,
            command=lambda v: update_total_with_discount()
        ).pack(side="left", padx=(0, 10))
        
        def update_total_with_discount():
            try:
                disc = float(discount_total_entry.get() or 0)
                dtype = "percentage" if discount_type_var.get() == "%" else "value"
                
                if dtype == "percentage" and (disc < 0 or disc > 100):
                    self.app.show_toast("Desconto percentual deve estar entre 0 e 100%.", "warning")
                    return
                elif dtype == "value" and disc < 0:
                    self.app.show_toast("Desconto em reais não pode ser negativo.", "warning")
                    return
                    
                subtotal = sum(it["total"] for it in items_list)
                
                if dtype == "value":
                    discount_amount = disc
                    if discount_amount > subtotal:
                        self.app.show_toast("Desconto não pode ser maior que o subtotal.", "warning")
                        return
                else:  # percentage
                    discount_amount = subtotal * (disc / 100)
                
                total = subtotal - discount_amount
                total_var.set(format_currency(total))
            except ValueError:
                pass
        
        ctk.CTkButton(
            discount_inner, text="Aplicar", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            height=35, width=80, corner_radius=8,
            command=update_total_with_discount,
        ).pack(side="left")

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
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"), width=120, height=38,
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
                discount_total = float(discount_total_entry.get() or 0)
                discount_type = "percentage" if discount_type_var.get() == "%" else "value"
                
                if discount_type == "percentage" and (discount_total < 0 or discount_total > 100):
                    self.app.show_toast("Desconto percentual deve estar entre 0 e 100%.", "error")
                    return
                elif discount_type == "value" and discount_total < 0:
                    self.app.show_toast("Desconto em reais não pode ser negativo.", "error")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido para desconto total.", "error")
                return
            
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
                        discount_total=discount_total,
                        discount_type=discount_type,
                        quote_type=quote_type,
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
                            discount=item.get("discount", 0),
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
                    # Atualizar desconto total e tipo
                    db.update_quote(quote_id, discount_total=discount_total, discount_type=discount_type, quote_type=quote_type)
                    
                    for item in items_list:
                        db.add_quote_item(
                            quote_id,
                            item["product_id"],
                            item["meters"],
                            discount=item.get("discount", 0),
                        )
                    self.app.show_toast("Orçamento criado com sucesso!", "success")

                dialog.destroy()
                self._build_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            btn_frame, text="💾 Salvar Orçamento", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            width=180, height=38, corner_radius=10,
            command=save_quote,
        ).pack(side="right")

    # ========== Clone (Clonar) orçamento com transferência de itens ==========

    def _clone_quote_dialog(self, quote):
        """Abre dialog para clonar orçamento, permitindo recortar itens para o novo."""
        items = quote.get("items", [])
        quote_id = quote["id"]

        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Clonar Orçamento #{quote_id:05d}")
        dialog.geometry("550x500")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 550) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            scroll, text="📋 Clonar Orçamento",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            scroll,
            text=f"Cliente: {quote.get('client_name', '-')}\n"
                 f"O novo orçamento será criado com os mesmos dados do cliente.\n"
                 f"Selecione os itens que deseja MOVER para o novo orçamento\n"
                 f"(serão removidos do orçamento atual).",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            justify="left", wraplength=480,
        ).pack(anchor="w", pady=(0, 12))

        # Checkboxes para itens
        item_vars = {}
        if items:
            ctk.CTkLabel(
                scroll, text="Selecione itens para transferir:",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
            ).pack(anchor="w", pady=(0, 8))

            for item in items:
                var = ctk.BooleanVar(value=False)
                item_id = item.get("id")
                item_vars[item_id] = var

                pricing_u = item.get("pricing_unit", "metro")
                unit_lbl = "m" if pricing_u == "metro" else "un"
                label_text = (
                    f"{item.get('product_name', '-')} — "
                    f"{item.get('meters', 0):.2f}{unit_lbl} × "
                    f"{format_currency(item.get('price_per_meter', 0))}/{unit_lbl} = "
                    f"{format_currency(item.get('total', 0))}"
                )
                chk = ctk.CTkCheckBox(
                    scroll, text=label_text, variable=var,
                    font=ctk.CTkFont(size=12),
                    checkbox_height=22, checkbox_width=22,
                    corner_radius=6, border_width=2,
                    fg_color=get_color("primary"),
                    hover_color=get_color("primary_hover"),
                    text_color=get_color("text"),
                )
                chk.pack(anchor="w", pady=3)
        else:
            ctk.CTkLabel(
                scroll, text="Este orçamento não possui itens para transferir.",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w", pady=10)

        # Tipo do novo orçamento
        ctk.CTkLabel(
            scroll, text="Tipo do novo orçamento:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(15, 5))

        new_type_var = ctk.StringVar(value=quote.get("quote_type", "instalado") or "instalado")
        type_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        type_frame.pack(anchor="w")
        ctk.CTkRadioButton(type_frame, text="Instalado", variable=new_type_var,
                           value="instalado", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(type_frame, text="Não Instalado", variable=new_type_var,
                           value="nao_instalado", font=ctk.CTkFont(size=12)).pack(side="left")

        # Botões
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar", font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"), width=120, height=38,
            command=dialog.destroy,
        ).pack(side="left")

        def do_clone():
            try:
                # Criar novo orçamento com mesmos dados do cliente
                new_quote_id = db.create_quote(
                    client_name=quote.get("client_name", ""),
                    client_phone=quote.get("client_phone", "") or "",
                    client_address=quote.get("client_address", "") or "",
                    technical_notes=quote.get("technical_notes", "") or "",
                    contract_terms=quote.get("contract_terms", "") or "",
                    payment_methods=quote.get("payment_methods", "") or "",
                    scheduled_date=quote.get("scheduled_date"),
                )
                db.update_quote(new_quote_id, quote_type=new_type_var.get())

                # Itens selecionados para transferir (recortar)
                moved_count = 0
                for item in items:
                    item_id = item.get("id")
                    if item_id and item_vars.get(item_id) and item_vars[item_id].get():
                        # Adicionar no novo orçamento
                        db.add_quote_item(
                            new_quote_id,
                            item.get("product_id"),
                            item.get("meters", 0),
                            discount=item.get("discount", 0),
                        )
                        # Remover do orçamento original
                        db.remove_quote_item(item_id)
                        moved_count += 1

                dialog.destroy()
                msg = f"Orçamento #{new_quote_id:05d} criado!"
                if moved_count > 0:
                    msg += f" {moved_count} item(ns) transferido(s)."
                self.app.show_toast(msg, "success")
                self._show_detail(new_quote_id)
            except Exception as e:
                self.app.show_toast(f"Erro ao clonar: {e}", "error")

        ctk.CTkButton(
            btn_frame, text="📋 Criar Orçamento Clone",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#8b5cf6", hover_color="#7c3aed",
            width=200, height=38, corner_radius=10,
            command=do_clone,
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
