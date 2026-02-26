# -*- coding: utf-8 -*-
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportMissingImports=false, reportUnusedImport=false, reportUnusedVariable=false
"""
CalhaGest - Gerador de PDF Profissional
Gera documentos PDF com layout inspirado no fazerorcamento.com.
Layout: Header azul com logo -> Titulo -> Descricao -> Precos -> Pagamento -> Contrato -> Assinaturas -> Rodape.
"""

# Garantir que unittest.mock esteja disponível antes de importar fpdf
# (fpdf.sign importa 'from unittest.mock import patch')
import unittest.mock  # noqa: F401

from fpdf import FPDF  # type: ignore[import-untyped]
from datetime import datetime
import os
from utils import format_measure, format_dimensions
from typing import Any, Optional


# Meses em portugues
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Cores do tema (azul)
BLUE_PRIMARY = (37, 99, 235)
BLUE_DARK = (30, 64, 175)
BLUE_LIGHT = (219, 234, 254)
GREEN_BADGE = (34, 197, 94)
TEXT_DARK = (30, 41, 59)
TEXT_SECONDARY = (100, 116, 139)
TEXT_LIGHT = (148, 163, 184)
BORDER_COLOR = (226, 232, 240)
WHITE = (255, 255, 255)
BG_LIGHT = (248, 250, 252)


def _fmt_currency(value: Any) -> str:
    """Formata valor em R$ brasileiro."""
    try:
        val = float(value or 0)
        formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def _fmt_date_extenso(date_str: Optional[str] = None) -> str:
    """Formata data por extenso: 'Criado em 27 de Janeiro de 2026'."""
    try:
        if date_str:
            dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        else:
            dt = datetime.now()
        mes = MESES_PT.get(dt.month, str(dt.month))
        return f"Criado em {dt.day} de {mes} de {dt.year}"
    except Exception:
        dt = datetime.now()
        mes = MESES_PT.get(dt.month, str(dt.month))
        return f"Criado em {dt.day} de {mes} de {dt.year}"


class QuotePDF(FPDF):
    """PDF profissional estilo fazerorcamento.com."""

    def __init__(self, company_name: str = "CalhaGest", company_info: Optional[dict[str, Any]] = None):
        super().__init__()
        self.company_name = company_name
        self.company_info: dict[str, Any] = company_info or {}
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        pass

    def footer(self):
        pass


def generate_quote_pdf(quote: dict[str, Any], company_settings: Optional[dict[str, Any]] = None, output_path: Optional[str] = None) -> str:
    """
    Gera um PDF profissional do orcamento no estilo fazerorcamento.com.
    """
    settings = company_settings or {}
    company_name = settings.get('company_name', 'CalhaGest')

    pdf = QuotePDF(company_name, settings)
    pdf.add_page()

    page_width = pdf.w
    margin = 15
    content_width = page_width - 2 * margin

    # ==============================
    # 1. FAIXA AZUL NO TOPO
    # ==============================
    pdf.set_fill_color(*BLUE_PRIMARY)
    pdf.rect(0, 0, page_width, 28, 'F')

    # ==============================
    # 2. LOGO DA EMPRESA (quadrado)
    # ==============================
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon", "Quality.jpeg")

    if os.path.exists(logo_path):
        try:
            logo_size = 25
            logo_x = (page_width - logo_size) / 2
            logo_y_top = 14

            # Redimensionar logo para economizar tamanho do PDF
            from PIL import Image
            import tempfile
            img = Image.open(logo_path)
            img = img.resize((256, 256), Image.LANCZOS)
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            temp_logo = os.path.join(tempfile.gettempdir(), 'calhagest_logo_small.jpg')
            img.save(temp_logo, 'JPEG', quality=90)

            pdf.image(temp_logo, logo_x, logo_y_top, logo_size, logo_size)
        except Exception:
            pass

    # ==============================
    # 3. INFORMACOES DA EMPRESA
    # ==============================
    y_pos = 48

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(margin, y_pos)
    pdf.cell(content_width, 7, company_name, align='C', new_x='LMARGIN', new_y='NEXT')
    y_pos += 7

    cnpj = settings.get('company_cnpj', '')
    if cnpj:
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 5, cnpj, align='C', new_x='LMARGIN', new_y='NEXT')
        y_pos += 5

    address = settings.get('company_address', '')
    if address:
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 5, address, align='C', new_x='LMARGIN', new_y='NEXT')
        y_pos += 5

    phone = settings.get('company_phone', '')
    if phone:
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 5, phone, align='C', new_x='LMARGIN', new_y='NEXT')
        y_pos += 5

    y_pos += 3

    # ==============================
    # 4. TITULO DO ORCAMENTO
    # ==============================
    qt = quote.get('quote_type', 'instalado') or 'instalado'
    items = quote.get('items', [])
    if items:
        product_types: list[str] = []
        seen: set[str] = set()
        for item in items:
            name = item.get('product_name', '').lower()
            if 'calha' in name and 'calhas' not in seen:
                product_types.append('calhas')
                seen.add('calhas')
            elif 'rufo' in name and 'rufos' not in seen:
                product_types.append('rufos')
                seen.add('rufos')
            elif 'pingadeira' in name and 'pingadeiras' not in seen:
                product_types.append('pingadeiras')
                seen.add('pingadeiras')
            elif name not in seen:
                product_types.append(item.get('product_name', ''))
                seen.add(name)

        if product_types:
            if qt == 'instalado':
                service_title = f"Instalacao"
            else:
                service_title = f"Orcamento"
        else:
            service_title = "Instalacao" if qt == 'instalado' else "Orcamento"
    else:
        service_title = "Instalacao" if qt == 'instalado' else "Orcamento de Servicos"

    # Se tem notas tecnicas curtas, usar como titulo
    notes = quote.get('technical_notes', '')
    if notes and len(notes) <= 60:
        service_title = notes

    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(margin, y_pos)
    pdf.cell(content_width, 7, service_title, align='C', new_x='LMARGIN', new_y='NEXT')
    y_pos += 6

    quote_id = quote.get('id', 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*TEXT_SECONDARY)
    pdf.set_xy(margin, y_pos)
    pdf.cell(content_width, 5, f"[OR.{quote_id:04d}]", align='C', new_x='LMARGIN', new_y='NEXT')
    y_pos += 5

    # ==============================
    # 5. DESCRICAO DAS ATIVIDADES
    # ==============================
    if notes and len(notes) > 60:
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.line(margin, y_pos, page_width - margin, y_pos)
        y_pos += 5

        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 8, "Descricao das atividades", new_x='LMARGIN', new_y='NEXT')
        y_pos += 9

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*TEXT_SECONDARY)
        pdf.set_xy(margin, y_pos)
        pdf.multi_cell(content_width, 5, notes)
        y_pos = pdf.get_y() + 4

    # ==============================
    # 6. TABELA DE PRECOS
    # ==============================
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.line(margin, y_pos, page_width - margin, y_pos)
    y_pos += 4

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(margin, y_pos)
    pdf.cell(content_width, 7, "Precos", new_x='LMARGIN', new_y='NEXT')
    y_pos += 7

    if items:
        col_product = content_width * 0.35
        col_qty = content_width * 0.15
        col_unit_price = content_width * 0.22
        col_subtotal = content_width * 0.28

        # Cabecalho das colunas
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin + col_product, y_pos)
        pdf.cell(col_qty, 5, "Qtde.", align='C')
        pdf.set_xy(margin + col_product + col_qty, y_pos)
        pdf.cell(col_unit_price, 5, "Valor unitario", align='C')
        y_pos += 7

        def _check_page_break(current_y, needed_height=12):
            """Verifica se precisa de nova pagina e adiciona se necessario."""
            page_bottom_limit = 297 - 25  # A4 height minus margin
            if current_y + needed_height > page_bottom_limit:
                pdf.add_page()
                current_y = 20
                # Repetir cabeçalho da tabela na nova página
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(*TEXT_DARK)
                pdf.set_xy(margin, current_y)
                pdf.cell(content_width, 7, "Precos (continuacao)", new_x='LMARGIN', new_y='NEXT')
                current_y += 9
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(*TEXT_DARK)
                pdf.set_xy(margin + col_product, current_y)
                pdf.cell(col_qty, 5, "Qtde.", align='C')
                pdf.set_xy(margin + col_product + col_qty, current_y)
                pdf.cell(col_unit_price, 5, "Valor unitario", align='C')
                current_y += 7
            return current_y

        for item in items:
            # Verificar se precisa de nova pagina antes de cada item
            y_pos = _check_page_break(y_pos, 12)

            product_name = item.get('product_name', '-')
            meters = item.get('meters', 0)
            price_per_meter = item.get('price_per_meter', 0)
            item_total = item.get('total', 0)
            measure = item.get('measure', 0)
            item_discount = item.get('discount', 0)
            item_width = item.get('width', 0)
            item_length = item.get('length', 0)
            item_pricing_unit = item.get('pricing_unit', 'metro') or 'metro'
            unit_suffix = 'Un' if item_pricing_unit == 'unidade' else 'm'

            row_y = y_pos

            # Nome do produto
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(*TEXT_DARK)
            pdf.set_xy(margin, row_y)
            product_display = f"{product_name}"
            if item_width or item_length:
                product_display += f" ({format_dimensions(item_width, item_length)})"
            elif measure:
                product_display += f" ({format_measure(measure)})"
            if item_discount > 0:
                product_display += f" [-{_fmt_currency(item_discount)}]"
            pdf.cell(col_product, 7, product_display)

            # Quantidade
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*TEXT_DARK)
            pdf.set_xy(margin + col_product, row_y)
            pdf.cell(col_qty, 7, f"{meters:.2f}{unit_suffix}", align='C')

            # Valor unitario
            pdf.set_xy(margin + col_product + col_qty, row_y)
            pdf.cell(col_unit_price, 7, _fmt_currency(price_per_meter), align='C')

            # Subtotal (badge verde)
            badge_x = margin + col_product + col_qty + col_unit_price + 2
            badge_w = col_subtotal - 7
            badge_h = 7

            pdf.set_fill_color(*GREEN_BADGE)
            pdf.rect(badge_x, row_y, badge_w, badge_h, 'F')

            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*WHITE)
            pdf.set_xy(badge_x, row_y)
            pdf.cell(badge_w, badge_h, _fmt_currency(item_total), align='C')

            y_pos += 10

        # Linha pontilhada
        y_pos += 2
        # Verificar quebra de pagina antes dos totais
        y_pos = _check_page_break(y_pos, 30)
        pdf.set_draw_color(*BORDER_COLOR)
        dash_x = margin
        while dash_x < page_width - margin:
            end_x = min(dash_x + 3, page_width - margin)
            pdf.line(dash_x, y_pos, end_x, y_pos)
            dash_x += 6
        y_pos += 5

        # Calcular subtotal (soma dos itens) e desconto total
        subtotal = sum(item.get('total', 0) for item in items)
        discount_total_value = quote.get('discount_total', 0)
        discount_type = quote.get('discount_type', 'percentage')
        
        if discount_type == 'value':
            discount_total_amount = discount_total_value if discount_total_value > 0 else 0
            discount_label = "Desconto Total (R$)"
        else:  # percentage
            discount_total_amount = subtotal * (discount_total_value / 100) if discount_total_value > 0 else 0
            discount_label = f"Desconto Total ({discount_total_value:.1f}%)"
        
        final_total = quote.get('total', 0)

        # Mostrar Subtotal se houver desconto total
        if discount_total_value > 0:
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(*TEXT_DARK)
            pdf.set_xy(margin, y_pos)
            pdf.cell(content_width * 0.5, 7, "Subtotal")
            pdf.set_xy(margin + content_width * 0.5, y_pos)
            pdf.cell(content_width * 0.5, 7, _fmt_currency(subtotal), align='R')
            y_pos += 8

            # Mostrar Desconto Total
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(*TEXT_SECONDARY)
            pdf.set_xy(margin, y_pos)
            pdf.cell(content_width * 0.5, 7, discount_label)
            pdf.set_xy(margin + content_width * 0.5, y_pos)
            pdf.cell(content_width * 0.5, 7, f"- {_fmt_currency(discount_total_amount)}", align='R')
            y_pos += 8

        # TOTAL
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width * 0.5, 8, "Total")

        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin + content_width * 0.5, y_pos)
        pdf.cell(content_width * 0.5, 8, _fmt_currency(final_total), align='R')
        y_pos += 10

    # ==============================
    # 6.5 SALDO DEVEDOR / PAGO
    # ==============================
    from database import db as _db
    pay_summary = _db.get_payment_summary(quote.get('id', 0))

    def _ensure_space(current_y, needed=20):
        """Garante espaco na pagina, adiciona nova pagina se necessario."""
        if current_y + needed > 297 - 25:
            pdf.add_page()
            return 20
        return current_y

    if pay_summary and pay_summary['total_paid'] > 0:
        y_pos = _ensure_space(y_pos, 30)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.line(margin, y_pos, page_width - margin, y_pos)
        y_pos += 5

        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 7, "Situacao Financeira")
        y_pos += 8

        # Valor Pago
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(34, 197, 94)  # green
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width * 0.5, 7, "Valor Pago")
        pdf.set_xy(margin + content_width * 0.5, y_pos)
        pdf.cell(content_width * 0.5, 7, _fmt_currency(pay_summary['total_paid']), align='R')
        y_pos += 7

        # Saldo Devedor
        if pay_summary['balance'] > 0:
            pdf.set_text_color(239, 68, 68)  # red
            pdf.set_xy(margin, y_pos)
            pdf.cell(content_width * 0.5, 7, "Saldo Devedor")
            pdf.set_xy(margin + content_width * 0.5, y_pos)
            pdf.cell(content_width * 0.5, 7, _fmt_currency(pay_summary['balance']), align='R')
        else:
            pdf.set_text_color(34, 197, 94)  # green
            pdf.set_xy(margin, y_pos)
            pdf.cell(content_width * 0.5, 7, "Status: QUITADO")
        y_pos += 8

    # ==============================
    # 7. METODOS DE PAGAMENTO
    # ==============================
    page_bottom = 297 - 25  # A4 height minus auto-break margin  # noqa

    payment_methods_str = quote.get('payment_methods', '')
    if payment_methods_str:
        methods = [m.strip() for m in payment_methods_str.split(',') if m.strip()]

        y_pos = _ensure_space(y_pos, 25)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.line(margin, y_pos, page_width - margin, y_pos)
        y_pos += 5

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 7, "Metodos de pagamento", new_x='LMARGIN', new_y='NEXT')
        y_pos += 9

        # Bootstrap Icons SVG mapping
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon", "payment")
        method_svg_icons = {
            'pix': 'x-diamond-fill.svg',
            'debito': 'credit-card.svg',
            'credito': 'credit-card.svg',
            'dinheiro': 'cash-stack.svg',
            'transferencia': 'arrow-left-right.svg',
            'boleto': 'file-earmark-break.svg',
        }

        method_labels = {
            'pix': 'pix',
            'debito': 'debito',
            'credito': 'credito',
            'dinheiro': 'dinheiro',
            'transferencia': 'transferencia',
            'boleto': 'boleto',
        }

        icon_size = 4  # mm for SVG icon
        cols = 4  # 4 badges per row
        col_width = content_width / cols
        badge_h = 7

        for idx, method in enumerate(methods):
            label = method_labels.get(method, method)
            svg_file = method_svg_icons.get(method, '')
            svg_path = os.path.join(icons_dir, svg_file) if svg_file else ''
            has_icon = svg_path and os.path.exists(svg_path)

            col = idx % cols
            if col == 0 and idx > 0:
                y_pos += badge_h + 2

            badge_x = margin + col * col_width

            pdf.set_font('Helvetica', '', 8)
            label_w = pdf.get_string_width(f" {label}") + 3
            badge_total_w = (icon_size + 5) + label_w + 4 if has_icon else label_w + 8

            # Borda externa do badge
            pdf.set_draw_color(*BORDER_COLOR)
            pdf.set_fill_color(*WHITE)
            pdf.rect(badge_x, y_pos, badge_total_w, badge_h, 'FD')

            if has_icon:
                # Icon box background
                icon_box_x = badge_x + 1.5
                icon_box_w = icon_size + 3
                pdf.set_fill_color(*BG_LIGHT)
                pdf.set_draw_color(*BORDER_COLOR)
                pdf.rect(icon_box_x, y_pos + 1, icon_box_w, badge_h - 2, 'FD')

                # Render SVG icon
                icon_x = icon_box_x + (icon_box_w - icon_size) / 2
                icon_y = y_pos + (badge_h - icon_size) / 2
                try:
                    pdf.image(svg_path, x=icon_x, y=icon_y, w=icon_size, h=icon_size)
                except Exception:
                    pass

                # Label after icon
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(*TEXT_DARK)
                pdf.set_xy(icon_box_x + icon_box_w + 1, y_pos)
                pdf.cell(label_w, badge_h, label or '')
            else:
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(*TEXT_DARK)
                pdf.set_xy(badge_x + 3, y_pos)
                pdf.cell(badge_total_w - 6, badge_h, label or '')

        y_pos += badge_h + 5

    # ==============================
    # 8. CONDICOES DE CONTRATO
    # ==============================
    contract = quote.get('contract_terms', '')
    if contract:
        # Estimar espaco: titulo(18) + texto + assinaturas(45)
        contract_lines = max(1, len(contract) // 80 + 1)
        contract_text_h = contract_lines * 5 + 5
        _ = 18 + contract_text_h + 45  # total_needed estimate

        y_pos = _ensure_space(y_pos, 30)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.line(margin, y_pos, page_width - margin, y_pos)
        y_pos += 5

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.cell(content_width, 7, "Condicoes de contrato", new_x='LMARGIN', new_y='NEXT')
        y_pos += 8

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_xy(margin, y_pos)
        pdf.multi_cell(content_width, 5, contract)
        y_pos = pdf.get_y() + 3
        # Atualizar y_pos apos multi_cell (pode ter quebrado pagina internamente)
        y_pos = _ensure_space(y_pos, 10)

    # ==============================
    # 9. ASSINATURAS + DATA + LINK (bloco unico)
    # ==============================
    # Calcular espaco total necessario para o bloco final
    block_height = 40  # espaco para assinaturas + data + link
    page_bottom = 297 - 10  # limite inferior da pagina A4
    
    # Se nao cabe na pagina atual, adicionar nova pagina
    if y_pos + block_height > page_bottom:
        pdf.add_page()
        y_pos = 30

    # Desabilitar auto page break temporariamente para nao quebrar o bloco
    pdf.set_auto_page_break(auto=False)

    # Posicionar assinaturas com espaco reduzido
    sig_y = y_pos + 10
    half_width = (content_width - 30) / 2

    # Linha assinatura empresa
    line_y = sig_y
    pdf.set_draw_color(*BLUE_PRIMARY)
    pdf.set_line_width(0.5)
    pdf.line(margin, line_y, margin + half_width, line_y)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(margin, line_y + 2)
    pdf.cell(half_width, 6, company_name, align='C')

    # Linha assinatura cliente
    client_line_x = margin + half_width + 30
    pdf.line(client_line_x, line_y, client_line_x + half_width, line_y)

    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(client_line_x, line_y + 2)
    pdf.cell(half_width, 6, "Cliente", align='C')

    pdf.set_line_width(0.2)

    # ==============================
    # 10. DATA POR EXTENSO
    # ==============================
    date_y = line_y + 12
    created_at = quote.get('created_at', '')
    date_text = _fmt_date_extenso(created_at[:10] if created_at else None)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(margin, date_y)
    pdf.cell(content_width, 6, date_text, align='C')

    # ==============================
    # 11. LINK ASSINAR DOCUMENTO
    # ==============================
    sign_y = date_y + 6
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*BLUE_PRIMARY)
    sign_text = 'Assinar documento'
    sign_url = 'https://assinador.iti.br/assinatura/index.xhtml'
    text_w = pdf.get_string_width(sign_text)
    sign_x = margin + (content_width - text_w) / 2
    pdf.set_xy(sign_x, sign_y)
    pdf.cell(text_w, 6, sign_text, link=sign_url)
    # Sublinhado decorativo
    pdf.set_draw_color(*BLUE_PRIMARY)
    pdf.set_line_width(0.3)
    pdf.line(sign_x, sign_y + 6, sign_x + text_w, sign_y + 6)
    pdf.set_line_width(0.2)

    # Restaurar auto page break
    pdf.set_auto_page_break(auto=True, margin=25)

    # ==============================
    # SALVAR PDF
    # ==============================
    if not output_path:
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

        client_name_safe = quote.get('client_name', 'Cliente').replace(' ', '_')
        date_str = datetime.now().strftime('%Y%m%d')
        output_path = os.path.join(pdf_dir, f"Orcamento_{client_name_safe}_{date_str}.pdf")

    pdf.output(output_path)
    return output_path
