from io import BytesIO
from openpyxl import Workbook
from app.schemas.analytics import GlobalAnalytics

def generate_analytics_excel(ga: GlobalAnalytics) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Metrics"

    ws.append(["Метрика", "Значение"])
    ws.append(["Всего смет", ga.total_estimates])
    ws.append(["Общая сумма", ga.total_amount])
    ws.append(["Средняя сумма", ga.average_amount])
    ws.append(["Медиана по сметам", ga.median_amount])
    ws.append(["ARPU", ga.arpu])
    ws.append(["MoM рост (%)", ga.mom_growth or 0])
    ws.append(["YoY рост (%)", ga.yoy_growth or 0])

    ws_ts = wb.create_sheet("Timeseries")
    ws_ts.append(["Период", "Сумма"])
    for item in ga.timeseries:
        ws_ts.append([item.period, item.value])

    ws_clients = wb.create_sheet("Top clients")
    ws_clients.append(["Клиент", "Выручка"])
    for c in ga.top_clients:
        ws_clients.append([c.name, c.total_amount])

    ws_resp = wb.create_sheet("By responsible")
    ws_resp.append(["Ответственный", "Сметы", "Выручка"])
    for r in ga.by_responsible:
        ws_resp.append([r.name, r.estimates_count, r.total_amount])

    ws_srv = wb.create_sheet("Top services")
    ws_srv.append(["Услуга", "Выручка"])
    for s in ga.top_services:
        ws_srv.append([s.name, s.total_amount])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
