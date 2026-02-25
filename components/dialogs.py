# -*- coding: utf-8 -*-
"""
CalhaGest - Diálogos e Notificações
Diálogos de confirmação, entrada e funções utilitárias de UI.
"""

import customtkinter as ctk
from datetime import datetime
from theme import get_color


class DateEntry(ctk.CTkFrame):
    """Campo de data com formatação automática DD/MM/AAAA."""

    def __init__(self, parent, placeholder="DD/MM/AAAA", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._var = ctk.StringVar()
        self._prev = ""
        self._block = False

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self._var,
            height=35,
            font=ctk.CTkFont(size=13),
            placeholder_text=placeholder,
        )
        self.entry.pack(fill="x")

        # Usar bind em vez de trace para ter controle preciso do cursor
        self.entry.bind("<KeyRelease>", self._on_key)

    def _format_digits(self, digits):
        """Formata dígitos puros em DD/MM/AAAA."""
        result = ""
        for i, d in enumerate(digits):
            if i == 2 or i == 4:
                result += "/"
            result += d
        return result

    def _on_key(self, event=None):
        """Chamado após cada tecla — formata e reposiciona o cursor."""
        if self._block:
            return
        self._block = True
        try:
            raw = self._var.get()

            # Capturar posição do cursor no texto cru
            try:
                old_cursor = self.entry.index(ctk.INSERT)
            except Exception:
                old_cursor = len(raw)

            # Extrair apenas dígitos, máximo 8
            digits = "".join(c for c in raw if c.isdigit())[:8]
            formatted = self._format_digits(digits)

            if formatted == raw:
                # Nada mudou, não precisa reposicionar
                self._prev = formatted
                return

            # Contar quantos dígitos estavam antes da posição do cursor no texto cru
            digits_before = sum(1 for c in raw[:old_cursor] if c.isdigit())

            # Atualizar o texto
            self._var.set(formatted)

            # Mapear: posição no texto formatado após 'digits_before' dígitos
            new_cursor = 0
            count = 0
            for i, c in enumerate(formatted):
                if c.isdigit():
                    count += 1
                if count == digits_before:
                    new_cursor = i + 1
                    break
            else:
                new_cursor = len(formatted)

            # Se caiu exatamente antes de uma barra, avançar para depois dela
            if new_cursor < len(formatted) and formatted[new_cursor] == '/':
                new_cursor += 1

            # Agendar reposicionamento para DEPOIS do widget processar o set()
            self.entry.after_idle(self._set_cursor, new_cursor)

            self._prev = formatted
        finally:
            self._block = False

    def _set_cursor(self, pos):
        """Reposiciona o cursor de forma segura, após o event-loop."""
        try:
            self.entry.icursor(pos)
        except Exception:
            pass

    def get(self):
        """Retorna a data digitada no formato DD/MM/AAAA."""
        return self._var.get()

    def get_iso(self):
        """Retorna a data em formato ISO AAAA-MM-DD para o banco de dados."""
        text = self._var.get()
        if len(text) == 10:
            parts = text.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return text

    def set(self, value):
        """Define a data. Aceita ISO (AAAA-MM-DD) ou BR (DD/MM/AAAA)."""
        self._block = True
        if value and "-" in str(value)[:10]:
            # Converter de ISO para BR
            parts = str(value)[:10].split("-")
            if len(parts) == 3:
                value = f"{parts[2]}/{parts[1]}/{parts[0]}"
        self._var.set(value or "")
        self._prev = self._var.get()
        self._block = False

    def delete(self, start, end):
        """Limpa o campo."""
        self._block = True
        self._var.set("")
        self._prev = ""
        self._block = False


class TimeEntry(ctk.CTkFrame):
    """Campo de horário com formatação automática HH:MM."""

    def __init__(self, parent, placeholder="HH:MM", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._var = ctk.StringVar()
        self._block = False

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self._var,
            height=35,
            font=ctk.CTkFont(size=13),
            placeholder_text=placeholder,
        )
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._on_key)

    def _on_key(self, event=None):
        if self._block:
            return
        self._block = True
        try:
            raw = self._var.get()
            try:
                old_cursor = self.entry.index(ctk.INSERT)
            except Exception:
                old_cursor = len(raw)

            digits = "".join(c for c in raw if c.isdigit())[:4]
            formatted = ""
            for i, d in enumerate(digits):
                if i == 2:
                    formatted += ":"
                formatted += d

            if formatted == raw:
                return

            digits_before = sum(1 for c in raw[:old_cursor] if c.isdigit())
            self._var.set(formatted)

            new_cursor = 0
            count = 0
            for i, c in enumerate(formatted):
                if c.isdigit():
                    count += 1
                if count == digits_before:
                    new_cursor = i + 1
                    break
            else:
                new_cursor = len(formatted)

            if new_cursor < len(formatted) and formatted[new_cursor] == ':':
                new_cursor += 1

            self.entry.after_idle(lambda: self._set_cursor(new_cursor))
        finally:
            self._block = False

    def _set_cursor(self, pos):
        try:
            self.entry.icursor(pos)
        except Exception:
            pass

    def get(self):
        """Retorna o horário digitado HH:MM."""
        return self._var.get()

    def set(self, value):
        """Define o horário."""
        self._block = True
        self._var.set(value or "")
        self._block = False

    def delete(self, start, end):
        self._block = True
        self._var.set("")
        self._block = False


class ConfirmDialog(ctk.CTkToplevel):
    """Diálogo de confirmação (Sim/Não)."""

    def __init__(self, parent, title, message, on_confirm):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        # Centralizar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 180) // 2
        self.geometry(f"+{x}+{y}")

        # Ícone de aviso
        ctk.CTkLabel(
            self, text="⚠️", font=ctk.CTkFont(size=32)
        ).pack(pady=(20, 5))

        # Mensagem
        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=get_color("text"),
            wraplength=350,
        ).pack(padx=20, pady=(0, 15))

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color=get_color("border"),
            text_color=get_color("text"),
            hover_color=get_color("border_hover"),
            width=120,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Confirmar",
            fg_color=get_color("error"),
            hover_color=get_color("error_hover"),
            width=120,
            command=self._confirm,
        ).pack(side="right", expand=True, padx=5)

    def _confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm()


class FormDialog(ctk.CTkToplevel):
    """Diálogo genérico com formulário."""

    def __init__(self, parent, title, fields, on_save, width=500, height=None,
                 initial_data=None):
        """
        Args:
            parent: Widget pai
            title: Título do diálogo
            fields: Lista de dicts com {key, label, type, options?, required?}
                    type: 'entry', 'text', 'option', 'number'
            on_save: Callback recebendo dict com valores
            initial_data: Dict com valores iniciais
        """
        super().__init__(parent)
        self.on_save = on_save
        self.entries = {}
        self.title(title)
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        # Calcular altura baseada na quantidade de campos
        if height is None:
            height = min(120 + len(fields) * 70, 650)
        self.geometry(f"{width}x{height}")

        # Centralizar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")

        # Área scrollável para campos
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(15, 5))

        initial_data = initial_data or {}

        for field in fields:
            key = field["key"]
            label = field.get("label", key)
            ftype = field.get("type", "entry")
            required = field.get("required", False)

            # Label
            lbl_text = f"{label} {'*' if required else ''}"
            ctk.CTkLabel(
                scroll,
                text=lbl_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=get_color("text"),
                anchor="w",
            ).pack(fill="x", pady=(8, 2))

            if ftype == "entry":
                entry = ctk.CTkEntry(scroll, height=35, font=ctk.CTkFont(size=13))
                if key in initial_data and initial_data[key]:
                    entry.insert(0, str(initial_data[key]))
                entry.pack(fill="x", pady=(0, 2))
                self.entries[key] = entry

            elif ftype == "number":
                entry = ctk.CTkEntry(scroll, height=35, font=ctk.CTkFont(size=13))
                if key in initial_data and initial_data[key] is not None:
                    entry.insert(0, str(initial_data[key]))
                entry.pack(fill="x", pady=(0, 2))
                self.entries[key] = entry

            elif ftype == "option":
                options = field.get("options", [])
                var = ctk.StringVar(
                    value=str(initial_data.get(key, options[0] if options else ""))
                )
                menu = ctk.CTkOptionMenu(
                    scroll,
                    values=options,
                    variable=var,
                    height=35,
                    font=ctk.CTkFont(size=13),
                )
                menu.pack(fill="x", pady=(0, 2))
                self.entries[key] = var

            elif ftype == "text":
                text = ctk.CTkTextbox(scroll, height=80, font=ctk.CTkFont(size=13))
                if key in initial_data and initial_data[key]:
                    text.insert("1.0", str(initial_data[key]))
                text.pack(fill="x", pady=(0, 2))
                self.entries[key] = text

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color=get_color("border"),
            text_color=get_color("text"),
            hover_color=get_color("border_hover"),
            width=120,
            command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Salvar",
            fg_color=get_color("primary"),
            hover_color=get_color("primary_hover"),
            width=120,
            command=self._save,
        ).pack(side="right", padx=5)

    def _save(self):
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry):
                data[key] = widget.get().strip()
            elif isinstance(widget, ctk.StringVar):
                data[key] = widget.get()
            elif isinstance(widget, ctk.CTkTextbox):
                data[key] = widget.get("1.0", "end-1c").strip()
            else:
                data[key] = ""
        self.destroy()
        if self.on_save:
            self.on_save(data)

    def get_values(self):
        """Retorna os valores atuais sem fechar."""
        data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry):
                data[key] = widget.get().strip()
            elif isinstance(widget, ctk.StringVar):
                data[key] = widget.get()
            elif isinstance(widget, ctk.CTkTextbox):
                data[key] = widget.get("1.0", "end-1c").strip()
        return data


def parse_decimal(value):
    """
    Converte string para float, aceitando vírgula ou ponto como separador decimal.
    Remove pontos de milhar (formato brasileiro).
    Exemplos: "1.250,50" -> 1250.50 | "1250.50" -> 1250.50 | "1250,50" -> 1250.50
    """
    if not value:
        return 0.0
    try:
        # Converter para string se não for
        value_str = str(value).strip()
        if not value_str:
            return 0.0
        
        # Contar quantidade de pontos e vírgulas
        dot_count = value_str.count('.')
        comma_count = value_str.count(',')
        
        # Se tem vírgula e ponto, assumir formato brasileiro (1.250,50)
        if dot_count > 0 and comma_count > 0:
            # Remover pontos (separadores de milhar) e trocar vírgula por ponto
            value_str = value_str.replace('.', '').replace(',', '.')
        # Se tem apenas vírgula, pode ser decimal brasileiro (1250,50)
        elif comma_count > 0:
            value_str = value_str.replace(',', '.')
        # Se tem múltiplos pontos, são separadores de milhar
        elif dot_count > 1:
            value_str = value_str.replace('.', '')
        
        return float(value_str)
    except (ValueError, TypeError, AttributeError):
        return 0.0


def format_currency(value):
    """Formata valor para moeda brasileira."""
    try:
        v = float(value)
        formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def format_date(date_str):
    """Formata data ISO para formato brasileiro."""
    if not date_str:
        return "-"
    try:
        date_part = str(date_str)[:10]
        parts = date_part.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        return date_part
    except Exception:
        return str(date_str)[:10]
