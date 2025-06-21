from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from app.schemas.analytics import GlobalAnalytics


def generate_analytics_excel(ga: GlobalAnalytics) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Analytics"

    row = 1
    ws.append(["Метрика", "Значение"])
    ws.append(["Всего смет", ga.total_estimates])
    ws.append(["Общая сумма", ga.total_amount])
    ws.append(["Средняя сумма", ga.average_amount])
    ws.append(["Медиана по сметам", ga.median_amount])
    ws.append(["ARPU", ga.arpu])
    ws.append(["MoM рост (%)", ga.mom_growth or 0])
    ws.append(["YoY рост (%)", ga.yoy_growth or 0])
    row = ws.max_row + 2

    ws.append(["Период", "Сумма"])
    for item in ga.timeseries:
        ws.append([item.period, item.value])
    row = ws.max_row + 2

    ws.append(["Top-10 клиентов", "Выручка"])
    for cli in ga.top_clients:
        ws.append([cli.name, cli.total_amount])
    row = ws.max_row + 2

    ws.append(["Ответственный", "Число смет", "Выручка"])
    for r in ga.by_responsible:
        ws.append([r.name, r.estimates_count, r.total_amount])
    row = ws.max_row + 2

    ws.append(["Top-10 услуг", "Выручка"])
    for srv in ga.top_services:
        ws.append([srv.name, srv.total_amount])

    # auto width
    for col in ws.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(length + 3, 40)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
