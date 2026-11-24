import base64
import binascii
import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


FIELDS = ("date", "position_id", "category", "channel", "event", "amount", "quantity")
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10_000

CHANNELS = {
    "personal": "Личная передача",
    "marketplace": "Покупка на маркетплейсе",
    "sbp": "Денежный взнос по СБП",
}
EVENT_CHANNELS = {
    "donation": {"sbp"},
    "purchase": {"sbp"},
    "accepted": {"personal", "marketplace"},
    "delivered": set(CHANNELS),
    "reported": set(CHANNELS),
}
MONEY_EVENTS = {"donation", "purchase"}
ITEM_EVENTS = {"accepted", "delivered"}


def parse_amount(value):
    amount = Decimal(value.replace(",", ".") or "0")
    if not amount.is_finite() or not 0 <= amount <= 100_000_000:
        raise ValueError("сумма должна быть от 0 до 100 000 000 ₽")
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError("в сумме допускается до двух знаков после запятой")
    return int(cents)


def parse_row(row):
    day = date.fromisoformat(row["date"])
    if row["date"] != day.isoformat():
        raise ValueError("дата должна иметь формат ГГГГ-ММ-ДД")

    channel, event = row["channel"], row["event"]
    if channel not in EVENT_CHANNELS.get(event, ()):
        raise ValueError("неизвестная операция или недопустимый для неё способ помощи")
    if any(not 1 <= len(row[field]) <= 80 for field in ("position_id", "category")):
        raise ValueError("укажите идентификатор и категорию длиной до 80 символов")

    try:
        cents = parse_amount(row["amount"])
        quantity = int(row["quantity"] or "0")
    except (InvalidOperation, ValueError) as error:
        raise ValueError("проверьте сумму и количество") from error
    if (event in MONEY_EVENTS and not (cents > 0 and quantity == 0)
            or event in ITEM_EVENTS and not (cents == 0 and 1 <= quantity <= 10_000)
            or event == "reported" and (cents or quantity)):
        raise ValueError("сумма и количество не соответствуют типу операции")

    return {"date": day.isoformat(), "position_id": row["position_id"],
            "category": row["category"], "channel": channel, "event": event,
            "cents": cents, "quantity": quantity}


def parse_upload(contents, filename):
    if not filename or not filename.lower().endswith(".csv"):
        raise ValueError("Выберите файл с расширением .csv.")
    _, separator, encoded = contents.partition(",")
    if not separator or len(encoded) > ((MAX_FILE_BYTES + 2) // 3) * 4:
        raise ValueError("CSV должен занимать не больше 2 МБ.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Не удалось прочитать содержимое файла.") from error
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("CSV должен занимать не больше 2 МБ.")
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            source = raw.decode("cp1251")
        except UnicodeDecodeError as error:
            raise ValueError("Сохраните CSV в кодировке UTF-8 или Windows-1251.") from error

    if not source.strip():
        raise ValueError("Файл пуст.")
    header = source.splitlines()[0]
    delimiter = ";" if ";" in header else ","
    reader = csv.DictReader(io.StringIO(source, newline=""), delimiter=delimiter, strict=True)
    records = []
    try:
        columns = reader.fieldnames or []
        reader.fieldnames = [column.strip() for column in columns]
        if len(columns) != len(FIELDS) or set(reader.fieldnames) != set(FIELDS):
            raise ValueError("Нужны столбцы: " + ", ".join(FIELDS) + ".")
        for row in reader:
            if len(records) >= MAX_ROWS:
                raise ValueError("В CSV должно быть не больше 10 000 строк данных.")
            if None in row or None in row.values():
                raise ValueError(f"Строка {reader.line_num}: проверьте число столбцов.")
            try:
                records.append(parse_row({key: value.strip() for key, value in row.items()}))
            except ValueError as error:
                raise ValueError(f"Строка {reader.line_num}: {error}.") from error
    except csv.Error as error:
        raise ValueError(f"Некорректный CSV около строки {reader.line_num}.") from error
    if not records:
        raise ValueError("В файле есть заголовки, но нет операций.")
    return records


def select_records(records, period, categories, channels):
    if not records:
        return []
    start = date.min.isoformat()
    if period in (30, 90, 365):
        end = date.fromisoformat(max(row["date"] for row in records))
        start = date.fromordinal(max(1, end.toordinal() - period + 1)).isoformat()
    return [row for row in records if row["date"] >= start
            and (not categories or row["category"] in categories)
            and (not channels or row["channel"] in channels)]


def aggregate(records):
    totals = {"donation": 0, "purchase": 0, "delivered": 0, "reported": 0}
    by_category = {}
    by_week = defaultdict(lambda: {"donation": 0, "purchase": 0})
    donations = []
    for row in records:
        category = by_category.setdefault(row["category"], dict.fromkeys(totals, 0))
        event = row["event"]
        if event in MONEY_EVENTS:
            value = row["cents"]
            day = date.fromisoformat(row["date"])
            by_week[day - timedelta(days=day.weekday())][event] += value
            if event == "donation":
                donations.append(value)
        elif event == "delivered":
            value = row["quantity"]
        elif event == "reported":
            value = 1
        else:
            continue
        totals[event] += value
        category[event] += value
    return totals, by_category, dict(sorted(by_week.items())), donations
