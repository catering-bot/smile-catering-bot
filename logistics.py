"""
Модуль расчёта логистики для SmiLe Catering Bot
"""

# ─── НОРМЫ ОБОРУДОВАНИЯ ────────────────────────────────────────

LOGISTICS = {
    "Фуршет": {
        "мебель": [
            ("Стол фуршетный высокий", lambda g: -(-g // 6), 1000),  # 1 на 6 гостей
        ],
        "сервировка_пакеты": {
            "💚 Эконом (одноразовая посуда)": 250,
            "💛 Стандарт (керамика + стекло)": 350,
            "💎 Премиум (керамика + стекло + декор)": 450,
        },
        "доп_оборудование": [
            ("Скатерть фуршетная", lambda g: -(-g // 6), 0),
            ("Салфетки (пачка 100шт)", lambda g: -(-g * 3 // 100), 0),
        ],
    },
    "Банкет": {
        "мебель": [
            ("Стол банкетный круглый", lambda g: -(-g // 8), 900),
            ("Стул банкетный", lambda g: g, 200),
        ],
        "сервировка_пакеты": {
            "💛 Стандарт (керамика + стекло)": 450,
            "💎 Премиум (керамика + стекло + декор)": 550,
        },
        "доп_оборудование": [
            ("Скатерть банкетная", lambda g: -(-g // 8), 0),
            ("Салфетки (пачка 100шт)", lambda g: -(-g * 3 // 100), 0),
        ],
    },
    "BBQ": {
        "мебель": [
            ("Стол прямоугольный", lambda g: -(-g // 8), 500),
            ("Стул банкетный", lambda g: g, 200),
        ],
        "сервировка_пакеты": {
            "💚 Эконом (одноразовая посуда)": 250,
            "💛 Стандарт (керамика + стекло)": 350,
        },
        "доп_оборудование": [
            ("Скатерть", lambda g: -(-g // 8), 0),
            ("Салфетки (пачка 100шт)", lambda g: -(-g * 3 // 100), 0),
        ],
    },
    "Кофе-брейк": {
        "мебель": [
            ("Стол фуршетный высокий", lambda g: -(-g // 6), 1000),
        ],
        "сервировка_пакеты": {
            "💛 Стандарт (керамика + стекло)": 350,
            "💎 Премиум (керамика + стекло + декор)": 450,
        },
        "доп_оборудование": [
            ("Скатерть фуршетная", lambda g: -(-g // 6), 0),
        ],
    },
}

DELIVERY = {
    "Москва": 10000,
    "МО": 15000,
}

GAZELLE_CAPACITY_KG = 1000

# Примерный вес оборудования
ITEM_WEIGHT = {
    "Стол банкетный круглый": 15,
    "Стол фуршетный высокий": 10,
    "Стол прямоугольный": 8,
    "Стул банкетный": 4,
    "Скатерть банкетная": 1,
    "Скатерть фуршетная": 0.5,
    "Скатерть": 0.5,
    "Салфетки (пачка 100шт)": 0.3,
}


def calc_logistics(fmt: str, guests: int, servicing_package: str, delivery_zone: str) -> dict:
    """
    Рассчитывает полную логистику мероприятия.
    Возвращает словарь с деталями расчёта.
    """
    config = LOGISTICS.get(fmt, LOGISTICS["Фуршет"])

    result = {
        "format": fmt,
        "guests": guests,
        "servicing_package": servicing_package,
        "delivery_zone": delivery_zone,
        "furniture": [],
        "servicing_cost": 0,
        "delivery_cost": DELIVERY.get(delivery_zone, 10000),
        "furniture_cost": 0,
        "total_weight_kg": 0,
        "trips_needed": 1,
        "total_logistics": 0,
        "lines": [],
    }

    # ── Мебель ──
    for name, qty_fn, price in config["мебель"]:
        qty = qty_fn(guests)
        cost = qty * price
        weight = qty * ITEM_WEIGHT.get(name, 5)
        result["furniture"].append({
            "name": name,
            "qty": qty,
            "price": price,
            "cost": cost,
            "weight": weight,
        })
        result["furniture_cost"] += cost
        result["total_weight_kg"] += weight

    # ── Доп оборудование (вес считаем, цена 0) ──
    for name, qty_fn, price in config.get("доп_оборудование", []):
        qty = qty_fn(guests)
        weight = qty * ITEM_WEIGHT.get(name, 0.5)
        result["total_weight_kg"] += weight

    # ── Сервировка ──
    packages = config.get("сервировка_пакеты", {})
    pkg_price = packages.get(servicing_package, list(packages.values())[0])
    result["servicing_cost"] = pkg_price * guests

    # ── Количество рейсов Газели ──
    result["trips_needed"] = max(1, -(-result["total_weight_kg"] // GAZELLE_CAPACITY_KG))

    # ── Итого ──
    result["total_logistics"] = (
        result["furniture_cost"] +
        result["servicing_cost"] +
        result["delivery_cost"] * result["trips_needed"]
    )

    return result


def format_logistics_message(r: dict) -> str:
    """Форматирует результат в красивое сообщение для Telegram"""
    lines = [
        f"🚚 ЛОГИСТИКА МЕРОПРИЯТИЯ\n",
        f"📋 {r['format']} • {r['guests']} гостей",
        f"📍 Доставка: {r['delivery_zone']}",
        f"{'='*35}",
        "",
        "🪑 МЕБЕЛЬ:",
    ]

    for item in r["furniture"]:
        if item["price"] > 0:
            lines.append(f"  • {item['name']} — {item['qty']} шт.")
            lines.append(f"    {item['qty']} × {item['price']:,} руб. = {item['cost']:,} руб.".replace(',', ' '))
        else:
            lines.append(f"  • {item['name']} — {item['qty']} шт.")

    lines += [
        "",
        f"🍽️ СЕРВИРОВКА:",
        f"  • {r['servicing_package']}",
        f"    {r['guests']} чел. × {r['servicing_cost']//r['guests']:,} руб. = {r['servicing_cost']:,} руб.".replace(',', ' '),
        "",
        f"🚛 ДОСТАВКА ({r['delivery_zone']}):",
        f"  • Газель Некст (до 1 тонны)",
        f"  • Рейсов: {r['trips_needed']} шт.",
        f"  • {r['trips_needed']} × {r['delivery_cost']:,} руб. = {r['delivery_cost'] * r['trips_needed']:,} руб.".replace(',', ' '),
        f"  • Примерный вес груза: {r['total_weight_kg']:.0f} кг",
        "",
        f"{'='*35}",
        f"🪑 Мебель: {r['furniture_cost']:,} руб.".replace(',', ' '),
        f"🍽️ Сервировка: {r['servicing_cost']:,} руб.".replace(',', ' '),
        f"🚛 Доставка: {r['delivery_cost'] * r['trips_needed']:,} руб.".replace(',', ' '),
        f"{'='*35}",
        f"💰 ИТОГО ЛОГИСТИКА: {r['total_logistics']:,} руб.".replace(',', ' '),
        f"👤 На персону: {r['total_logistics']//r['guests']:,} руб.".replace(',', ' '),
    ]

    return "\n".join(lines)
