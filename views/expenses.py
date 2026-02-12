# -*- coding: utf-8 -*-
"""
CalhaGest - Sistema Financeiro (Despesas e Equipamentos)
Registrar e gerenciar despesas da empresa.
"""

import customtkinter as ctk
from database import db
from components.cards import create_header, create_search_bar
from theme import get_color, COLORS
from components.dialogs import ConfirmDialog, format_currency, format_date, DateEntry, parse_decimal


class ExpensesView(ctk.CTkFrame):
    """View de gestão de despesas."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.search_text = ""
        self.category_filter = ""
        self._load_categories()
        self._build_list()

    def _load_categories(self):
        """Carrega categorias do banco de dados."""
        categories = db.get_all_expense_categories()
        self.expense_categories = [(cat['key'], cat['label']) for cat in categories]
        self.category_map = {cat['key']: cat['label'] for cat in categories}
        self.category_colors = {cat['key']: cat['color'] for cat in categories}

    def _build_list(self):
        for w in self.winfo_children():
            w.destroy()

        header = create_header(
            self, "Financeiro — Despesas", "Registre e acompanhe as despesas da empresa",
            action_text="", action_command=None,
        )
        header.pack(fill="x", pady=(0, 15))

        # Botões de ação
        action_frame = ctk.CTkFrame(header, fg_color="transparent")
        action_frame.pack(side="right")

        ctk.CTkButton(
            action_frame, text="  ⚙️ Categorias  ",
            font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), hover_color=get_color("border_hover"),
            text_color=get_color("text"),
            height=38, corner_radius=10,
            command=self._open_categories_manager,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_frame, text="  + Nova Despesa  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=38, corner_radius=10,
            command=self._open_expense_form,
        ).pack(side="left")

        # Resumo
        summary = db.get_expenses_summary()
        summary_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                      border_width=1, border_color=COLORS["border"])
        summary_frame.pack(fill="x", pady=(0, 15))
        grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        stats = [
            ("💸 Total Despesas", format_currency(summary.get("total", 0)), COLORS["error"]),
            ("📅 Este Mês", format_currency(summary.get("month_total", 0)), COLORS["warning"]),
            ("📊 Categorias", str(len(summary.get("by_category", {}))), COLORS["primary"]),
        ]
        for col, (label, value, color) in enumerate(stats):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, sticky="nsew")
            ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack()
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=color).pack(pady=(2, 0))

        # Filtros
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        search_frame, self.search_entry = create_search_bar(
            filter_frame, "Pesquisar despesa...", self._on_search
        )
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        cat_options = ["Todas"] + [v for _, v in self.expense_categories]
        self.cat_var = ctk.StringVar(value="Todas")
        ctk.CTkOptionMenu(
            filter_frame, values=cat_options, variable=self.cat_var,
            font=ctk.CTkFont(size=12), height=38, width=150,
            command=self._on_category_filter,
        ).pack(side="right")

        # Lista
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self._load_expenses()

    def _on_search(self, text):
        self.search_text = text
        self._load_expenses()

    def _on_category_filter(self, value):
        if value == "Todas":
            self.category_filter = ""
        else:
            rev_map = {v: k for k, v in self.expense_categories}
            self.category_filter = rev_map.get(value, "")
        self._load_expenses()

    def _load_expenses(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        expenses = db.get_all_expenses(search=self.search_text, category_filter=self.category_filter)

        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(expenses)} despesa(s)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(0, 8))

        if not expenses:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhuma despesa encontrada.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_secondary"],
            ).pack(pady=40)
            return

        for exp in expenses:
            self._create_expense_card(exp)

    def _create_expense_card(self, expense):
        card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"], corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=10)

        # Left info
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left, text=expense.get("description", "-"),
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w")

        cat_key = expense.get("category", "geral")
        cat_label = self.category_map.get(cat_key, cat_key)
        cat_color = self.category_colors.get(cat_key, "#6b7280")

        info_frame = ctk.CTkFrame(left, fg_color="transparent")
        info_frame.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            info_frame, text=f" {cat_label} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=cat_color, text_color="#FFFFFF", corner_radius=4,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            info_frame,
            text=f"📅 {format_date(expense.get('expense_date', ''))}",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"],
        ).pack(side="left")

        if expense.get("notes"):
            ctk.CTkLabel(
                left, text=expense["notes"],
                font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"],
                wraplength=300, justify="left",
            ).pack(anchor="w", pady=(2, 0))

        # Right: value + actions
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkLabel(
            right, text=format_currency(expense.get("amount", 0)),
            font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["error"],
        ).pack(pady=(0, 4))

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="✏️", width=30, height=28,
            fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
            corner_radius=6,
            command=lambda e=expense: self._open_expense_form(e),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_row, text="🗑", width=30, height=28,
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"], corner_radius=6,
            command=lambda e=expense: self._confirm_delete(e),
        ).pack(side="left", padx=2)

    def _open_expense_form(self, existing=None):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Despesa" if existing else "Nova Despesa")
        dialog.geometry("450x480")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 450) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 480) // 2
        dialog.geometry(f"+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(scroll, text="💸 Despesa",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        # Descrição
        ctk.CTkLabel(scroll, text="Descrição *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        desc_entry = ctk.CTkEntry(scroll, height=35, font=ctk.CTkFont(size=13))
        desc_entry.pack(fill="x", pady=(2, 8))

        # Categoria
        ctk.CTkLabel(scroll, text="Categoria *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        cat_labels = [v for _, v in self.expense_categories]
        cat_var = ctk.StringVar(value=cat_labels[0] if cat_labels else "Geral")
        ctk.CTkOptionMenu(scroll, values=cat_labels, variable=cat_var,
                          font=ctk.CTkFont(size=12), height=35).pack(fill="x", pady=(2, 8))

        # Valor
        ctk.CTkLabel(scroll, text="Valor (R$) *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        amount_entry = ctk.CTkEntry(scroll, height=35, font=ctk.CTkFont(size=13))
        amount_entry.pack(fill="x", pady=(2, 8))

        # Data
        ctk.CTkLabel(scroll, text="Data (DD/MM/AAAA)", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        date_entry = DateEntry(scroll)
        date_entry.pack(fill="x", pady=(2, 8))

        # Observações
        ctk.CTkLabel(scroll, text="Observações", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        notes_text = ctk.CTkTextbox(scroll, height=60, font=ctk.CTkFont(size=12))
        notes_text.pack(fill="x", pady=(2, 12))

        # Preencher se edição
        if existing:
            desc_entry.insert(0, existing.get("description", ""))
            cat_key = existing.get("category", "geral")
            cat_var.set(self.category_map.get(cat_key, cat_labels[0] if cat_labels else "Geral"))
            amount_entry.insert(0, str(existing.get("amount", 0)))
            if existing.get("expense_date"):
                date_entry.set(str(existing["expense_date"])[:10])
            if existing.get("notes"):
                notes_text.insert("1.0", existing["notes"])

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar", font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"), width=100, height=38,
            command=dialog.destroy,
        ).pack(side="left")

        def save():
            desc = desc_entry.get().strip()
            if not desc:
                self.app.show_toast("Descrição é obrigatória.", "error")
                return
            try:
                amount = parse_decimal(amount_entry.get() or "0")
                if amount <= 0:
                    self.app.show_toast("Valor deve ser maior que zero.", "error")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido.", "error")
                return

            rev_map = {v: k for k, v in self.expense_categories}
            category = rev_map.get(cat_var.get(), self.expense_categories[0][0] if self.expense_categories else "geral")
            expense_date = date_entry.get_iso().strip() or None
            notes = notes_text.get("1.0", "end-1c").strip()

            try:
                if existing:
                    db.update_expense(
                        existing["id"],
                        description=desc,
                        category=category,
                        amount=amount,
                        expense_date=expense_date,
                        notes=notes,
                    )
                    self.app.show_toast("Despesa atualizada!", "success")
                else:
                    db.create_expense(
                        description=desc,
                        category=category,
                        amount=amount,
                        expense_date=expense_date,
                        notes=notes,
                    )
                    self.app.show_toast("Despesa registrada!", "success")

                dialog.destroy()
                self._build_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            btn_frame, text="💾 Salvar", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            width=150, height=38, corner_radius=10,
            command=save,
        ).pack(side="right")

    def _confirm_delete(self, expense):
        ConfirmDialog(
            self.app,
            "Excluir Despesa",
            f"Excluir despesa \"{expense.get('description', '')}\"?",
            lambda eid=expense["id"]: self._delete_expense(eid),
        )

    def _delete_expense(self, expense_id):
        db.delete_expense(expense_id)
        self.app.show_toast("Despesa excluída.", "success")
        self._build_list()

    def _open_categories_manager(self):
        """Abre diálogo para gerenciar categorias de despesas."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Gerenciar Categorias de Despesas")
        dialog.geometry("600x500")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 600) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        # Header
        header = ctk.CTkFrame(dialog, fg_color=COLORS["card"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚙️ Categorias de Despesas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            header, text="+ Nova Categoria",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=32, corner_radius=8,
            command=lambda: self._open_category_form(dialog),
        ).pack(side="right", padx=20)

        # Lista de categorias
        list_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=15)

        def load_categories():
            for w in list_frame.winfo_children():
                w.destroy()

            categories = db.get_all_expense_categories()

            ctk.CTkLabel(
                list_frame, text=f"{len(categories)} categoria(s)",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w", pady=(0, 10))

            for cat in categories:
                card = ctk.CTkFrame(list_frame, fg_color=COLORS["card"], corner_radius=8,
                                    border_width=1, border_color=COLORS["border"])
                card.pack(fill="x", pady=3)

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=12, pady=8)

                # Color badge
                color_badge = ctk.CTkFrame(inner, fg_color=cat['color'], width=30, height=30,
                                           corner_radius=5)
                color_badge.pack(side="left", padx=(0, 12))
                color_badge.pack_propagate(False)

                # Info
                info = ctk.CTkFrame(inner, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    info, text=cat['label'],
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLORS["text"],
                ).pack(anchor="w")

                ctk.CTkLabel(
                    info, text=f"Chave: {cat['key']}",
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"],
                ).pack(anchor="w")

                # Actions
                actions = ctk.CTkFrame(inner, fg_color="transparent")
                actions.pack(side="right")

                ctk.CTkButton(
                    actions, text="✏️", width=30, height=28,
                    fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                    corner_radius=6,
                    command=lambda c=cat: self._open_category_form(dialog, c, load_categories),
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    actions, text="🗑", width=30, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda c=cat: self._confirm_delete_category(c, load_categories),
                ).pack(side="left", padx=2)

        load_categories()

    def _open_category_form(self, parent_dialog, existing=None, reload_callback=None):
        """Formulário para criar/editar categoria."""
        form = ctk.CTkToplevel(parent_dialog)
        form.title("Editar Categoria" if existing else "Nova Categoria")
        form.geometry("800x600")
        form.grab_set()
        form.transient(parent_dialog)

        form.update_idletasks()
        x = parent_dialog.winfo_x() + (parent_dialog.winfo_width() - 800) // 2
        y = parent_dialog.winfo_y() + (parent_dialog.winfo_height() - 600) // 2
        form.geometry(f"+{x}+{y}")

        content = ctk.CTkFrame(form, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            content, text="📂 Categoria de Despesa",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(0, 15))

        # Chave (só na criação)
        if not existing:
            ctk.CTkLabel(
                content, text="Chave (identificador único) *",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w")
            key_entry = ctk.CTkEntry(content, height=35, font=ctk.CTkFont(size=13),
                                     placeholder_text="Ex: material_construcao")
            key_entry.pack(fill="x", pady=(2, 8))

        # Label
        ctk.CTkLabel(
            content, text="Nome *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        label_entry = ctk.CTkEntry(content, height=35, font=ctk.CTkFont(size=13),
                                   placeholder_text="Ex: Material de Construção")
        label_entry.pack(fill="x", pady=(2, 8))

        # Color
        ctk.CTkLabel(
            content, text="Cor *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(8, 5))

        # Variável para armazenar cor selecionada
        selected_color = ctk.StringVar(value=existing['color'] if existing else "#6b7280")

        # Container do seletor de cor
        color_container = ctk.CTkFrame(content, fg_color=COLORS["card"],
                                       corner_radius=10, border_width=1,
                                       border_color=COLORS["border"])
        color_container.pack(fill="x", pady=(0, 12))

        # Preview da cor selecionada
        color_preview_frame = ctk.CTkFrame(color_container, fg_color="transparent")
        color_preview_frame.pack(fill="x", padx=15, pady=12)

        color_preview = ctk.CTkFrame(color_preview_frame,
                                     fg_color=selected_color.get(),
                                     width=60, height=60,
                                     corner_radius=8,
                                     border_width=2,
                                     border_color=COLORS["border"])
        color_preview.pack(side="left", padx=(0, 15))
        color_preview.pack_propagate(False)

        # Info da cor
        color_info_frame = ctk.CTkFrame(color_preview_frame, fg_color="transparent")
        color_info_frame.pack(side="left", fill="both", expand=True)

        color_label = ctk.CTkLabel(color_info_frame,
                                   text=selected_color.get(),
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   text_color=COLORS["text"])
        color_label.pack(anchor="w")

        ctk.CTkLabel(color_info_frame,
                    text="Clique no botão abaixo para escolher uma cor",
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(2, 0))

        def open_color_picker():
            try:
                from tkcolorpicker import askcolor
                color_result = askcolor(selected_color.get(), form, title="Escolher Cor")
                if color_result and color_result[1]:
                    new_color = color_result[1]
                    selected_color.set(new_color)
                    color_preview.configure(fg_color=new_color)
                    color_label.configure(text=new_color)
            except ImportError:
                # Fallback para palleta de cores simples se tkcolorpicker não estiver disponível
                self._show_color_palette(form, selected_color, color_preview, color_label)

        ctk.CTkButton(
            color_preview_frame, text="🎨 Escolher Cor",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=35, width=150, corner_radius=8,
            command=open_color_picker,
        ).pack(side="right")

        # Preencher se edição
        if existing:
            label_entry.insert(0, existing['label'])

        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"),
            width=100, height=38,
            command=form.destroy,
        ).pack(side="left")

        def save():
            label = label_entry.get().strip()
            color = selected_color.get() or "#6b7280"

            if not label:
                self.app.show_toast("Nome é obrigatório.", "error")
                return

            if not existing:
                key = key_entry.get().strip()
                if not key:
                    self.app.show_toast("Chave é obrigatória.", "error")
                    return
                try:
                    db.create_expense_category(key, label, color)
                    self.app.show_toast("Categoria criada!", "success")
                    form.destroy()
                    if reload_callback:
                        reload_callback()
                    self._load_categories()
                    self._build_list()
                except ValueError as e:
                    self.app.show_toast(str(e), "error")
            else:
                db.update_expense_category(existing['id'], label, color)
                self.app.show_toast("Categoria atualizada!", "success")
                form.destroy()
                if reload_callback:
                    reload_callback()
                self._load_categories()
                self._build_list()

        ctk.CTkButton(
            btn_frame, text="💾 Salvar",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            width=150, height=38, corner_radius=10,
            command=save,
        ).pack(side="right")

    def _show_color_palette(self, parent, color_var, preview_frame, label_widget):
        """Mostra paleta de cores visual quando tkcolorpicker não está disponível."""
        palette_dialog = ctk.CTkToplevel(parent)
        palette_dialog.title("Escolher Cor")
        palette_dialog.geometry("500x450")
        palette_dialog.grab_set()
        palette_dialog.transient(parent)

        palette_dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        palette_dialog.geometry(f"+{x}+{y}")

        main_frame = ctk.CTkFrame(palette_dialog, fg_color=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame, text="🎨 Selecione uma Cor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(0, 15))

        # Paleta de cores predefinidas
        colors_palette = [
            ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16", "#22c55e"],
            ["#10b981", "#14b8a6", "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1"],
            ["#8b5cf6", "#a855f7", "#d946ef", "#ec4899", "#f43f5e", "#fb7185"],
            ["#64748b", "#6b7280", "#71717a", "#78716c", "#57534e", "#44403c"],
            ["#dc2626", "#ea580c", "#d97706", "#ca8a04", "#65a30d", "#16a34a"],
            ["#059669", "#0d9488", "#0891b2", "#0284c7", "#2563eb", "#4f46e5"],
            ["#7c3aed", "#9333ea", "#c026d3", "#db2777", "#e11d48", "#be123c"],
            ["#475569", "#52525b", "#737373", "#a8a29e", "#d4d4d8", "#e7e5e4"],
        ]

        # Grid de cores
        colors_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        colors_grid.pack(fill="both", expand=True, pady=(0, 15))

        for row_idx, color_row in enumerate(colors_palette):
            row_frame = ctk.CTkFrame(colors_grid, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            
            for col_idx, color in enumerate(color_row):
                def make_callback(c):
                    return lambda: self._select_color(c, color_var, preview_frame, label_widget, palette_dialog)
                
                color_btn = ctk.CTkButton(
                    row_frame, text="",
                    fg_color=color,
                    hover_color=color,
                    width=70, height=45,
                    corner_radius=8,
                    border_width=2,
                    border_color=COLORS["border"] if color != color_var.get() else "#ffffff",
                    command=make_callback(color),
                )
                color_btn.pack(side="left", padx=3)

        # Input manual
        manual_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["card"],
                                    corner_radius=8, border_width=1,
                                    border_color=COLORS["border"])
        manual_frame.pack(fill="x", pady=(10, 0))
        
        manual_content = ctk.CTkFrame(manual_frame, fg_color="transparent")
        manual_content.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            manual_content, text="Ou digite uma cor hexadecimal:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 10))

        hex_entry = ctk.CTkEntry(manual_content, height=32, width=120,
                                 font=ctk.CTkFont(size=12),
                                 placeholder_text="#000000")
        hex_entry.pack(side="left", padx=(0, 8))
        hex_entry.insert(0, color_var.get())

        def apply_custom():
            custom_color = hex_entry.get().strip()
            if custom_color and custom_color.startswith('#') and len(custom_color) == 7:
                self._select_color(custom_color, color_var, preview_frame, label_widget, palette_dialog)
            else:
                self.app.show_toast("Cor inválida. Use formato #RRGGBB", "error")

        ctk.CTkButton(
            manual_content, text="Aplicar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            width=80, height=32, corner_radius=6,
            command=apply_custom,
        ).pack(side="left")

    def _select_color(self, color, color_var, preview_frame, label_widget, dialog):
        """Seleciona uma cor e atualiza a preview."""
        color_var.set(color)
        preview_frame.configure(fg_color=color)
        label_widget.configure(text=color)
        dialog.destroy()

    def _confirm_delete_category(self, category, reload_callback):
        """Confirma exclusão de categoria."""
        def delete():
            try:
                db.delete_expense_category(category['id'])
                self.app.show_toast("Categoria excluída.", "success")
                reload_callback()
                self._load_categories()
                self._build_list()
            except ValueError as e:
                self.app.show_toast(str(e), "error")

        ConfirmDialog(
            self.app,
            "Excluir Categoria",
            f"Excluir categoria \"{category['label']}\"?\n\nEsta ação não poderá ser desfeita se a categoria não estiver em uso.",
            delete,
        )
