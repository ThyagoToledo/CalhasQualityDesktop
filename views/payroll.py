# -*- coding: utf-8 -*-
"""
CalhaGest - Folha de Pagamento
Gerenciar funcionários e pagamentos de folha.
"""

import customtkinter as ctk
from datetime import datetime
from database import db
from components.cards import create_header
from theme import get_color, COLORS
from components.dialogs import ConfirmDialog, format_currency, format_date, parse_decimal


class PayrollView(ctk.CTkFrame):
    """View de gestão de folha de pagamento."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_list()

    def _build_list(self):
        for w in self.winfo_children():
            w.destroy()

        header = create_header(
            self, "Folha de Pagamento", "Gerencie funcionários e pagamentos",
            action_text="", action_command=None,
        )
        header.pack(fill="x", pady=(0, 15))

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="  👤 Novo Funcionário  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            height=38, corner_radius=10,
            command=self._open_employee_form,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="  💰 Registrar Pagamento  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            height=38, corner_radius=10,
            command=self._open_payroll_form,
        ).pack(side="left")

        # Resumo
        ps = db.get_payroll_summary()
        summary_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=12,
                                      border_width=1, border_color=COLORS["border"])
        summary_frame.pack(fill="x", pady=(0, 15))

        grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats_items = [
            ("👥 Funcionários", str(ps.get("active_employees", 0)), COLORS["primary"]),
            ("📅 Folha Prevista", format_currency(ps.get("expected_monthly", 0)), COLORS["warning"]),
            ("💰 Pago Este Mês", format_currency(ps.get("month_total", 0)), COLORS["success"]),
            ("💸 Total Pago", format_currency(ps.get("total_paid", 0)), COLORS["error"]),
        ]
        for col, (label, value, color) in enumerate(stats_items):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=0, column=col, padx=8, sticky="nsew")
            ctk.CTkFrame(cell, height=3, fg_color=color, corner_radius=2).pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack()
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=color).pack(pady=(2, 0))

        # Tabview: Funcionários | Pagamentos
        self.tabview = ctk.CTkTabview(
            self, fg_color=COLORS["card"], corner_radius=12,
            border_width=1, border_color=COLORS["border"],
            segmented_button_fg_color=get_color("border"),
            segmented_button_selected_color=get_color("primary"),
            segmented_button_selected_hover_color=get_color("primary_hover"),
            segmented_button_unselected_color=get_color("border"),
            segmented_button_unselected_hover_color=get_color("border_hover"),
            text_color=COLORS["text"],
        )
        self.tabview.pack(fill="both", expand=True)

        tab_emp = self.tabview.add("👥 Funcionários")
        tab_pay = self.tabview.add("💰 Pagamentos")

        self._fill_employees_tab(tab_emp)
        self._fill_payroll_tab(tab_pay)

    def _fill_employees_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        employees = db.get_all_employees(active_only=False)

        if not employees:
            ctk.CTkLabel(scroll, text="Nenhum funcionário cadastrado.",
                         font=ctk.CTkFont(size=14), text_color=COLORS["text_secondary"]).pack(pady=40)
            return

        for emp in employees:
            card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=3, padx=5)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=15, pady=10)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            name_text = emp.get("name", "-")
            active = emp.get("active", 1)
            if not active:
                name_text += " (Inativo)"
            ctk.CTkLabel(left, text=name_text,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=COLORS["text"] if active else COLORS["text_secondary"]).pack(anchor="w")

            info_parts = []
            if emp.get("role"):
                info_parts.append(f"Cargo: {emp['role']}")
            if emp.get("phone"):
                info_parts.append(f"📞 {emp['phone']}")
            info_parts.append(f"Salário: {format_currency(emp.get('salary', 0))}")
            ctk.CTkLabel(left, text="  |  ".join(info_parts),
                         font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).pack(anchor="w")

            # Ações
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            ctk.CTkButton(
                right, text="✏️", width=30, height=28,
                fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                corner_radius=6,
                command=lambda e=emp: self._open_employee_form(e),
            ).pack(side="left", padx=2)

            if active:
                ctk.CTkButton(
                    right, text="⏸", width=30, height=28,
                    fg_color=COLORS["error_light"], text_color=COLORS["error"],
                    hover_color=COLORS["error_hover_light"], corner_radius=6,
                    command=lambda e=emp: self._toggle_active(e, 0),
                ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(
                    right, text="▶", width=30, height=28,
                    fg_color=COLORS["success_light"], text_color=COLORS["success"],
                    hover_color=COLORS["success"], corner_radius=6,
                    command=lambda e=emp: self._toggle_active(e, 1),
                ).pack(side="left", padx=2)

            ctk.CTkButton(
                right, text="🗑", width=30, height=28,
                fg_color=COLORS["error_light"], text_color=COLORS["error"],
                hover_color=COLORS["error_hover_light"], corner_radius=6,
                command=lambda e=emp: self._confirm_delete_employee(e),
            ).pack(side="left", padx=2)

    def _fill_payroll_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Filtro por mês
        filter_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(5, 10), padx=5)

        ctk.CTkLabel(filter_frame, text="Filtrar mês (AAAA-MM):",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text"]).pack(side="left")

        self.month_filter_entry = ctk.CTkEntry(filter_frame, width=120, height=32,
                                                font=ctk.CTkFont(size=12),
                                                placeholder_text="Ex: 2025-02")
        self.month_filter_entry.pack(side="left", padx=8)

        ctk.CTkButton(
            filter_frame, text="Filtrar", height=32, width=70,
            font=ctk.CTkFont(size=11),
            fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
            command=lambda: self._reload_payroll(scroll),
        ).pack(side="left")

        ctk.CTkButton(
            filter_frame, text="Todos", height=32, width=60,
            font=ctk.CTkFont(size=11),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"),
            command=lambda: self._show_all_payroll(scroll),
        ).pack(side="left", padx=4)

        self._payroll_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._payroll_list_frame.pack(fill="both", expand=True)

        self._load_payroll_records(self._payroll_list_frame)

    def _reload_payroll(self, parent):
        month = self.month_filter_entry.get().strip()
        for w in self._payroll_list_frame.winfo_children():
            w.destroy()
        self._load_payroll_records(self._payroll_list_frame, month_filter=month)

    def _show_all_payroll(self, parent):
        self.month_filter_entry.delete(0, "end")
        for w in self._payroll_list_frame.winfo_children():
            w.destroy()
        self._load_payroll_records(self._payroll_list_frame)

    def _load_payroll_records(self, parent, month_filter=""):
        records = db.get_all_payroll(month_filter=month_filter)

        if not records:
            ctk.CTkLabel(parent, text="Nenhum pagamento de folha registrado.",
                         font=ctk.CTkFont(size=14), text_color=COLORS["text_secondary"]).pack(pady=30)
            return

        for rec in records:
            card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8,
                                 border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=2, padx=5)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(left, text=rec.get("employee_name", "-"),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=COLORS["text"]).pack(anchor="w")
            info = f"Ref: {rec.get('reference_month', '-')}  |  Data: {format_date(rec.get('payment_date', ''))}"
            if rec.get("employee_role"):
                info = f"{rec['employee_role']}  |  " + info
            if rec.get("notes"):
                info += f"  |  {rec['notes']}"
            ctk.CTkLabel(left, text=info, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_secondary"]).pack(anchor="w")

            ctk.CTkLabel(inner, text=format_currency(rec.get("amount", 0)),
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=COLORS["error"]).pack(side="right", padx=(10, 0))

            ctk.CTkButton(
                inner, text="🗑", width=28, height=28,
                fg_color=COLORS["error_light"], text_color=COLORS["error"],
                hover_color=COLORS["error_hover_light"], corner_radius=6,
                command=lambda r=rec: self._delete_payroll_record(r),
            ).pack(side="right")

    def _open_employee_form(self, existing=None):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Editar Funcionário" if existing else "Novo Funcionário")
        dialog.geometry("420x380")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 420) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 380) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(frame, text="👤 Funcionário",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        # Nome
        ctk.CTkLabel(frame, text="Nome *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        name_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13))
        name_entry.pack(fill="x", pady=(2, 8))

        # Cargo
        ctk.CTkLabel(frame, text="Cargo", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        role_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13))
        role_entry.pack(fill="x", pady=(2, 8))

        # Telefone e Salário
        row_frame = ctk.CTkFrame(frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 8))
        row_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row_frame, text="Telefone", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        phone_entry = ctk.CTkEntry(row_frame, height=35, font=ctk.CTkFont(size=13))
        phone_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkLabel(row_frame, text="Salário (R$)", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        salary_entry = ctk.CTkEntry(row_frame, height=35, font=ctk.CTkFont(size=13))
        salary_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        if existing:
            name_entry.insert(0, existing.get("name", ""))
            role_entry.insert(0, existing.get("role", "") or "")
            phone_entry.insert(0, existing.get("phone", "") or "")
            salary_entry.insert(0, str(existing.get("salary", 0)))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"), width=100, height=38,
            command=dialog.destroy,
        ).pack(side="left")

        def save():
            name = name_entry.get().strip()
            if not name:
                self.app.show_toast("Nome é obrigatório.", "error")
                return
            try:
                salary = parse_decimal(salary_entry.get() or "0")
            except ValueError:
                self.app.show_toast("Salário inválido.", "error")
                return
            try:
                if existing:
                    db.update_employee(
                        existing["id"],
                        name=name,
                        role=role_entry.get().strip(),
                        phone=phone_entry.get().strip(),
                        salary=salary,
                    )
                    self.app.show_toast("Funcionário atualizado!", "success")
                else:
                    db.create_employee(
                        name=name,
                        role=role_entry.get().strip(),
                        phone=phone_entry.get().strip(),
                        salary=salary,
                    )
                    self.app.show_toast("Funcionário cadastrado!", "success")
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

    def _open_payroll_form(self):
        employees = db.get_all_employees(active_only=True)
        if not employees:
            self.app.show_toast("Cadastre funcionários antes de registrar pagamentos.", "warning")
            return

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Registrar Pagamento de Folha")
        dialog.geometry("420x400")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 420) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 400) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(frame, text="💰 Pagamento de Folha",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        # Funcionário
        ctk.CTkLabel(frame, text="Funcionário *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        emp_names = [f"{e['name']} ({e.get('role', '-')})" for e in employees]
        emp_var = ctk.StringVar(value=emp_names[0])
        ctk.CTkOptionMenu(frame, values=emp_names, variable=emp_var,
                          font=ctk.CTkFont(size=12), height=35).pack(fill="x", pady=(2, 8))

        # Valor
        ctk.CTkLabel(frame, text="Valor (R$) *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        amount_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13))
        amount_entry.pack(fill="x", pady=(2, 8))
        # Preencher com salário do primeiro funcionário
        amount_entry.insert(0, str(employees[0].get("salary", 0)))

        def on_emp_change(val):
            idx = emp_names.index(val) if val in emp_names else 0
            amount_entry.delete(0, "end")
            amount_entry.insert(0, str(employees[idx].get("salary", 0)))

        emp_var.trace_add("write", lambda *_: on_emp_change(emp_var.get()))

        # Mês de referência
        ctk.CTkLabel(frame, text="Mês Referência (AAAA-MM) *", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        month_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13),
                                    placeholder_text="Ex: 2025-02")
        month_entry.pack(fill="x", pady=(2, 8))
        month_entry.insert(0, datetime.now().strftime("%Y-%m"))

        # Observações
        ctk.CTkLabel(frame, text="Observações", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        notes_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13))
        notes_entry.pack(fill="x", pady=(2, 12))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", font=ctk.CTkFont(size=13),
            fg_color=get_color("border"), text_color=get_color("text"),
            hover_color=get_color("border_hover"), width=100, height=38,
            command=dialog.destroy,
        ).pack(side="left")

        def save():
            sel = emp_var.get()
            idx = emp_names.index(sel) if sel in emp_names else 0
            employee = employees[idx]

            try:
                amount = parse_decimal(amount_entry.get() or "0")
                if amount <= 0:
                    self.app.show_toast("Valor deve ser maior que zero.", "error")
                    return
            except ValueError:
                self.app.show_toast("Valor inválido.", "error")
                return

            ref_month = month_entry.get().strip()
            if not ref_month:
                self.app.show_toast("Mês de referência é obrigatório.", "error")
                return

            try:
                db.add_payroll(
                    employee_id=employee["id"],
                    amount=amount,
                    reference_month=ref_month,
                    notes=notes_entry.get().strip(),
                )
                self.app.show_toast(f"Pagamento registrado para {employee['name']}!", "success")
                dialog.destroy()
                self._build_list()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        ctk.CTkButton(
            btn_frame, text="💾 Registrar", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=get_color("success"), hover_color=get_color("success_hover"),
            width=150, height=38, corner_radius=10,
            command=save,
        ).pack(side="right")

    def _toggle_active(self, employee, active):
        db.update_employee(employee["id"], active=active)
        status = "ativado" if active else "desativado"
        self.app.show_toast(f"Funcionário {status}.", "success")
        self._build_list()

    def _confirm_delete_employee(self, employee):
        ConfirmDialog(
            self.app,
            "Excluir Funcionário",
            f"Excluir funcionário \"{employee.get('name', '')}\" e todos os seus pagamentos?",
            lambda eid=employee["id"]: self._do_delete_employee(eid),
        )

    def _do_delete_employee(self, emp_id):
        db.delete_employee(emp_id)
        self.app.show_toast("Funcionário excluído.", "success")
        self._build_list()

    def _delete_payroll_record(self, record):
        ConfirmDialog(
            self.app,
            "Excluir Pagamento",
            f"Excluir pagamento de {format_currency(record.get('amount', 0))} para {record.get('employee_name', '')}?",
            lambda pid=record["id"]: self._do_delete_payroll(pid),
        )

    def _do_delete_payroll(self, payroll_id):
        db.delete_payroll(payroll_id)
        self.app.show_toast("Pagamento excluído.", "success")
        self._build_list()
