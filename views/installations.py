# -*- coding: utf-8 -*-
"""
CalhaGest - Gestão de Instalações
Agendamento e acompanhamento de instalações vinculadas a orçamentos.
Com calendário interativo, campo de horário e formatação DD/MM/AAAA.
"""

import customtkinter as ctk
import calendar
from datetime import datetime, date
from database import db
from components.cards import StatusBadge, create_header
from theme import get_color, COLORS
from components.dialogs import (
    ConfirmDialog, format_currency, format_date, DateEntry, TimeEntry
)


STATUS_OPTIONS = ["Todos", "Pendente", "Em Progresso", "Concluída", "Cancelada"]
STATUS_MAP = {
    "Todos": "", "Pendente": "pending", "Em Progresso": "in-progress",
    "Concluída": "completed", "Cancelada": "cancelled",
}

CAL_COLORS = {
    "today_bg": "#2563eb",
    "today_fg": "#ffffff",
    "pending_bg": "#fef3c7",
    "pending_dot": "#f59e0b",
    "completed_bg": "#d1fae5",
    "completed_dot": "#10b981",
    "inprogress_bg": "#dbeafe",
    "inprogress_dot": "#3b82f6",
    "header_bg": "#1e293b",
    "header_fg": "#ffffff",
    "weekend_fg": "#94a3b8",
    "day_hover": "#eff6ff",
    "day_normal": "#ffffff",
    "day_fg": "#1e293b",
    "other_month_fg": "#cbd5e1",
}


class InstallationsView(ctk.CTkFrame):
    """View de gestão de instalações com calendário."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.status_filter = ""
        self.cal_year = datetime.now().year
        self.cal_month = datetime.now().month
        self._installations_cache = []
        self._build()

    def _build(self):
        # Cabeçalho
        header = create_header(
            self, "Instalações", "Agende e acompanhe instalações",
            action_text="Nova Instalação", action_command=self._open_create_dialog
        )
        header.pack(fill="x", pady=(0, 12))

        # Corpo principal: Calendário (esquerda) + Lista (direita)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # === CALENDÁRIO ===
        cal_card = ctk.CTkFrame(body, fg_color=COLORS["card"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
        cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.cal_container = ctk.CTkFrame(cal_card, fg_color="transparent")
        self.cal_container.pack(fill="both", expand=True, padx=12, pady=12)

        # === LISTA ===
        list_card = ctk.CTkFrame(body, fg_color=COLORS["card"], corner_radius=12,
                                  border_width=1, border_color=COLORS["border"])
        list_card.grid(row=0, column=1, sticky="nsew")

        # Filtro
        filter_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=12, pady=(12, 8))

        self.filter_var = ctk.StringVar(value="Todos")
        ctk.CTkSegmentedButton(
            filter_frame,
            values=STATUS_OPTIONS,
            variable=self.filter_var,
            command=self._on_filter,
            font=ctk.CTkFont(size=11),
            height=32,
        ).pack(fill="x")

        # Lista scrollável
        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._refresh_all()

    def _refresh_all(self):
        """Recarrega calendário e lista."""
        self._installations_cache = db.get_all_installations(status_filter=self.status_filter)
        self._build_calendar()
        self._load_installations()

    def _on_filter(self, value):
        self.status_filter = STATUS_MAP.get(value, "")
        self._refresh_all()

    # ==================== CALENDÁRIO ====================

    def _build_calendar(self):
        for w in self.cal_container.winfo_children():
            w.destroy()

        now = datetime.now()

        # Navegação do mês
        nav = ctk.CTkFrame(self.cal_container, fg_color=CAL_COLORS["header_bg"],
                            corner_radius=10)
        nav.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            nav, text="◀", width=36, height=36, corner_radius=8,
            fg_color="transparent", hover_color=get_color("sidebar_hover"),
            text_color=CAL_COLORS["header_fg"],
            font=ctk.CTkFont(size=16),
            command=self._prev_month,
        ).pack(side="left", padx=6, pady=6)

        month_names = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        ctk.CTkLabel(
            nav, text=f"{month_names[self.cal_month]} {self.cal_year}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CAL_COLORS["header_fg"],
        ).pack(side="left", expand=True)

        ctk.CTkButton(
            nav, text="▶", width=36, height=36, corner_radius=8,
            fg_color="transparent", hover_color=get_color("sidebar_hover"),
            text_color=CAL_COLORS["header_fg"],
            font=ctk.CTkFont(size=16),
            command=self._next_month,
        ).pack(side="right", padx=6, pady=6)

        # Dias da semana
        days_header = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        days_header.pack(fill="x")
        for i, day_name in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
            color = CAL_COLORS["weekend_fg"] if i >= 5 else COLORS["text_secondary"]
            ctk.CTkLabel(
                days_header, text=day_name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color, width=40,
            ).pack(side="left", expand=True)

        # Grade de dias
        grid = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=(4, 0))
        for c in range(7):
            grid.grid_columnconfigure(c, weight=1)

        # Mapear instalações por dia
        inst_by_day = {}
        for inst in self._installations_cache:
            sd = inst.get("scheduled_date", "")
            if sd:
                try:
                    d = str(sd)[:10]
                    parts = d.split("-")
                    if len(parts) == 3:
                        idate = date(int(parts[0]), int(parts[1]), int(parts[2]))
                        if idate.year == self.cal_year and idate.month == self.cal_month:
                            inst_by_day.setdefault(idate.day, []).append(inst)
                except (ValueError, IndexError):
                    pass

        cal_obj = calendar.Calendar(firstweekday=0)
        weeks = cal_obj.monthdayscalendar(self.cal_year, self.cal_month)

        for row_idx, week in enumerate(weeks):
            grid.grid_rowconfigure(row_idx, weight=1)
            for col_idx, day_num in enumerate(week):
                cell = ctk.CTkFrame(grid, corner_radius=6, fg_color="transparent")
                cell.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")

                if day_num == 0:
                    # Dia fora do mês
                    continue

                is_today = (
                    day_num == now.day
                    and self.cal_month == now.month
                    and self.cal_year == now.year
                )

                day_insts = inst_by_day.get(day_num, [])
                has_pending = any(
                    i.get("status") in ("pending", "in-progress") for i in day_insts
                )
                has_completed = any(
                    i.get("status") == "completed" for i in day_insts
                )

                # Cor de fundo
                if is_today:
                    bg = CAL_COLORS["today_bg"]
                    fg = CAL_COLORS["today_fg"]
                elif has_pending:
                    bg = CAL_COLORS["pending_bg"]
                    fg = CAL_COLORS["day_fg"]
                elif has_completed:
                    bg = CAL_COLORS["completed_bg"]
                    fg = CAL_COLORS["day_fg"]
                else:
                    bg = CAL_COLORS["day_normal"]
                    fg = CAL_COLORS["day_fg"]

                cell.configure(fg_color=bg)

                # Número do dia
                day_label = ctk.CTkLabel(
                    cell, text=str(day_num),
                    font=ctk.CTkFont(size=13, weight="bold" if is_today or day_insts else "normal"),
                    text_color=fg,
                )
                day_label.pack(pady=(4, 0))

                # Indicadores de instalações
                if day_insts:
                    dots_frame = ctk.CTkFrame(cell, fg_color="transparent", height=8)
                    dots_frame.pack(pady=(0, 2))
                    count = min(len(day_insts), 3)
                    for inst in day_insts[:count]:
                        st = inst.get("status", "pending")
                        if st == "completed":
                            dot_color = CAL_COLORS["completed_dot"]
                        elif st == "in-progress":
                            dot_color = CAL_COLORS["inprogress_dot"]
                        else:
                            dot_color = CAL_COLORS["pending_dot"]
                        ctk.CTkFrame(
                            dots_frame, width=8, height=8,
                            corner_radius=4, fg_color=dot_color,
                        ).pack(side="left", padx=1)
                    if len(day_insts) > 3:
                        ctk.CTkLabel(
                            dots_frame, text=f"+{len(day_insts)-3}",
                            font=ctk.CTkFont(size=8),
                            text_color=COLORS["text_secondary"],
                        ).pack(side="left", padx=1)

                # Click para ver detalhes do dia (instalações + orçamentos)
                cell.configure(cursor="hand2")
                cell.bind("<Button-1>", lambda e, d=day_num: self._show_day_history(d))
                for child in cell.winfo_children():
                    child.bind("<Button-1>", lambda e, d=day_num: self._show_day_history(d))

        # Legenda
        legend = ctk.CTkFrame(self.cal_container, fg_color="transparent")
        legend.pack(fill="x", pady=(8, 0))

        legend_items = [
            (CAL_COLORS["today_bg"], "Hoje"),
            (CAL_COLORS["pending_dot"], "Pendente"),
            (CAL_COLORS["inprogress_dot"], "Em Progresso"),
            (CAL_COLORS["completed_dot"], "Concluída"),
        ]
        for color, text in legend_items:
            item = ctk.CTkFrame(legend, fg_color="transparent")
            item.pack(side="left", padx=6)
            ctk.CTkFrame(item, width=10, height=10, corner_radius=5,
                         fg_color=color).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(item, text=text, font=ctk.CTkFont(size=10),
                         text_color=COLORS["text_secondary"]).pack(side="left")

    def _prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        self._refresh_all()

    def _next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        self._refresh_all()

    def _show_day_detail(self, day_num):
        """Mostra instalações do dia clicado na lista."""
        target_date = f"{self.cal_year}-{self.cal_month:02d}-{day_num:02d}"
        self._load_installations(filter_date=target_date)

    def _show_day_history(self, day_num):
        """Mostra instalações do dia com detalhes expandíveis."""
        target_date = f"{self.cal_year}-{self.cal_month:02d}-{day_num:02d}"
        
        # Buscar instalações
        day_installations = [
            i for i in self._installations_cache
            if str(i.get("scheduled_date", ""))[:10] == target_date
        ]
        
        # Criar dialog
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Instalações - {day_num:02d}/{self.cal_month:02d}/{self.cal_year}")
        dialog.geometry("550x450")
        dialog.grab_set()
        dialog.transient(self.app)
        
        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 550) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 450) // 2
        dialog.geometry(f"+{x}+{y}")
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        ctk.CTkLabel(
            scroll,
            text=f"📅 Instalações de {day_num:02d}/{self.cal_month:02d}/{self.cal_year}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(0, 15))
        
        def refresh_dialog():
            """Recarrega o conteúdo do dialog."""
            # Atualizar cache e buscar novamente
            self._installations_cache = db.get_all_installations(status_filter=self.status_filter)
            updated_installations = [
                i for i in self._installations_cache
                if str(i.get("scheduled_date", ""))[:10] == target_date
            ]
            
            # Limpar conteúdo (exceto título)
            children = scroll.winfo_children()
            for child in children[1:]:  # Pular o título
                child.destroy()
            
            if updated_installations:
                for inst in updated_installations:
                    self._create_day_installation_card(scroll, inst, dialog, refresh_dialog)
            else:
                ctk.CTkLabel(
                    scroll,
                    text="Nenhuma instalação neste dia.",
                    font=ctk.CTkFont(size=13),
                    text_color=COLORS["text_secondary"],
                ).pack(pady=40)
            
            # Botão fechar
            ctk.CTkButton(
                scroll, text="Fechar", fg_color=get_color("primary"),
                hover_color=get_color("primary_hover"), height=36,
                command=dialog.destroy,
            ).pack(pady=(15, 0))
        
        # Instalações
        if day_installations:
            for inst in day_installations:
                self._create_day_installation_card(scroll, inst, dialog, refresh_dialog)
        else:
            ctk.CTkLabel(
                scroll,
                text="Nenhuma instalação neste dia.",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
            ).pack(pady=40)
        
        # Botão fechar
        ctk.CTkButton(
            scroll, text="Fechar", fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"), height=36,
            command=dialog.destroy,
        ).pack(pady=(15, 0))

    def _create_day_installation_card(self, parent, inst, dialog, refresh_callback):
        """Cria card de instalação no dialog do dia com detalhes e ação de remover."""
        status = inst.get("status", "pending")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=4)
        
        # Cabeçalho do card (sempre visível)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 0))
        
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            left, text=inst.get("client_name", "-"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(side="left")
        
        StatusBadge(header, status).pack(side="right")
        
        # Detalhes (horário, endereço, descrição)
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.pack(fill="x", padx=12, pady=(6, 0))
        
        # Horário
        sched = str(inst.get("scheduled_date", ""))
        time_str = ""
        if len(sched) > 10 and " " in sched:
            time_part = sched.split(" ")[1][:5]
            if time_part and time_part != "00:00":
                time_str = time_part
        
        if time_str:
            ctk.CTkLabel(
                details_frame, text=f"🕐 Horário: {time_str}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["primary"], anchor="w",
            ).pack(anchor="w", pady=(0, 2))
        
        # Endereço
        addr = inst.get("address", "") or ""
        if addr:
            ctk.CTkLabel(
                details_frame, text=f"📍 {addr}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"], anchor="w",
            ).pack(anchor="w", pady=(0, 2))
        
        # Notas/Descrição
        notes = inst.get("notes", "") or ""
        if notes:
            ctk.CTkLabel(
                details_frame, text=f"📝 {notes}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"], anchor="w",
                wraplength=450, justify="left",
            ).pack(anchor="w", pady=(0, 2))
        
        # Valor do orçamento
        total = inst.get("total", 0)
        if total:
            ctk.CTkLabel(
                details_frame, text=f"💰 {format_currency(total)}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary"], anchor="w",
            ).pack(anchor="w", pady=(0, 2))
        
        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(6, 10))
        
        if status == "pending":
            ctk.CTkButton(
                btn_frame, text="▶ Iniciar", font=ctk.CTkFont(size=11),
                fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
                width=80, height=30, corner_radius=8,
                command=lambda: (self._update_status(inst["id"], "in-progress"),
                                 refresh_callback()),
            ).pack(side="left", padx=(0, 5))
        
        if status == "in-progress":
            ctk.CTkButton(
                btn_frame, text="✅ Completar", font=ctk.CTkFont(size=11),
                fg_color=get_color("success"), hover_color=get_color("success_hover"),
                width=100, height=30, corner_radius=8,
                command=lambda: (self._update_status(inst["id"], "completed"),
                                 refresh_callback()),
            ).pack(side="left", padx=(0, 5))
        
        def delete_and_refresh():
            db.delete_installation(inst["id"])
            self.app.show_toast("Instalação removida.", "success")
            self._refresh_all()
            refresh_callback()
        
        ctk.CTkButton(
            btn_frame, text="🗑️ Remover", font=ctk.CTkFont(size=11),
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=90, height=30, corner_radius=8,
            command=lambda: ConfirmDialog(
                self.app, "Remover Instalação",
                f"Remover instalação de {inst.get('client_name', '-')}?",
                delete_and_refresh,
            ),
        ).pack(side="right")

    # ==================== LISTA ====================

    def _load_installations(self, filter_date=None):
        for w in self.list_frame.winfo_children():
            w.destroy()

        installations = self._installations_cache

        if filter_date:
            installations = [
                i for i in installations
                if str(i.get("scheduled_date", ""))[:10] == filter_date
            ]
            # Mostrar data filtrada
            parts = filter_date.split("-")
            if len(parts) == 3:
                date_label = f"{parts[2]}/{parts[1]}/{parts[0]}"
            else:
                date_label = filter_date

            reset_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            reset_frame.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(
                reset_frame, text=f"📅 {date_label}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["primary"],
            ).pack(side="left")
            ctk.CTkButton(
                reset_frame, text="✕ Limpar filtro", font=ctk.CTkFont(size=11),
                fg_color="transparent", text_color=COLORS["text_secondary"],
                hover_color=COLORS["border"], height=24, width=90,
                command=lambda: self._load_installations(),
            ).pack(side="right")

        ctk.CTkLabel(
            self.list_frame,
            text=f"{len(installations)} instalação(ões)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        if not installations:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhuma instalação encontrada.",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
            ).pack(pady=30)
            return

        for inst in installations:
            self._create_installation_card(inst)

    def _create_installation_card(self, inst):
        card = ctk.CTkFrame(
            self.list_frame,
            fg_color=COLORS["card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=3)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=10)

        # Info
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(anchor="w")

        ctk.CTkLabel(
            top_row,
            text=inst.get("client_name", "-"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        StatusBadge(top_row, inst.get("status", "pending")).pack(side="left", padx=(8, 0))

        # Data e horário
        sched = inst.get("scheduled_date", "")
        date_str = format_date(sched)
        # Extrair horário se existir (formato YYYY-MM-DD HH:MM)
        time_str = ""
        sched_s = str(sched)
        if len(sched_s) > 10 and " " in sched_s:
            time_part = sched_s.split(" ")[1][:5]
            if time_part and time_part != "00:00":
                time_str = f"  🕐 {time_part}"

        addr = inst.get("address", "-") or "-"
        details = f"📅 {date_str}{time_str}  •  📍 {addr}"
        ctk.CTkLabel(
            left,
            text=details,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        if inst.get("notes"):
            ctk.CTkLabel(
                left,
                text=f"📝 {inst['notes']}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_secondary"],
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

        # Botões de ação
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right")

        status = inst.get("status", "pending")

        if status == "pending":
            ctk.CTkButton(
                right, text="▶ Iniciar", font=ctk.CTkFont(size=10),
                fg_color=get_color("primary"), hover_color=get_color("primary_hover"),
                width=70, height=28, corner_radius=8,
                command=lambda i=inst: self._update_status(i["id"], "in-progress"),
            ).pack(side="left", padx=2)

        if status == "in-progress":
            ctk.CTkButton(
                right, text="✅ Completar", font=ctk.CTkFont(size=10),
                fg_color=get_color("success"), hover_color=get_color("success_hover"),
                width=85, height=28, corner_radius=8,
                command=lambda i=inst: self._update_status(i["id"], "completed"),
            ).pack(side="left", padx=2)

        if status in ("pending", "in-progress"):
            ctk.CTkButton(
                right, text="✕", font=ctk.CTkFont(size=10),
                fg_color=COLORS["error_light"], text_color=COLORS["error"],
                hover_color=COLORS["error_hover_light"],
                width=28, height=28, corner_radius=8,
                command=lambda i=inst: self._confirm_cancel(i),
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            right, text="🗑️", font=ctk.CTkFont(size=10),
            fg_color=COLORS["error_light"], text_color=COLORS["error"],
            hover_color=COLORS["error_hover_light"],
            width=28, height=28, corner_radius=8,
            command=lambda i=inst: self._confirm_delete(i),
        ).pack(side="left", padx=2)

    # ==================== DIÁLOGOS ====================

    def _open_create_dialog(self):
        """Abre diálogo para criar nova instalação com data DD/MM/AAAA e horário."""
        approved = db.get_all_quotes(status_filter="approved")
        if not approved:
            self.app.show_toast("Nenhum orçamento aprovado disponível.", "warning")
            return

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Nova Instalação")
        dialog.geometry("520x420")
        dialog.grab_set()
        dialog.transient(self.app)

        dialog.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() - 520) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - 420) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Selecionar orçamento
        ctk.CTkLabel(
            frame, text="Orçamento Aprovado *",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(0, 4))

        quote_options = [
            f"#{q['id']:05d} - {q['client_name']} ({format_currency(q['total'])})"
            for q in approved
        ]
        quote_map = {opt: q for opt, q in zip(quote_options, approved)}
        quote_var = ctk.StringVar(value=quote_options[0])

        ctk.CTkOptionMenu(
            frame, values=quote_options, variable=quote_var,
            font=ctk.CTkFont(size=12), height=35,
        ).pack(fill="x", pady=(0, 10))

        # Data e Horário na mesma linha
        datetime_frame = ctk.CTkFrame(frame, fg_color="transparent")
        datetime_frame.pack(fill="x", pady=(0, 10))
        datetime_frame.grid_columnconfigure(0, weight=2)
        datetime_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            datetime_frame, text="Data Agendada *",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            datetime_frame, text="Horário",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"],
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        date_entry = DateEntry(datetime_frame)
        date_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        time_entry = TimeEntry(datetime_frame)
        time_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))

        # Notas
        ctk.CTkLabel(
            frame, text="Notas Adicionais",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", pady=(8, 4))
        notes_text = ctk.CTkTextbox(frame, height=70, font=ctk.CTkFont(size=12))
        notes_text.pack(fill="x", pady=(0, 15))

        def save():
            sel_quote = quote_map.get(quote_var.get())
            if not sel_quote:
                self.app.show_toast("Selecione um orçamento.", "error")
                return
            date_str = date_entry.get_iso().strip()
            if not date_str or len(date_str) < 10:
                self.app.show_toast("Data é obrigatória (DD/MM/AAAA).", "error")
                return
            # Combinar data + horário
            time_str = time_entry.get().strip()
            if time_str and len(time_str) == 5:
                date_str = f"{date_str} {time_str}"
            try:
                notes = notes_text.get("1.0", "end-1c").strip()
                db.create_installation(sel_quote["id"], date_str, notes)
                dialog.destroy()
                self.app.show_toast("Instalação agendada!", "success")
                self._refresh_all()
            except Exception as e:
                self.app.show_toast(f"Erro: {e}", "error")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color=get_color("border"),
            text_color=get_color("text"), hover_color=get_color("border_hover"),
            width=100, height=36, command=dialog.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="📅 Agendar", fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"), width=120, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save,
        ).pack(side="right")

    def _update_status(self, installation_id, new_status):
        db.update_installation_status(installation_id, new_status)
        self.app.show_toast("Status atualizado!", "success")
        self._refresh_all()

    def _confirm_cancel(self, inst):
        ConfirmDialog(
            self.app, "Cancelar Instalação",
            f"Cancelar instalação de {inst['client_name']}?",
            lambda iid=inst["id"]: self._update_status(iid, "cancelled"),
        )

    def _confirm_delete(self, inst):
        ConfirmDialog(
            self.app, "Excluir Instalação",
            f"Excluir instalação de {inst['client_name']}?",
            lambda iid=inst["id"]: self._delete_installation(iid),
        )

    def _delete_installation(self, installation_id):
        db.delete_installation(installation_id)
        self.app.show_toast("Instalação excluída.", "success")
        self._refresh_all()
