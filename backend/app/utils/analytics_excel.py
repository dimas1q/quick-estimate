from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from app.schemas.analytics import GlobalAnalytics


def generate_analytics_excel(data: GlobalAnalytics) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Analytics"

    row = 1
    ws.cell(row=row, column=1, value="Ключевые метрики")
    row += 1
    metrics = [
        ("Всего смет", data.total_estimates),
        ("Общая сумма", data.total_amount),
        ("Средняя сумма", data.average_amount),
        ("Медиана по сметам", data.median_amount),
        ("ARPU", data.arpu),
        ("MoM рост (%)", data.mom_growth or 0),
        ("YoY рост (%)", data.yoy_growth or 0),
    ]
    for label, value in metrics:
        ws.append([label, value])
    row = ws.max_row + 2

    ws.cell(row=row, column=1, value="Период")
    ws.cell(row=row, column=2, value="Сумма")
    row += 1
    for ts in data.timeseries:
        ws.append([ts.period, ts.value])
    row = ws.max_row + 2

    ws.cell(row=row, column=1, value="Top-10 клиентов")
    ws.cell(row=row, column=2, value="Выручка")
    row += 1
    for c in data.top_clients:
        ws.append([c.name, c.total_amount])
    row = ws.max_row + 2

    ws.cell(row=row, column=1, value="Ответственный")
    ws.cell(row=row, column=2, value="Число смет")
    ws.cell(row=row, column=3, value="Выручка")
    row += 1
    for r in data.by_responsible:
        ws.append([r.name, r.estimates_count, r.total_amount])
    row = ws.max_row + 2

    ws.cell(row=row, column=1, value="Top-10 услуг")
    ws.cell(row=row, column=2, value="Выручка")
    row += 1
    for s in data.top_services:
        ws.append([s.name, s.total_amount])

    for column in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(column)].width = 18

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
