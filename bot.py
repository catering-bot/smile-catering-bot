import os
import logging
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ─── ШАГИ ДИАЛОГА ───────────────────────────────────────────────
CLIENT, FORMAT, GUESTS, DATE, PLACE, TIME, BUDGET, WEIGHT, MODE = range(9)
AUTO_CONFIRM = 9
MANUAL_CAT, MANUAL_ITEMS, MANUAL_CONFIRM = 10, 11, 12

# ─── ПЕРСОНАЛ ПО КОЛИЧЕСТВУ ГОСТЕЙ ─────────────────────────────
def calc_staff(guests: int, fmt: str) -> dict:
    if guests <= 30:
        return {"Менеджер": 1, "Официант": 1, "Повар": 1, "Грузчик": 1}
    elif guests <= 60:
        return {"Менеджер": 1, "Официант": 2, "Повар": 1, "Грузчик": 1}
    elif guests <= 100:
        return {"Менеджер": 1, "Официант": 3, "Повар": 2, "Грузчик": 1}
    elif guests <= 150:
        return {"Менеджер": 1, "Официант": 6, "Повар": 2, "Грузчик": 2}
    elif guests <= 250:
        return {"Менеджер": 1, "Официант": 8, "Повар": 3, "Грузчик": 2}
    else:
        return {"Менеджер": 1, "Официант": 10, "Повар": 4, "Грузчик": 3}

STAFF_PRICES = {"Менеджер": 12000, "Официант": 10000, "Повар": 10000, "Грузчик": 10000}

def calc_staff_total(guests: int, fmt: str) -> tuple:
    staff = calc_staff(guests, fmt)
    total = sum(qty * STAFF_PRICES[role] for role, qty in staff.items())
    return staff, total

# ─── ПОРЦИИ НА ЧЕЛОВЕКА ПО ФОРМАТУ И КАТЕГОРИИ ─────────────────
PORTIONS = {
    "Фуршет":  {"канапе": 5, "тарталетки": 2, "брускетта": 2, "закуски": 1, "салаты": 1, "горячее": 1, "десерты": 2, "напитки холодные": 3, "напитки горячие": 1, "хлеб": 1},
    "Банкет":  {"закуски": 1, "салаты": 1, "горячее": 1, "десерты": 2, "напитки холодные": 3, "напитки горячие": 1, "хлеб": 1},
    "BBQ":     {"bbq": 3, "салаты": 1, "десерты": 1, "напитки холодные": 3, "напитки горячие": 1},
}

# ─── МИНИМАЛЬНЫЙ ВЫХОД НА ЧЕЛОВЕКА (гр) ────────────────────────
MIN_WEIGHT = {"Фуршет": 450, "Банкет": 650, "BBQ": 550}

# ─── ЗАГРУЗКА МЕНЮ ИЗ EXCEL ────────────────────────────────────
def load_menu() -> dict:
    """Загружает меню из Excel файла menu.xlsx"""
    try:
        df = pd.read_excel("menu.xlsx", sheet_name="цены 2025", header=None)
        mask = df.notna().any(axis=1)
        data = df[mask].copy()

        menu = {}
        current_cat = None

        for idx, row in data.iterrows():
            name = str(row[0]).strip() if pd.notna(row[0]) else ""
            weight = row[1] if pd.notna(row[1]) else 0
            price = row[4] if pd.notna(row[4]) else 0

            # Пропускаем служебные строки
            if name in ["Меню", "выход, гр", "выход б/а в мл.", "выход в гр.",
                        "Стоимость меню", "Дополнительные затраты", "Итог:",
                        "Стоимость на персону:", "SmiLe Event & Catering",
                        "info@slcatering.ru", ""]:
                continue

            # Определяем категорию (строки без цены)
            if pd.isna(row[4]) or price == 0:
                if name and not name.startswith("Персонал") and not name.startswith("Стол") and not name.startswith("Доставка"):
                    current_cat = name.lower().strip()
                    if current_cat not in menu:
                        menu[current_cat] = []
                continue

            # Добавляем блюдо в категорию
            if current_cat and name and price > 0:
                try:
                    w = float(str(weight).replace("1 шт", "50")) if weight else 0
                    p = float(price)
                    if p > 0 and w > 0:
                        menu[current_cat].append({
                            "name": name,
                            "weight": w,
                            "price": p,
                        })
                except:
                    pass

        return menu
    except Exception as e:
        logging.error(f"Ошибка загрузки меню: {e}")
        return {}

# ─── АВТО-ПОДБОР МЕНЮ ──────────────────────────────────────────
def auto_select_menu(fmt: str, guests: int, food_budget: float, target_weight: int) -> list:
    """
    Подбирает блюда под бюджет и выход в граммах.
    Возвращает список выбранных позиций.
    """
    menu = load_menu()
    portions = PORTIONS.get(fmt, PORTIONS["Фуршет"])

    selected = []
    total_cost = 0
    total_weight = 0
    budget_per_person = food_budget / guests

    # Приоритет категорий
    cat_priority = list(portions.keys())

    for cat in cat_priority:
        if cat not in menu or not menu[cat]:
            # Пробуем найти похожую категорию
            found = False
            for menu_cat in menu:
                if cat in menu_cat or menu_cat in cat:
                    cat = menu_cat
                    found = True
                    break
            if not found:
                continue

        items = menu[cat]
        portions_per_person = portions.get(cat, 1)
        total_portions = portions_per_person * guests

        # Сортируем по соотношению цена/грамм
        items_sorted = sorted(items, key=lambda x: x['price'] / max(x['weight'], 1))

        # Берём 2-3 позиции из категории
        count = 3 if cat in ["канапе", "горячее", "салаты"] else 2
        picked = 0

        for item in items_sorted:
            if picked >= count:
                break

            cost = item['price'] * total_portions
            weight_contribution = item['weight'] * portions_per_person

            # Проверяем не превышаем ли бюджет
            if total_cost + cost <= food_budget * 0.95:
                selected.append({
                    "category": cat.upper(),
                    "name": item['name'],
                    "qty": total_portions,
                    "qty_label": f"{total_portions} порц.",
                    "price": item['price'],
                    "price_label": f"{item['price']:.0f} руб.",
                    "total": cost,
                    "total_label": f"{cost:,.0f} руб.".replace(',', ' '),
                    "weight_per_person": item['weight'] * portions_per_person,
                    "desc": f"Выход {item['weight']:.0f} гр/порц.",
                })
                total_cost += cost
                total_weight += weight_contribution
                picked += 1

    return selected, total_cost, total_weight

# ─── ХЭНДЛЕРЫ ──────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в SmiLe Catering!\n\n"
        "Команды:\n"
        "/смета — создать новую смету\n"
        "/помощь — справка",
        reply_markup=ReplyKeyboardRemove()
    )

async def new_smeta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "📋 Создаём смету\n\n"
        "Шаг 1/8 — Введите название клиента:",
        reply_markup=ReplyKeyboardRemove()
    )
    return CLIENT

async def get_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['client'] = update.message.text
    keyboard = [["🍽️ Фуршет", "🥂 Банкет", "🔥 BBQ"]]
    await update.message.reply_text(
        "Шаг 2/8 — Выберите формат:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return FORMAT

async def get_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Фуршет" in text: context.user_data['format'] = "Фуршет"
    elif "Банкет" in text: context.user_data['format'] = "Банкет"
    elif "BBQ" in text: context.user_data['format'] = "BBQ"
    else:
        await update.message.reply_text("Выберите из предложенных вариантов.")
        return FORMAT
    await update.message.reply_text(
        "Шаг 3/8 — Сколько гостей?\n(введите число, например: 120)",
        reply_markup=ReplyKeyboardRemove()
    )
    return GUESTS

async def get_guests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        guests = int(update.message.text.strip())
        if guests < 1: raise ValueError
    except:
        await update.message.reply_text("Введите число гостей (например: 120)")
        return GUESTS
    context.user_data['guests'] = guests
    await update.message.reply_text("Шаг 4/8 — Дата мероприятия (например: 24 мая 2025):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Шаг 5/8 — Место проведения:")
    return PLACE

async def get_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['place'] = update.message.text
    await update.message.reply_text("Шаг 6/8 — Время мероприятия (например: 19:00 — 23:00):")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    await update.message.reply_text(
        "Шаг 7/8 — Общий бюджет в рублях?\n(например: 500000)"
    )
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        budget = float(update.message.text.strip().replace(' ', '').replace(',', ''))
        if budget < 1000: raise ValueError
    except:
        await update.message.reply_text("Введите бюджет числом (например: 500000)")
        return BUDGET
    context.user_data['budget'] = budget
    await update.message.reply_text(
        "Шаг 8/8 — Желаемый выход на 1 гостя в граммах?\n"
        "• Фуршет: обычно 400-500 гр\n"
        "• Банкет: обычно 600-700 гр\n"
        "• BBQ: обычно 500-600 гр\n\n"
        "(введите число, например: 500)"
    )
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = int(update.message.text.strip())
        if weight < 100: raise ValueError
    except:
        await update.message.reply_text("Введите выход в граммах (например: 500)")
        return WEIGHT
    context.user_data['weight'] = weight

    # Считаем персонал
    guests = context.user_data['guests']
    fmt = context.user_data['format']
    budget = context.user_data['budget']
    staff, staff_total = calc_staff_total(guests, fmt)
    food_budget = budget - staff_total

    context.user_data['staff'] = staff
    context.user_data['staff_total'] = staff_total
    context.user_data['food_budget'] = food_budget

    staff_lines = "\n".join([f"  • {r}: {q} чел. × {STAFF_PRICES[r]:,} = {q*STAFF_PRICES[r]:,} руб." for r,q in staff.items()])

    keyboard = [["🤖 Авто-подбор меню", "✋ Выбрать вручную"]]
    await update.message.reply_text(
        f"📊 Расчёт бюджета:\n\n"
        f"Общий бюджет: {budget:,.0f} руб.\n"
        f"Персонал: {staff_total:,.0f} руб.\n"
        f"{staff_lines}\n\n"
        f"💰 На еду остаётся: {food_budget:,.0f} руб.\n"
        f"👤 На 1 гостя: {food_budget/guests:,.0f} руб.\n"
        f"⚖️ Целевой выход: {weight} гр/чел\n\n"
        f"Выберите режим подбора меню:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MODE

async def get_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "Авто" in text:
        await update.message.reply_text(
            "🤖 Подбираю меню...\n"
            "Анализирую Excel файл и подбираю позиции под бюджет и выход.",
            reply_markup=ReplyKeyboardRemove()
        )
        return await auto_mode(update, context)
    else:
        return await manual_mode_start(update, context)

# ─── АВТО РЕЖИМ ────────────────────────────────────────────────
async def auto_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guests = context.user_data['guests']
    fmt = context.user_data['format']
    food_budget = context.user_data['food_budget']
    target_weight = context.user_data['weight']

    selected, total_cost, total_weight = auto_select_menu(fmt, guests, food_budget, target_weight)

    if not selected:
        await update.message.reply_text(
            "❌ Не удалось подобрать меню.\n"
            "Проверьте что файл menu.xlsx загружен на сервер."
        )
        return ConversationHandler.END

    context.user_data['selected'] = selected
    context.user_data['food_total'] = total_cost
    context.user_data['total_weight'] = total_weight

    # Группируем по категориям для показа
    cats = {}
    for item in selected:
        cat = item['category']
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(item)

    lines = ["🤖 Подобрано меню:\n"]
    for cat, items in cats.items():
        lines.append(f"\n{cat}:")
        for item in items:
            lines.append(f"  • {item['name'][:45]}")
            lines.append(f"    {item['qty_label']} × {item['price_label']} = {item['total_label']}")

    staff_total = context.user_data['staff_total']
    budget = context.user_data['budget']
    grand = total_cost + staff_total

    lines.append(f"\n{'─'*35}")
    lines.append(f"🍽️ Стоимость меню: {total_cost:,.0f} руб.".replace(',', ' '))
    lines.append(f"👥 Персонал: {staff_total:,.0f} руб.".replace(',', ' '))
    lines.append(f"💰 ИТОГО: {grand:,.0f} руб.".replace(',', ' '))
    lines.append(f"👤 На персону: {grand//guests:,.0f} руб.".replace(',', ' '))
    lines.append(f"⚖️ Выход: {total_weight:.0f} гр/чел")

    # Проверяем вписывается ли в бюджет
    if grand <= budget:
        lines.append(f"✅ Вписывается в бюджет!")
    else:
        lines.append(f"⚠️ Превышение: {grand-budget:,.0f} руб.".replace(',', ' '))

    keyboard = [["✅ Генерировать PDF", "🔄 Попробовать заново", "✋ Выбрать вручную"]]
    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return AUTO_CONFIRM

async def auto_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "PDF" in text:
        return await generate_and_send_pdf(update, context)
    elif "заново" in text:
        return await auto_mode(update, context)
    else:
        return await manual_mode_start(update, context)

# ─── РУЧНОЙ РЕЖИМ ──────────────────────────────────────────────
async def manual_mode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = load_menu()
    context.user_data['menu'] = menu
    context.user_data['selected'] = []
    context.user_data['current_cat_idx'] = 0

    cats = list(menu.keys())
    context.user_data['categories'] = cats

    await update.message.reply_text(
        "✋ Ручной выбор меню\n\n"
        "Я буду показывать категории по одной.\n"
        "Выбирайте позиции или пропускайте категорию.",
        reply_markup=ReplyKeyboardRemove()
    )
    return await show_category(update, context)

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = context.user_data['categories']
    idx = context.user_data['current_cat_idx']

    if idx >= len(cats):
        return await manual_finish(update, context)

    cat = cats[idx]
    items = context.user_data['menu'][cat]
    guests = context.user_data['guests']
    fmt = context.user_data['format']
    portions = PORTIONS.get(fmt, PORTIONS["Фуршет"])
    portions_pp = portions.get(cat, 1)

    lines = [f"📂 {cat.upper()} ({idx+1}/{len(cats)})\n"]
    lines.append(f"Порций на человека: {portions_pp} шт.\n")

    keyboard = []
    for i, item in enumerate(items[:10], 1):
        total_portions = portions_pp * guests
        cost = item['price'] * total_portions
        lines.append(f"{i}. {item['name'][:50]}")
        lines.append(f"   {item['weight']:.0f}гр • {item['price']:.0f}₽/порц • {cost:,.0f}₽ всего".replace(',', ' '))
        keyboard.append([f"{i}. {item['name'][:35]}"])

    keyboard.append(["⏭️ Пропустить категорию", "✅ Готово — генерировать PDF"])

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    )
    return MANUAL_ITEMS

async def manual_select_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "Пропустить" in text:
        context.user_data['current_cat_idx'] += 1
        return await show_category(update, context)

    if "Готово" in text or "генерировать" in text:
        return await generate_and_send_pdf(update, context)

    # Парсим выбранную позицию
    cats = context.user_data['categories']
    idx = context.user_data['current_cat_idx']
    cat = cats[idx]
    items = context.user_data['menu'][cat]
    guests = context.user_data['guests']
    fmt = context.user_data['format']
    portions = PORTIONS.get(fmt, PORTIONS["Фуршет"])
    portions_pp = portions.get(cat, 1)

    try:
        num = int(text.split('.')[0]) - 1
        if 0 <= num < len(items):
            item = items[num]
            total_portions = portions_pp * guests
            cost = item['price'] * total_portions

            context.user_data['selected'].append({
                "category": cat.upper(),
                "name": item['name'],
                "qty": total_portions,
                "qty_label": f"{total_portions} порц.",
                "price": item['price'],
                "price_label": f"{item['price']:.0f} руб.",
                "total": cost,
                "total_label": f"{cost:,.0f} руб.".replace(',', ' '),
                "weight_per_person": item['weight'] * portions_pp,
                "desc": f"Выход {item['weight']:.0f} гр/порц.",
            })
            await update.message.reply_text(f"✅ Добавлено: {item['name']}")
    except:
        pass

    return MANUAL_ITEMS

async def manual_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected = context.user_data.get('selected', [])
    if not selected:
        await update.message.reply_text(
            "❌ Вы не выбрали ни одной позиции!\n"
            "Начните заново: /смета"
        )
        return ConversationHandler.END
    return await generate_and_send_pdf(update, context)

# ─── ГЕНЕРАЦИЯ PDF ─────────────────────────────────────────────
async def generate_and_send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from pdf_generator import generate_pdf

    await update.message.reply_text(
        "📄 Генерирую PDF смету...",
        reply_markup=ReplyKeyboardRemove()
    )

    data = context.user_data
    selected = data.get('selected', [])

    # Считаем итоги
    food_total = sum(item['total'] for item in selected)
    staff_total = data.get('staff_total', 0)
    grand_total = food_total + staff_total
    guests = data['guests']
    total_weight = sum(item.get('weight_per_person', 0) for item in selected) / max(len(selected), 1) * len(selected)

    event_data = {
        "client": data.get('client', ''),
        "format": data.get('format', ''),
        "guests": guests,
        "date": data.get('date', ''),
        "place": data.get('place', ''),
        "time": data.get('time', ''),
        "budget": data.get('budget', 0),
        "target_weight": data.get('weight', 0),
        "number": "001",
        "manager": "Елена Смирнова",
    }

    try:
        pdf_path = generate_pdf(event_data, selected, data.get('staff', {}), food_total, staff_total, grand_total)

        with open(pdf_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"Смета_{event_data['client']}_{event_data['date']}.pdf",
                caption=(
                    f"✅ Смета готова!\n\n"
                    f"👤 {event_data['client']}\n"
                    f"🍽️ {event_data['format']} • {guests} гостей\n"
                    f"📅 {event_data['date']}\n"
                    f"💰 Итого: {grand_total:,.0f} руб.\n"
                    f"👤 На персону: {grand_total//guests:,.0f} руб."
                ).replace(',', ' ')
            )
    except Exception as e:
        logging.error(f"Ошибка генерации PDF: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Отменено. Напишите /смета чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Справка SmiLe Catering Bot\n\n"
        "/смета — создать новую смету\n"
        "/отмена — отменить текущую смету\n\n"
        "Бот умеет:\n"
        "🤖 Авто-подбор меню под бюджет и выход\n"
        "✋ Ручной выбор позиций из Excel\n"
        "📄 Генерация PDF сметы в фирменном стиле"
    )

# ─── ЗАПУСК ────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("смета", new_smeta),
            CommandHandler("smeta", new_smeta),
        ],
        states={
            CLIENT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client)],
            FORMAT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_format)],
            GUESTS:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_guests)],
            DATE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            PLACE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_place)],
            TIME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            BUDGET:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            WEIGHT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            MODE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mode)],
            AUTO_CONFIRM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, auto_confirm)],
            MANUAL_ITEMS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_select_item)],
        },
        fallbacks=[
            CommandHandler("отмена", cancel),
            CommandHandler("cancel", cancel),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("помощь", help_cmd))
    app.add_handler(conv)

    print("🤖 SmiLe Catering Bot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
