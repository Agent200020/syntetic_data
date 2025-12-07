import random
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from collections import defaultdict

# ----------------------
# Справочники
# ----------------------
# ----------------------
# Районы Самары + координаты (приблизительные центры)
# ----------------------


regions = [
    {"name": "Ленинский", "postal": "443010", "lat": 53.1950, "lon": 50.0950},
    {"name": "Кировский", "postal": "443001", "lat": 53.2500, "lon": 50.2100},
    {"name": "Советский", "postal": "443050", "lat": 53.2250, "lon": 50.2500},
    {"name": "Октябрьский", "postal": "443020", "lat": 53.2100, "lon": 50.1650},
    {"name": "Железнодорожный", "postal": "443041", "lat": 53.2150, "lon": 50.1300},
    {"name": "Самарский", "postal": "443099", "lat": 53.1950, "lon": 50.1250},
    {"name": "Промышленный", "postal": "443029", "lat": 53.2350, "lon": 50.1800},
    {"name": "Красноглинский", "postal": "443048", "lat": 53.3050, "lon": 50.3150}
]

def jitter_km(lat, lon, radius_km=3):
    dist_km = random.uniform(2, 4)
    angle = random.uniform(0, 2*math.pi)
    dlat = (dist_km/111) * math.cos(angle)  
    dlon = (dist_km/(111*math.cos(math.radians(lat)))) * math.sin(angle)
    return lat + dlat, lon + dlon

mcc_categories = {
    "5411": "Продуктовый магазин",
    "5812": "Рестораны",
    "5912": "Аптеки",
    "4111": "Транспорт",
    "5311": "Универсальные магазины",
    "6012": "Финансовые услуги",
    "5541": "АЗС",
    "7997": "Фитнес-центры",
    "5651": "Одежда",
    "5732": "Электроника"
}

channel_payment_map = {
    "POS": ["NFC", "Chip", "Swipe"],
    "e-commerce": ["Online", "QR"],
    "MOTO": ["Online", "Chip"],
    "mobile_app": ["NFC", "QR", "Online"],
    "self_service": ["NFC", "QR", "Chip"]
}

channels = ["POS", "e-commerce", "MOTO", "mobile_app", "self_service"]

channel_amount_multipliers = {
    "POS": 1.0,
    "e-commerce": 1.5,
    "MOTO": 1.2,
    "mobile_app": 1.3,
    "self_service": 0.8
}

month_activity_factor = {
    1: 0.7,
    2: 0.7,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 1.2,
    7: 1.2,
    8: 1.0,
    9: 1.0,
    10: 1.0,
    11: 1.0,
    12: 1.5
}

currencies = ["RUB", "USD", "EUR"]

# ----------------------
# Weighted MCC (чтобы продукты встречались чаще)
# ----------------------
def weighted_mcc(region_name):
    return random.choices(
        population=list(mcc_categories.keys()),
        weights=[0.3 if k == "5411" else 0.1 for k in mcc_categories.keys()],
    )[0]

# ----------------------
# Генерация мерчантов
# ----------------------

def jitter_coordinates(lat, lon, jitter_m=200):
    """
    Добавляет случайный джиттер (смещение) к координатам.
    jitter_m — радиус джиттера в метрах (по умолчанию 200м).
    """
    import math
    # 1 градус широты примерно 111 000 метров
    lat_jitter = (random.uniform(-1, 1) * jitter_m) / 111000
    # 1 градус долготы зависит от широты
    lon_jitter = (random.uniform(-1, 1) * jitter_m) / (111000 * math.cos(math.radians(lat)))
    return lat + lat_jitter, lon + lon_jitter


merchants = []
merchant_inns = set()
for region in regions:
    for i in range(5):
        inn = str(random.randint(1000000000, 9999999999))
        while inn in merchant_inns:
            inn = str(random.randint(1000000000, 9999999999))
        merchant_inns.add(inn)
        mcc = weighted_mcc(region["name"])
        merchants.append({
            "merchant_name": f"{mcc_categories[mcc]} #{i+1} ({region['name']})",
            "merchant_inn": inn,
            "merchant_location": region["name"],
            "merchant_postal_code": region["postal"],
            "terminal_id": f"T{random.randint(10000,99999)}",
            "mcc": mcc,
            "category": mcc_categories[mcc]
        })


# ----------------------
# Генерация клиентов
# ----------------------
clients = [str(random.randint(100000000000, 999999999999)) for _ in range(3000)]

# ----------------------
# Подготовка словарей
# ----------------------
region_weights = {
    "Ленинский": 12,
    "Кировский": 14,
    "Советский": 13,
    "Октябрьский": 10,
    "Железнодорожный": 9,
    "Самарский": 8,
    "Промышленный": 18,
    "Красноглинский": 6
}


region_merchants = {r["name"]: [] for r in regions}
for m in merchants:
    region_merchants[m["merchant_location"]].append(m)

region_names = list(region_weights.keys())
region_probs = list(region_weights.values())

# ----------------------
# Суммы по MCC
# ----------------------
def generate_amount_by_mcc(mcc):
    avg_amounts = {
        "5411": 1500,   # Продуктовый магазин
        "5812": 3000,   # Рестораны
        "5912": 1000,   # Аптеки (оставим дефолт)
        "4111": 300,    # Транспорт
        "5311": 700,    # Универсальные магазины
        "6012": 4000,   # Финансовые услуги
        "5541": 2000,   # АЗС
        "7997": 4000,   # Фитнес-центры
        "5651": 5000,   # Одежда
        "5732": 12000   # Электроника
    }

    base = avg_amounts.get(mcc, 2000)  # Фолбэк если вдруг что-то пошло не так

    # Разброс +-20%
    min_amount = base * 0.8
    max_amount = base * 1.2

    amount = round(random.uniform(min_amount, max_amount), 2)

    # Сегмент по сумме
    if amount < 1000:
        segment = "low"
    elif amount < 5000:
        segment = "mid"
    else:
        segment = "high"

    return amount, segment


# ----------------------
# Паттерны по времени
# ----------------------
hours = list(range(24))
base_hour_weights = [
    1,1,1,   # 0-3 ночь
    2,3,4,     # 4-6 рассвет
    8,10,10,   # 7-9 утро
    8,7,6,     # 10-12 день
    7,8,10,    # 13-15 обед
    10,10,9,   # 16-18 вечер
    8,6,4,     # 19-21 спад
    3,2,1      # 22-23 ночь
]

def choose_transaction_date(start_date, end_date):
    days_count = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(days_count)]
    weights = []
    for d in dates:
        w = month_activity_factor.get(d.month, 1.0)
        if d.month == 12 and 20 <= d.day <= 31:
            w *= 3
        if d.month == 11 and d.weekday() == 4 and 22 <= d.day <= 28:
            w *= 2
        weights.append(w)
    return random.choices(dates, weights=weights, k=1)[0]

# ----------------------
# Лояльность и активность
# ----------------------
def generate_loyalty_and_activity(customer_segment, repeat_customer, loyalty_program):
    base_scores = {
        "retail": (0.3, 0.6),
        "b2b": (0.5, 0.8),
        "vip": (0.7, 0.95),
        "youth": (0.2, 0.5)
    }

    # Выбираем базу по сегменту
    min_base, max_base = base_scores.get(customer_segment, (0.4, 0.6))
    
    # Генерируем лояльность из диапазона
    loyalty = random.uniform(min_base, max_base)

    # Прибавка за участие в программе и повторные покупки
    if repeat_customer:
        loyalty += random.uniform(0.02, 0.05)
    if loyalty_program == "yes":
        loyalty += random.uniform(0.02, 0.05)

    # Шум: аддитивный, от -0.1 до +0.1
    noise = random.uniform(-0.1, 0.1)
    loyalty += noise

    # Ограничиваем диапазон
    loyalty = max(0.0, min(1.0, loyalty))

    # Аналогично для активности
    activity = random.uniform(0.3, 0.9)
    activity = max(0.0, min(1.0, activity))

    return loyalty, activity



# ----------------------
# Основной цикл генерации
# ----------------------
end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
start_date = end_date - timedelta(days=365)

records = []
n_transactions = 2353 

for _ in range(n_transactions):
    channel = random.choices(channels, weights=[0.25,0.15,0.2,0.3,0.1])[0]
    payment_type = random.choice(channel_payment_map[channel])

    region = random.choices(region_names, weights=region_probs)[0]
    merchant = random.choice(region_merchants[region])
    client = random.choice(clients)

    tx_date = choose_transaction_date(start_date, end_date)
    weekday = tx_date.weekday()
    hour_weights = base_hour_weights.copy()
    if weekday >= 5:  # выходные
        hour_weights[10] += 3
        hour_weights[20] += 4
        hour_weights[21] += 4
        hour_weights[22] += 2
    hour = random.choices(hours, weights=hour_weights)[0]
    minute, second = random.randint(0,59), random.randint(0,59)

    currency_tx = random.choices(currencies, weights=[0.85,0.1,0.05])[0]
    currency_card = random.choices(currencies, weights=[0.8,0.15,0.05])[0]
    conversion = 1.0
    if currency_tx != currency_card:
        conversion = round(random.uniform(90,110),2)

    amount, segment = generate_amount_by_mcc(merchant["mcc"])
    amount *= channel_amount_multipliers[channel]
    amount = round(amount,2)

    customer_segment = random.choice(["retail","b2b","vip","youth"])
    repeat_customer = random.choice([True,False])
    loyalty_program = random.choice(["yes","no"])
    loyalty_score, annual_activity_score = generate_loyalty_and_activity(customer_segment, repeat_customer, loyalty_program)

    record = {
        "merchant_name": merchant["merchant_name"],
        "merchant_inn": merchant["merchant_inn"],
        "merchant_location": merchant["merchant_location"],
        "merchant_postal_code": merchant["merchant_postal_code"],
        "terminal_id": merchant["terminal_id"],
        "channel": channel,
        "mcc": merchant["mcc"],
        "currency_transaction": currency_tx,
        "currency_card": currency_card,
        "conversion_rate": conversion,
        "payer_inn": client,
        "category": merchant["category"],
        "amount": amount,
        "date": tx_date.strftime("%Y-%m-%d"),
        "time": f"{hour:02d}:{minute:02d}:{second:02d}",
        "day_of_week": tx_date.strftime("%A"),
        "month": tx_date.strftime("%B"),
        "year": tx_date.year,
        "hour": hour,
        "is_weekend": weekday>=5,
        "is_evening": hour>=19,
        "amount_segment": segment,
        "region": merchant["merchant_location"],
        "channel_group": "digital" if merchant["category"] in ["Электроника","Финансовые услуги"] else "offline",
        "currency_group": "domestic" if currency_tx=="RUB" else "foreign",
        "payment_type": payment_type,
        "is_cross_region": random.choice([True,False]),
        "customer_segment": customer_segment,
        "ticket_size": "small" if amount<1000 else ("medium" if amount<5000 else "large"),
        "merchant_type": merchant["category"],
        "channel_type": "online" if random.random()<0.3 else "offline",
        "holiday_flag": random.choice([0,1]),
        "repeat_customer": repeat_customer,
        "device_type": random.choice(["mobile","desktop","pos_terminal"]),
        "loyalty_program": loyalty_program,
        "age_group": random.choice(["18-25","26-35","36-50","50+"]),
        "income_level": random.choice(["low","middle","high"]),
        "education": random.choice(["school","college","university","phd"]),
        "family_status": random.choice(["single","married","kids"]),
        "occupation": random.choice(["student","employee","self-employed","retired"]),
        "visit_frequency": random.choice(["rare","regular","frequent"]),
        "fraud_flag": random.choice([0,0,0,1]),
        "discount_used": random.choice(["yes","no"]),
        "campaign": random.choice(["A","B","C"]),
        "loyalty_score": round(loyalty_score,3),
        "annual_activity_score": round(annual_activity_score,3)
    }
    records.append(record)

# ----------------------
# Сохранение
# ----------------------
df = pd.DataFrame(records)
out_path = "static/data/transactions_extend.json"
df.to_json(out_path, orient="records", force_ascii=False, indent=2)
print(f"✅ Сохранено {len(df)} транзакций в {out_path}")

region_coords = {r["name"]: (r["lat"], r["lon"]) for r in regions}

# Добавляем координаты в DataFrame
df["lat"] = df["region"].map(lambda x: region_coords[x][0])
df["lon"] = df["region"].map(lambda x: region_coords[x][1])


excel_out = "static/data/transactions_extend.xlsx"
df.to_excel(excel_out, index=False, engine='openpyxl')
print(f"✅ Сохранено {len(df)} транзакций в {out_path} и {excel_out}")

