import os
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_fonts():
    for name, fname in [('DejaVu','DejaVuSans.ttf'),('DejaVu-Bold','DejaVuSans-Bold.ttf'),('DejaVu-Italic','DejaVuSans-Oblique.ttf')]:
        try:
            pdfmetrics.registerFont(TTFont(name, fname))
        except Exception as e:
            logging.warning(f"Шрифт {fname} не найден: {e}")

register_fonts()
FONT = 'DejaVu'
FONT_BOLD = 'DejaVu-Bold'
FONT_ITALIC = 'DejaVu-Italic'

# ─── ЦВЕТА ──────────────────────────────────────────────────────
GOLD      = colors.HexColor('#BD8F6B')
DARK_BG   = colors.HexColor('#111111')
DARK2     = colors.HexColor('#1A1A1A')
DARK3     = colors.HexColor('#232323')
DARK4     = colors.HexColor('#2C2C2C')
GRAY      = colors.HexColor('#6E6E6E')
LIGHT_GRAY = colors.HexColor('#C8C8C8')
GOLD_LIGHT = colors.HexColor('#CFA07A')

W, H = A4
MARGIN = 14*mm
CW = W - 2*MARGIN

STAFF_PRICES = {"Менеджер": 12000, "Официант": 10000, "Повар": 10000, "Грузчик": 10000}
PARTNERS = "Партнёры Forbes  •  The Art Newspaper Russia  •  С 2016 года  •  2000+ позиций в меню"
SLOGAN   = "Больше, чем просто еда — мы создаём состояние праздника"

def prepare_logo():
    """Загружает готовый логотип"""
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        logging.warning("logo.png не найден!")
        return None
    logging.info("Логотип найден!")
    return logo_path

def fmt(n):
    return f"{int(n):,}".replace(',', ' ') + " руб."

def ST(name):
    styles = {
        'slogan':       ParagraphStyle('slogan',      fontSize=9.5, textColor=GOLD_LIGHT, alignment=TA_CENTER, fontName=FONT_ITALIC, leading=13),
        'partners':     ParagraphStyle('partners',    fontSize=6.5, textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=9),
        'smeta_label':  ParagraphStyle('smeta_label', fontSize=6.5, textColor=GRAY,       alignment=TA_RIGHT,  fontName=FONT, leading=9),
        'smeta_val':    ParagraphStyle('smeta_val',   fontSize=11,  textColor=LIGHT_GRAY, alignment=TA_RIGHT,  fontName=FONT_BOLD, leading=14),
        'event_val':    ParagraphStyle('event_val',   fontSize=8.5, textColor=GOLD,       alignment=TA_RIGHT,  fontName=FONT_BOLD, leading=11),
        'smeta_lbl_l':  ParagraphStyle('smeta_lbl_l', fontSize=6.5, textColor=GRAY,       alignment=TA_LEFT,   fontName=FONT, leading=9),
        'event_val_l':  ParagraphStyle('event_val_l', fontSize=8.5, textColor=GOLD,       alignment=TA_LEFT,   fontName=FONT_BOLD, leading=11),
        'brand_name':   ParagraphStyle('brand_name',  fontSize=18,  textColor=LIGHT_GRAY, alignment=TA_CENTER, fontName=FONT_BOLD, leading=22),
        'brand_sub':    ParagraphStyle('brand_sub',   fontSize=7,   textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=9, tracking=4),
        'client_lbl':   ParagraphStyle('client_lbl',  fontSize=6.5, textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=9),
        'client_val':   ParagraphStyle('client_val',  fontSize=8,   textColor=LIGHT_GRAY, alignment=TA_CENTER, fontName=FONT_BOLD, leading=11),
        'cat':          ParagraphStyle('cat',          fontSize=7,   textColor=GOLD,       fontName=FONT_BOLD, leading=9, tracking=2),
        'cat_sub':      ParagraphStyle('cat_sub',      fontSize=6,   textColor=GRAY,       fontName=FONT, leading=8),
        'col_h':        ParagraphStyle('col_h',        fontSize=6,   textColor=GRAY,       alignment=TA_RIGHT,  fontName=FONT, leading=8),
        'col_h_l':      ParagraphStyle('col_h_l',      fontSize=6,   textColor=GRAY,       alignment=TA_LEFT,   fontName=FONT, leading=8),
        'dish':         ParagraphStyle('dish',         fontSize=7.5, textColor=LIGHT_GRAY, fontName=FONT, leading=10),
        'desc':         ParagraphStyle('desc',         fontSize=6.5, textColor=GRAY,       fontName=FONT_ITALIC, leading=9),
        'qty':          ParagraphStyle('qty',          fontSize=7.5, textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=10),
        'price':        ParagraphStyle('price',        fontSize=7.5, textColor=GRAY,       alignment=TA_RIGHT,  fontName=FONT, leading=10),
        'amount':       ParagraphStyle('amount',       fontSize=7.5, textColor=LIGHT_GRAY, alignment=TA_RIGHT,  fontName=FONT_BOLD, leading=10),
        'total_l':      ParagraphStyle('total_l',      fontSize=8,   textColor=GRAY,       fontName=FONT, leading=11),
        'total_v':      ParagraphStyle('total_v',      fontSize=8,   textColor=LIGHT_GRAY, alignment=TA_RIGHT,  fontName=FONT, leading=11),
        'grand_l':      ParagraphStyle('grand_l',      fontSize=14,  textColor=GOLD,       fontName=FONT_BOLD, leading=17),
        'grand_v':      ParagraphStyle('grand_v',      fontSize=14,  textColor=GOLD,       alignment=TA_RIGHT,  fontName=FONT_BOLD, leading=17),
        'per':          ParagraphStyle('per',           fontSize=7.5, textColor=GRAY,       alignment=TA_RIGHT,  fontName=FONT, leading=10),
        'note_lbl':     ParagraphStyle('note_lbl',     fontSize=6.5, textColor=GRAY,       fontName=FONT, leading=9),
        'note_val':     ParagraphStyle('note_val',     fontSize=7,   textColor=LIGHT_GRAY, fontName=FONT, leading=10),
        'footer':       ParagraphStyle('footer',       fontSize=6.5, textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=9),
        'why_title':    ParagraphStyle('why_title',    fontSize=7,   textColor=GOLD,       alignment=TA_CENTER, fontName=FONT_BOLD, leading=9),
        'why_text':     ParagraphStyle('why_text',     fontSize=6,   textColor=GRAY,       alignment=TA_CENTER, fontName=FONT, leading=8),
        'budget_ok':    ParagraphStyle('budget_ok',    fontSize=8,   textColor=colors.HexColor('#4CAF50'), alignment=TA_CENTER, fontName=FONT_BOLD, leading=10),
        'budget_warn':  ParagraphStyle('budget_warn',  fontSize=8,   textColor=colors.HexColor('#FF9800'), alignment=TA_CENTER, fontName=FONT_BOLD, leading=10),
    }
    return styles[name]

def menu_row(dish, qty, price, amount, desc, bg):
    inner = Table([
        [Paragraph(f"  {dish}", ST('dish'))],
        [Paragraph(f"  {desc}", ST('desc'))],
    ], colWidths=[CW*0.5])
    inner.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    row = Table([[inner, Paragraph(qty, ST('qty')), Paragraph(price, ST('price')), Paragraph(amount, ST('amount'))]],
                colWidths=[CW*0.5, CW*0.16, CW*0.16, CW*0.18])
    row.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (0,-1), 0), ('RIGHTPADDING', (-1,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, DARK3),
    ]))
    return row

def cat_header(name, subtitle=""):
    inner = [[Paragraph(f"  {name}", ST('cat'))]]
    if subtitle:
        inner.append([Paragraph(f"  {subtitle}", ST('cat_sub'))])
    r = Table(inner, colWidths=[CW])
    r.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, GOLD),
        ('LINELEFT', (0,0), (0,-1), 2, GOLD),
    ]))
    return r

def generate_pdf(event: dict, selected: list, staff: dict, food_total: float, staff_total: float, grand_total: float) -> str:
    import logging
    logging.info("generate_pdf: старт")

    out_path = f"/tmp/smeta_{event['client'].replace(' ', '_')}.pdf"

    doc = SimpleDocTemplate(out_path, pagesize=A4,
        rightMargin=MARGIN, leftMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
    story = []

    logging.info("generate_pdf: подготовка логотипа")
    logo_path = prepare_logo()
    logging.info(f"generate_pdf: логотип = {logo_path}")

    logging.info("generate_pdf: строим шапку")
    # ── ШАПКА ──
    if logo_path:
        logo = RLImage(logo_path, width=22*mm, height=22*mm)
        center_content = [
            [logo],
            [Paragraph("smile", ST('brand_name'))],
            [Paragraph("EVENT  CATERING", ST('brand_sub'))],
            [Spacer(1, 5)],
            [Paragraph("КЛИЕНТ", ST('client_lbl'))],
            [Paragraph(event['client'], ST('client_val'))],
        ]
    else:
        center_content = [
            [Paragraph("smile", ST('brand_name'))],
            [Paragraph("EVENT  CATERING", ST('brand_sub'))],
            [Spacer(1, 5)],
            [Paragraph("КЛИЕНТ", ST('client_lbl'))],
            [Paragraph(event['client'], ST('client_val'))],
        ]

    center = Table(center_content, colWidths=[CW*0.36])
    center.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))

    left = Table([
        [Paragraph("СМЕТА", ST('smeta_label'))],
        [Paragraph(f"№ {event['number']}", ST('smeta_val'))],
        [Spacer(1, 5)],
        [Paragraph("ФОРМАТ", ST('smeta_label'))],
        [Paragraph(event['format'], ST('event_val'))],
        [Spacer(1, 5)],
        [Paragraph("ГОСТЕЙ", ST('smeta_label'))],
        [Paragraph(str(event['guests']), ST('event_val'))],
    ], colWidths=[CW*0.28])
    left.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))

    right = Table([
        [Paragraph("ДАТА", ST('smeta_lbl_l'))],
        [Paragraph(event['date'], ST('event_val_l'))],
        [Spacer(1, 5)],
        [Paragraph("МЕСТО", ST('smeta_lbl_l'))],
        [Paragraph(event.get('place', '—'), ST('event_val_l'))],
        [Spacer(1, 5)],
        [Paragraph("ВРЕМЯ", ST('smeta_lbl_l'))],
        [Paragraph(event.get('time', '—'), ST('event_val_l'))],
    ], colWidths=[CW*0.28])
    right.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))

    header = Table([[left, center, right]], colWidths=[CW*0.3, CW*0.38, CW*0.32])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 14), ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (0,-1), 16), ('RIGHTPADDING', (-1,0), (-1,-1), 16),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'), ('ALIGN', (1,0), (1,-1), 'CENTER'), ('ALIGN', (2,0), (2,-1), 'LEFT'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, GOLD),
        ('LINEBEFORE', (1,0), (1,-1), 0.5, DARK4), ('LINEAFTER', (1,0), (1,-1), 0.5, DARK4),
    ]))
    story.append(header)

    # ── СЛОГАН ──
    slogan_t = Table([
        [Paragraph(f'"{SLOGAN}"', ST('slogan'))],
        [Paragraph(PARTNERS, ST('partners'))],
    ], colWidths=[CW])
    slogan_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK3),
        ('TOPPADDING', (0,0), (0,0), 9), ('BOTTOMPADDING', (0,0), (0,0), 4),
        ('TOPPADDING', (0,1), (0,1), 0), ('BOTTOMPADDING', (0,1), (0,1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 16), ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(slogan_t)
    story.append(Spacer(1, 3*mm))

    # ── МАРКЕТИНГ ──
    why = [("С 2016 ГОДА","8 лет на рынке<br/>кейтеринга"),("2000+ ПОЗИЦИЙ","Авторские блюда<br/>мировой кухни"),
           ("1000+ м²","Собственное<br/>производство"),("24 ЧАСА","На организацию<br/>мероприятия"),("FORBES","Официальный<br/>партнёр")]
    why_t = Table([[Paragraph(t, ST('why_title')) for t,_ in why],[Paragraph(d, ST('why_text')) for _,d in why]], colWidths=[CW/5]*5)
    why_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,0), 8), ('BOTTOMPADDING', (0,0), (-1,0), 3),
        ('TOPPADDING', (0,1), (-1,1), 0), ('BOTTOMPADDING', (0,1), (-1,1), 8),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, DARK4), ('LINEBETWEEN', (0,0), (-1,-1), 0.3, DARK4),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(why_t)
    story.append(Spacer(1, 4*mm))

    # ── БЮДЖЕТ И ВЫХОД ──
    budget = event.get('budget', 0)
    target_weight = event.get('target_weight', 0)
    guests = event['guests']
    actual_weight = sum(item.get('weight_per_person', 0) for item in selected)
    budget_ok = grand_total <= budget
    weight_ok = actual_weight >= target_weight * 0.9

    budget_info = Table([[
        Table([
            [Paragraph("БЮДЖЕТ", ST('note_lbl'))],
            [Paragraph(f"{fmt(budget)}", ST('note_val'))],
            [Paragraph(f"{'✅ Вписываемся' if budget_ok else '⚠️ Превышение: ' + fmt(grand_total-budget)}", ST('budget_ok') if budget_ok else ST('budget_warn'))],
        ], colWidths=[CW*0.23]),
        Table([
            [Paragraph("ВЫХОД НА ГОСТЯ", ST('note_lbl'))],
            [Paragraph(f"Цель: {target_weight} гр", ST('note_val'))],
            [Paragraph(f"Факт: {actual_weight:.0f} гр  {'✅' if weight_ok else '⚠️'}", ST('budget_ok') if weight_ok else ST('budget_warn'))],
        ], colWidths=[CW*0.23]),
        Table([
            [Paragraph("СТОИМОСТЬ МЕНЮ", ST('note_lbl'))],
            [Paragraph(fmt(food_total), ST('note_val'))],
            [Paragraph(f"На 1 гостя: {fmt(food_total//guests)}", ST('note_lbl'))],
        ], colWidths=[CW*0.23]),
        Table([
            [Paragraph("ИТОГО", ST('note_lbl'))],
            [Paragraph(fmt(grand_total), ST('note_val'))],
            [Paragraph(f"На 1 гостя: {fmt(grand_total//guests)}", ST('note_lbl'))],
        ], colWidths=[CW*0.23]),
    ]], colWidths=[CW*0.25]*4)
    budget_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10), ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('LINEBETWEEN', (0,0), (-1,-1), 0.3, DARK4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, DARK4),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(budget_info)
    story.append(Spacer(1, 3*mm))

    # ── КОЛОНКИ ──
    col_h = Table([[
        Paragraph("НАИМЕНОВАНИЕ И ОПИСАНИЕ", ST('col_h_l')),
        Paragraph("КОЛ-ВО", ST('col_h')),
        Paragraph("ЦЕНА", ST('col_h')),
        Paragraph("СУММА", ST('col_h')),
    ]], colWidths=[CW*0.5, CW*0.16, CW*0.16, CW*0.18])
    col_h.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK4),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (0,-1), 10), ('RIGHTPADDING', (-1,0), (-1,-1), 10),
    ]))
    story.append(col_h)

    # ── МЕНЮ ──
    cats = {}
    for item in selected:
        cat = item['category']
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(item)

    for cat, items in cats.items():
        story.append(cat_header(cat))
        for i, item in enumerate(items):
            bg = DARK_BG if i%2==0 else colors.HexColor('#161616')
            story.append(menu_row(
                item['name'],
                item['qty_label'],
                item['price_label'],
                item['total_label'],
                item.get('desc', ''),
                bg
            ))
        story.append(Spacer(1, 2*mm))

    # ── ПЕРСОНАЛ ──
    story.append(Spacer(1, 2*mm))
    story.append(cat_header("ПЕРСОНАЛ И СЕРВИС"))
    for i, (role, qty) in enumerate(staff.items()):
        price = STAFF_PRICES.get(role, 10000)
        total = qty * price
        bg = DARK_BG if i%2==0 else colors.HexColor('#161616')
        desc_map = {
            "Менеджер": "Координация мероприятия, контроль качества, коммуникация с клиентом",
            "Официант": "Обслуживание гостей, поддержание сервировки, уборка посуды",
            "Повар": "Финальное приготовление и разогрев блюд на площадке",
            "Грузчик": "Доставка и вывоз оборудования, посуды и инвентаря",
        }
        story.append(menu_row(
            role,
            f"{qty} чел.",
            f"{price:,} руб.".replace(',', ' '),
            f"{total:,} руб.".replace(',', ' '),
            desc_map.get(role, ""),
            bg
        ))

    story.append(Spacer(1, 5*mm))

    # ── ПРИМЕЧАНИЯ ──
    notes = Table([[
        Table([
            [Paragraph("ВКЛЮЧЕНО В СТОИМОСТЬ:", ST('note_lbl'))],
            [Paragraph("• Профессиональная сервировка и декор стола", ST('note_val'))],
            [Paragraph("• Фарфоровая посуда и столовые приборы", ST('note_val'))],
            [Paragraph("• Доставка продуктов и оборудования", ST('note_val'))],
            [Paragraph("• Уборка после мероприятия", ST('note_val'))],
        ], colWidths=[CW*0.44]),
        Table([
            [Paragraph("УСЛОВИЯ ОПЛАТЫ:", ST('note_lbl'))],
            [Paragraph("• Предоплата 50% при подписании договора", ST('note_val'))],
            [Paragraph("• Остаток 50% за 3 дня до мероприятия", ST('note_val'))],
            [Paragraph("• Счёт действителен 5 рабочих дней", ST('note_val'))],
            [Paragraph(f"• Менеджер: {event.get('manager','Елена')}  +7 (926) 141-25-18", ST('note_val'))],
        ], colWidths=[CW*0.44]),
    ]], colWidths=[CW*0.5, CW*0.5])
    notes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12), ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('LINEAFTER', (0,0), (0,-1), 0.3, DARK4),
    ]))
    story.append(notes)
    story.append(Spacer(1, 4*mm))

    # ── ИТОГО ──
    lt = Table([
        [Paragraph("Стоимость меню:", ST('total_l')), Paragraph(fmt(food_total), ST('total_v'))],
        [Paragraph("Персонал:", ST('total_l')), Paragraph(fmt(staff_total), ST('total_v'))],
        [Paragraph("ИТОГО:", ST('grand_l')), Paragraph(fmt(grand_total), ST('grand_v'))],
        [Paragraph("Стоимость на 1 персону:", ST('total_l')), Paragraph(fmt(grand_total // guests), ST('per'))],
    ], colWidths=[CW*0.55, CW*0.45])
    lt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (0,-1), 14), ('RIGHTPADDING', (-1,0), (-1,-1), 14),
        ('LINEABOVE', (0,2), (-1,2), 1.5, GOLD), ('LINEBELOW', (0,2), (-1,2), 0.5, DARK4),
        ('LINEBELOW', (0,0), (-1,0), 0.3, DARK4),
    ]))
    story.append(lt)
    story.append(Spacer(1, 4*mm))

    # ── ПОДВАЛ ──
    footer = Table([[
        Paragraph("SmiLe Event Catering  |  info@slcatering.ru  |  +7 (925) 605-38-50  |  +7 (926) 052-80-84  |  slcatering.ru  |  #smileeventcatering", ST('footer')),
    ]], colWidths=[CW])
    footer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('TOPPADDING', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LINEABOVE', (0,0), (-1,0), 1.5, GOLD),
    ]))
    story.append(footer)

    logging.info("generate_pdf: запускаем doc.build")
    def dark_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
    logging.info(f"generate_pdf: PDF готов! {out_path}")
    return out_path
