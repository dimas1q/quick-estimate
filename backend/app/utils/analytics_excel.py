from io import BytesIO
from openpyxl import Workbook
from app.schemas.analytics import GlobalAnalytics


def generate_analytics_excel(ga: GlobalAnalytics) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Analytics'

    ws.append(['\u041c\u0435\u0442\u0440\u0438\u043a\u0430', '\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435'])
    metrics = [
        ('\u0412\u0441\u0435\u0433\u043e \u0441\u043c\u0435\u0442', ga.total_estimates),
        ('\u041e\u0431\u0449\u0430\u044f \u0441\u0443\u043c\u043c\u0430', ga.total_amount),
        ('\u0421\u0440\u0435\u0434\u043d\u044f\u044f \u0441\u0443\u043c\u043c\u0430', ga.average_amount),
        ('\u041c\u0435\u0434\u0438\u0430\u043d\u0430 \u043f\u043e \u0441\u043c\u0435\u0442\u0430\u043c', ga.median_amount),
        ('ARPU', ga.arpu),
        ('MoM \u0440\u043e\u0441\u0442 (%)', ga.mom_growth or 0),
        ('YoY \u0440\u043e\u0441\u0442 (%)', ga.yoy_growth or 0),
    ]
    for row in metrics:
        ws.append(list(row))

    ws.append([])
    ws.append(['\u041f\u0435\u0440\u0438\u043e\u0434', '\u0421\u0443\u043c\u043c\u0430'])
    for ts in ga.timeseries:
        ws.append([ts.period, ts.value])

    ws.append([])
    ws.append(['Top-10 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432', '\u0412\u044b\u0440\u0443\u0447\u043a\u0430'])
    for cli in ga.top_clients:
        ws.append([cli.name, cli.total_amount])

    ws.append([])
    ws.append(['\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439', '\u0427\u0438\u0441\u043b\u043e \u0441\u043c\u0435\u0442', '\u0412\u044b\u0440\u0443\u0447\u043a\u0430'])
    for r in ga.by_responsible:
        ws.append([r.name, r.estimates_count, r.total_amount])

    ws.append([])
    ws.append(['Top-10 \u0443\u0441\u043b\u0443\u0433', '\u0412\u044b\u0440\u0443\u0447\u043a\u0430'])
    for srv in ga.top_services:
        ws.append([srv.name, srv.total_amount])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
