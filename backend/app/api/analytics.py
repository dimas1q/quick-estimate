# backend/app/api/analytics.py

import io
import csv
import subprocess

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.utils.auth import get_current_user
from app.models.client import Client
from app.models.estimate import Estimate, EstimateStatus
from app.models.item import EstimateItem
from app.schemas.analytics import (
    ClientAnalytics,
    GlobalAnalytics,
    TimeSeriesItem,
    ServiceMetric,
    ResponsibleMetric,
    GranularityEnum,
)

router = APIRouter(tags=["analytics"], dependencies=[Depends(get_current_user)])


def _make_period_expr(granularity: GranularityEnum):
    # для квартала используем специальный формат
    if granularity == GranularityEnum.quarter:
        return func.to_char(Estimate.date, 'YYYY-"Q"Q').label("period")

    fmt_map = {
        GranularityEnum.day: "YYYY-MM-DD",
        GranularityEnum.week: "IYYY-IW",
        GranularityEnum.month: "YYYY-MM",
        GranularityEnum.year: "YYYY",
    }
    fmt = fmt_map[granularity]
    # date_trunc поддерживает все, кроме квартала
    return func.to_char(func.date_trunc(granularity.value, Estimate.date), fmt).label(
        "period"
    )


def compute_growth(
    ts: List[TimeSeriesItem],
    granularity: GranularityEnum,
) -> tuple[float | None, float | None]:
    # без двух точек роста не посчитать
    if len(ts) < 2:
        return None, None

    last = ts[-1]
    lookup = {item.period: item.value for item in ts}

    # разбор последнего периода и вычисление ключей “предыдущего” MoM и YoY
    if granularity == GranularityEnum.day:
        # формат YYYY-MM-DD
        dt = datetime.strptime(last.period, "%Y-%m-%d")
        prev_dt = dt - relativedelta(days=1)
        prev_key = prev_dt.strftime("%Y-%m-%d")
        yoy_dt = dt - relativedelta(years=1)
        yoy_key = yoy_dt.strftime("%Y-%m-%d")

    elif granularity == GranularityEnum.week:
        # формат IYYY-IW, например "2025-05" (ISO-год-неделя)
        year_str, week_str = last.period.split("-")
        iso_year, iso_week = int(year_str), int(week_str)
        # понедельник той недели
        dt = datetime.fromisocalendar(iso_year, iso_week, 1)
        prev_dt = dt - relativedelta(weeks=1)
        py_year, py_week, _ = prev_dt.isocalendar()
        prev_key = f"{py_year}-{py_week:02d}"
        yoy_dt = dt - relativedelta(years=1)
        yy_year, yy_week, _ = yoy_dt.isocalendar()
        yoy_key = f"{yy_year}-{yy_week:02d}"

    elif granularity == GranularityEnum.month:
        # формат YYYY-MM
        dt = datetime.strptime(last.period, "%Y-%m")
        prev_dt = dt - relativedelta(months=1)
        prev_key = prev_dt.strftime("%Y-%m")
        yoy_dt = dt - relativedelta(years=1)
        yoy_key = yoy_dt.strftime("%Y-%m")

    elif granularity == GranularityEnum.quarter:
        # формат YYYY-Qn, например "2025-Q2"
        year_str, q_str = last.period.split("-Q")
        year, quarter = int(year_str), int(q_str)
        # первая дата квартала
        month = (quarter - 1) * 3 + 1
        dt = datetime(year, month, 1)
        prev_dt = dt - relativedelta(months=3)
        py_year = prev_dt.year
        py_quarter = (prev_dt.month - 1) // 3 + 1
        prev_key = f"{py_year}-Q{py_quarter}"
        yoy_dt = dt - relativedelta(years=1)
        yy_year = yoy_dt.year
        # тот же квартал год назад
        yoy_key = f"{yy_year}-Q{quarter}"

    elif granularity == GranularityEnum.year:
        # формат YYYY
        dt = datetime.strptime(last.period, "%Y")
        prev_dt = dt - relativedelta(years=1)
        prev_key = prev_dt.strftime("%Y")
        # для YoY та же дата
        yoy_key = prev_key

    else:
        return None, None

    prev_val = lookup.get(prev_key)
    yoy_val = lookup.get(yoy_key)

    mom = ((last.value - prev_val) / prev_val * 100) if prev_val else None
    yoy = ((last.value - yoy_val) / yoy_val * 100) if yoy_val else None

    return mom, yoy


@router.get(
    "/clients/{client_id}",
    response_model=ClientAnalytics,
    summary="Аналитика по конкретному клиенту",
)
async def get_client_analytics(
    client_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[List[EstimateStatus]] = Query(None),
    vat_enabled: Optional[bool] = Query(None),
    granularity: GranularityEnum = Query(GranularityEnum.month),
    categories: Optional[List[str]] = Query(
        None, description="Фильтр по названиям категорий услуг"
    ),
    db: AsyncSession = Depends(get_db),
):
    # составляем общий фильтр
    filters = [Estimate.client_id == client_id]
    if start_date:
        filters.append(Estimate.date >= start_date)
    if end_date:
        filters.append(Estimate.date <= end_date)
    if status:
        filters.append(Estimate.status.in_(status))
    if vat_enabled is not None:
        filters.append(Estimate.vat_enabled == vat_enabled)

    revenue_filters = []  # список фильтров для join(Estimate.items)
    if categories:
        lowered = [c.lower() for c in categories]
        revenue_filters.append(func.lower(EstimateItem.category).in_(lowered))

    if categories:
        q_cnt = (
            select(func.count(func.distinct(Estimate.id)))
            .select_from(Estimate)
            .join(Estimate.items)
            .where(*filters, *revenue_filters)
        )
    else:
        q_cnt = select(func.count()).select_from(Estimate).where(*filters)

    total_estimates = (await db.execute(q_cnt)).scalar_one()
    if total_estimates == 0:
        raise HTTPException(404, "Смет по данным фильтрам не найдено")

    # total revenue
    revenue_expr = EstimateItem.quantity * EstimateItem.unit_price
    q_sum = (
        select(func.coalesce(func.sum(revenue_expr), 0.0))
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
    )
    total_amount = (await db.execute(q_sum)).scalar_one()
    average_amount = total_amount / total_estimates

    # time series
    period = _make_period_expr(granularity)
    q_ts = (
        select(period, func.coalesce(func.sum(revenue_expr), 0.0).label("value"))
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by("period")
        .order_by("period")
    )
    ts_rows = (await db.execute(q_ts)).all()
    timeseries = [TimeSeriesItem(period=r.period, value=r.value) for r in ts_rows]

    mom, yoy = compute_growth(timeseries, granularity)

    # top-3 services
    q_top = (
        select(
            EstimateItem.name.label("name"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("total_amount"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(EstimateItem.name)
        .order_by(desc("total_amount"))
        .limit(3)
    )
    top_rows = (await db.execute(q_top)).all()
    top_services = [
        ServiceMetric(name=r.name, total_amount=r.total_amount) for r in top_rows
    ]

    # by_responsible для данного клиента
    q_resp = (
        select(
            Estimate.responsible.label("name"),
            func.count(func.distinct(Estimate.id)).label("estimates_count"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("total_amount"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(Estimate.client_id == client_id, *filters, *revenue_filters)
        .group_by(Estimate.responsible)
    )
    resp_rows = (await db.execute(q_resp)).all()
    by_responsible = [
        ResponsibleMetric(
            name=r.name,
            estimates_count=r.estimates_count,
            total_amount=r.total_amount,
        )
        for r in resp_rows
    ]

    subq = (
        select(
            Estimate.id.label("estimate_id"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("estimate_total"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(Estimate.id)
        .subquery()
    )

    median_expr = func.percentile_cont(0.5).within_group(subq.c.estimate_total.asc())

    q_median = select(median_expr).select_from(subq)
    median_res = (await db.execute(q_median)).scalar_one_or_none()
    median_amount = median_res or 0.0

    return ClientAnalytics(
        client_id=client_id,
        total_estimates=total_estimates,
        total_amount=total_amount,
        average_amount=average_amount,
        timeseries=timeseries,
        top_services=top_services,
        by_responsible=by_responsible,
        granularity=granularity,
        median_amount=median_amount,
        mom_growth=mom,
        yoy_growth=yoy,
    )


@router.get(
    "/",
    response_model=GlobalAnalytics,
    summary="Глобальная аналитика по всем клиентам",
)
async def get_global_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[List[EstimateStatus]] = Query(None),
    vat_enabled: Optional[bool] = Query(None),
    granularity: GranularityEnum = Query(GranularityEnum.month),
    categories: Optional[List[str]] = Query(
        None, description="Фильтр по названиям категорий услуг"
    ),
    db: AsyncSession = Depends(get_db),
):
    # общий фильтр
    filters = []
    if start_date:
        filters.append(Estimate.date >= start_date)
    if end_date:
        filters.append(Estimate.date <= end_date)
    if status:
        filters.append(Estimate.status.in_(status))
    if vat_enabled is not None:
        filters.append(Estimate.vat_enabled == vat_enabled)

    revenue_filters = []
    if categories:
        lowered = [c.lower() for c in categories]
        revenue_filters.append(func.lower(EstimateItem.category).in_(lowered))

    if categories:
        q_cnt = (
            select(func.count(func.distinct(Estimate.id)))
            .select_from(Estimate)
            .join(Estimate.items)
            .where(*filters, *revenue_filters)
        )
    else:
        q_cnt = select(func.count()).select_from(Estimate).where(*filters)

    total_estimates = (await db.execute(q_cnt)).scalar_one()
    if total_estimates == 0:
        raise HTTPException(404, "Смет по данным фильтрам не найдено")

    # total revenue
    revenue_expr = EstimateItem.quantity * EstimateItem.unit_price
    q_sum = (
        select(func.coalesce(func.sum(revenue_expr), 0.0))
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
    )
    total_amount = (await db.execute(q_sum)).scalar_one()
    average_amount = total_amount / total_estimates if total_estimates else 0.0

    # time series
    period = _make_period_expr(granularity)
    q_ts = (
        select(period, func.coalesce(func.sum(revenue_expr), 0.0).label("value"))
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by("period")
        .order_by("period")
    )
    ts_rows = (await db.execute(q_ts)).all()
    timeseries = [TimeSeriesItem(period=r.period, value=r.value) for r in ts_rows]

    mom, yoy = compute_growth(timeseries, granularity)

    # top-10 clients (по имени)
    q_clients = (
        select(
            Client.name.label("name"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("total_amount"),
        )
        .select_from(Estimate)
        .join(Estimate.client)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(Client.name)
        .order_by(desc("total_amount"))
        .limit(10)
    )
    cl_rows = (await db.execute(q_clients)).all()
    top_clients = [
        ServiceMetric(name=r.name, total_amount=r.total_amount) for r in cl_rows
    ]

    # by responsible: и кол-во, и сумма
    q_resp = (
        select(
            Estimate.responsible.label("name"),
            func.count(func.distinct(Estimate.id)).label("estimates_count"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("total_amount"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(Estimate.responsible)
    )
    resp_rows = (await db.execute(q_resp)).all()
    by_responsible = [
        ResponsibleMetric(
            name=r.name,
            estimates_count=r.estimates_count,
            total_amount=r.total_amount,
        )
        for r in resp_rows
    ]

    # top-10 услуг глобально
    q_srv = (
        select(
            EstimateItem.name.label("name"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("total_amount"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(EstimateItem.name)
        .order_by(desc("total_amount"))
        .limit(10)
    )
    srv_rows = (await db.execute(q_srv)).all()
    top_services = [
        ServiceMetric(name=r.name, total_amount=r.total_amount) for r in srv_rows
    ]

    subq = (
        select(
            Estimate.id.label("estimate_id"),
            func.coalesce(func.sum(revenue_expr), 0.0).label("estimate_total"),
        )
        .select_from(Estimate)
        .join(Estimate.items)
        .where(*filters, *revenue_filters)
        .group_by(Estimate.id)
        .subquery()
    )

    median_expr = func.percentile_cont(0.5).within_group(subq.c.estimate_total.asc())

    q_median = select(median_expr).select_from(subq)
    median_res = (await db.execute(q_median)).scalar_one_or_none()
    median_amount = median_res or 0.0

    q_clients_count = (
        select(func.count(func.distinct(Estimate.client_id)))
        .select_from(Estimate)
        .where(*filters)
    )
    clients_count = (await db.execute(q_clients_count)).scalar_one()
    arpu = total_amount / clients_count if clients_count else 0

    return GlobalAnalytics(
        total_estimates=total_estimates,
        total_amount=total_amount,
        average_amount=average_amount,
        timeseries=timeseries,
        top_clients=top_clients,
        by_responsible=by_responsible,
        top_services=top_services,
        granularity=granularity,
        arpu=arpu,
        median_amount=median_amount,
        mom_growth=mom,
        yoy_growth=yoy,
    )


@router.get("/export", summary="Экспорт глобальной аналитики в CSV или PDF")
async def export_analytics(
    format: Literal["csv", "pdf"] = Query(
        "csv", description="Формат экспорта: csv или pdf"
    ),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[List[EstimateStatus]] = Query(None),
    vat_enabled: Optional[bool] = Query(None),
    granularity: GranularityEnum = Query(GranularityEnum.month),
    categories: Optional[List[str]] = Query(None, description="Категории услуг"),
    db: AsyncSession = Depends(get_db),
):
    # 1) получаем те же данные, что и в /api/analytics/
    ga: GlobalAnalytics = await get_global_analytics(
        start_date=start_date,
        end_date=end_date,
        status=status,
        vat_enabled=vat_enabled,
        granularity=granularity,
        categories=categories,
        db=db,
    )

    # 2) CSV
    if format == "csv":

        def iter_csv():
            buf = io.StringIO()
            w = csv.writer(buf)

            # -- ключевые метрики --
            w.writerow(["Метрика", "Значение"])
            w.writerow(["Всего смет", ga.total_estimates])
            w.writerow(["Общая сумма", ga.total_amount])
            w.writerow(["Средняя сумма", ga.average_amount])
            w.writerow(["Медиана по сметам", ga.median_amount])
            w.writerow(["ARPU", ga.arpu])
            w.writerow(["MoM рост (%)", ga.mom_growth or 0])
            w.writerow(["YoY рост (%)", ga.yoy_growth or 0])
            w.writerow([])

            # -- динамика --
            w.writerow(["Период", "Сумма"])
            for row in ga.timeseries:
                w.writerow([row.period, row.value])
            w.writerow([])

            # -- топ-10 клиентов --
            w.writerow(["Top-10 клиентов", "Выручка"])
            for cli in ga.top_clients:
                w.writerow([cli.name, cli.total_amount])
            w.writerow([])

            # -- разбивка по ответственным --
            w.writerow(["Ответственный", "Число смет", "Выручка"])
            for resp in ga.by_responsible:
                w.writerow([resp.name, resp.estimates_count, resp.total_amount])
            w.writerow([])

            # -- топ-10 услуг --
            w.writerow(["Top-10 услуг", "Выручка"])
            for srv in ga.top_services:
                w.writerow([srv.name, srv.total_amount])

            buf.seek(0)
            yield buf.read()

        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="analytics.csv"'},
        )

    # 3) PDF через wkhtmltopdf
    html = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>table{border-collapse:collapse;}td,th{border:1px solid #333;padding:4px;}</style>",
        f"<title>Аналитика {granularity.value}</title></head><body>",
        f"<h1>Глобальная аналитика ({granularity.value})</h1>",
        "<h2>Ключевые метрики</h2><ul>",
        f"<li>Всего смет: {ga.total_estimates}</li>",
        f"<li>Общая сумма: {ga.total_amount}</li>",
        f"<li>Средняя сумма: {ga.average_amount}</li>",
        f"<li>Медиана: {ga.median_amount}</li>",
        f"<li>ARPU: {ga.arpu}</li>",
        f"<li>MoM рост: {ga.mom_growth or 0:.2f}%</li>",
        f"<li>YoY рост: {ga.yoy_growth or 0:.2f}%</li>",
        "</ul>",
        "<h2>Динамика по периодам</h2>",
        "<table><tr><th>Период</th><th>Сумма</th></tr>",
    ]
    for row in ga.timeseries:
        html.append(f"<tr><td>{row.period}</td><td>{row.value}</td></tr>")
    html.append("</table>")

    html.append("<h2>Top-10 клиентов</h2>")
    html.append("<table><tr><th>Клиент</th><th>Выручка</th></tr>")
    for cli in ga.top_clients:
        html.append(f"<tr><td>{cli.name}</td><td>{cli.total_amount}</td></tr>")
    html.append("</table>")

    html.append("<h2>По ответственным</h2>")
    html.append(
        "<table><tr><th>Ответственный</th><th>Число смет</th><th>Выручка</th></tr>"
    )
    for resp in ga.by_responsible:
        html.append(
            f"<tr><td>{resp.name}</td><td>{resp.estimates_count}</td><td>{resp.total_amount}</td></tr>"
        )
    html.append("</table>")

    html.append("<h2>Top-10 услуг</h2>")
    html.append("<table><tr><th>Услуга</th><th>Выручка</th></tr>")
    for srv in ga.top_services:
        html.append(f"<tr><td>{srv.name}</td><td>{srv.total_amount}</td></tr>")
    html.append("</table>")

    html.append("</body></html>")
    html_str = "\n".join(html)

    # wkhtmltopdf: HTML → PDF
    proc = subprocess.run(
        ["wkhtmltopdf", "--encoding", "utf-8", "-", "-"],
        input=html_str.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise HTTPException(
            500, detail=f"PDF generation failed: {proc.stderr.decode('utf-8')}"
        )

    return Response(
        content=proc.stdout,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="analytics.pdf"'},
    )
