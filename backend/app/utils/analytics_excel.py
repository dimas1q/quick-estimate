from io import BytesIO
from openpyxl import Workbook
from app.schemas.analytics import GlobalAnalytics, ClientAnalytics


def generate_analytics_excel(analytics: GlobalAnalytics | ClientAnalytics) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Analytics"

    ws.append(["Метрика", "Значение"])
    ws.append(["Всего смет", analytics.total_estimates])
    ws.append(["Общая сумма", analytics.total_amount])
    ws.append(["Средняя сумма", analytics.average_amount])
    ws.append(["Медиана по сметам", analytics.median_amount])
    if hasattr(analytics, "arpu"):
        ws.append(["ARPU", getattr(analytics, "arpu")])
    ws.append(["MoM рост (%)", analytics.mom_growth or 0])
    ws.append(["YoY рост (%)", analytics.yoy_growth or 0])
    ws.append([])

    ws.append(["Период", "Сумма"])
    for ts in analytics.timeseries:
        ws.append([ts.period, ts.value])
    ws.append([])

    if hasattr(analytics, "top_clients"):
        ws.append(["Top клиентов", "Выручка"])
        for c in analytics.top_clients:
            ws.append([c.name, c.total_amount])
        ws.append([])

    ws.append(["Ответственный", "Число смет", "Выручка"])
    for r in analytics.by_responsible:
        ws.append([r.name, r.estimates_count, r.total_amount])
    ws.append([])

    ws.append(["Top услуг", "Выручка"])
    for s in analytics.top_services:
        ws.append([s.name, s.total_amount])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
