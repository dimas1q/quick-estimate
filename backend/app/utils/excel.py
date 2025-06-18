## backend/app/utils/excel.py

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from app.models.estimate import Estimate
from collections import defaultdict

def generate_excel(estimate: Estimate) -> BytesIO:
    from openpyxl.styles import PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = estimate.name[:31].replace(":", "-")

    status_map = {
        "draft": "Черновик", "sent": "Отправлена", "approved": "Одобрена", "paid": "Оплачена", "cancelled": "Отменена"
    }
    currency_format = "₽#,##0.00"
    bold_font = Font(bold=True)
    title_font = Font(size=14, bold=True)
    header_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    total_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    cat_total_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)
    title_cell = ws.cell(row=1, column=1, value=estimate.name)
    title_cell.font = title_font
    title_cell.alignment = center_align

    fields = [
        ("Клиент", estimate.client.name),
        ("Компания клиента", estimate.client.company),
        ("Контакт", estimate.client.email),
        ("Статус", status_map.get(estimate.status.value, estimate.status.value)),
        ("Ответственный", estimate.responsible),
        ("НДС", f"Включён ({estimate.vat_rate}%)" if estimate.vat_enabled else "Не включён"),
        ("Дата создания", estimate.date.strftime("%d.%m.%Y %H:%M:%S")),
    ]
    if getattr(estimate, "notes", None):
        joined = "\n".join(f"{n.text} — {n.user.name} ({n.created_at.strftime('%d.%m.%Y %H:%M')})" for n in estimate.notes)
        fields.append(("Примечания", joined))

    row = 3
    for label, value in fields:
        ws[f"A{row}"] = label
        ws[f"B{row}"] = value
        ws[f"A{row}"].font = bold_font
        row += 1

    row += 1
    ws[f"A{row}"] = "Услуги"
    ws[f"A{row}"].font = Font(size=12, bold=True)
    row += 1

    headers = [
        "Категория", "Название", "Описание", "Кол-во", "Ед. изм.",
        "Внутр. цена", "Итог (вн.)", "Внеш. цена", "Итог (внеш.)"
    ]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border
        cell.fill = header_fill

    row += 1
    grouped = defaultdict(list)
    for item in estimate.items:
        grouped[item.category or "Без категории"].append(item)

    col_max_width = [len(h) for h in headers]
    def update_max(col, val):
        col_max_width[col] = max(col_max_width[col], len(str(val)) if val else 0)

    cat_blocks = []
    internal_service_rows = []
    external_service_rows = []

    for category, items in grouped.items():
        cat_start = row
        cat_internal_rows = []
        cat_external_rows = []

        for item in items:
            values = [
                category,
                item.name,
                item.description,
                item.quantity,
                item.unit,
                item.internal_price,
                None, # Итог (вн.)
                item.external_price,
                None, # Итог (внеш.)
            ]
            for col, val in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = border
                cell.alignment = center_align if col not in (2, 3) else Alignment(horizontal="left", vertical="center")
                if col == 6 or col == 8:
                    cell.number_format = currency_format
                if col == 7:
                    cell.value = f"=F{row}*D{row}"
                    cell.number_format = currency_format
                    cat_internal_rows.append(row)
                    internal_service_rows.append(row)
                if col == 9:
                    cell.value = f"=H{row}*D{row}"
                    cell.number_format = currency_format
                    cat_external_rows.append(row)
                    external_service_rows.append(row)
                update_max(col - 1, val)
            row += 1

        # Итоги по категории
        ws.cell(row=row, column=1, value=f"Итог по категории: {category}").font = bold_font
        ws.cell(row=row, column=1).fill = cat_total_fill
        ws.cell(row=row, column=6, value="Внутр.").font = bold_font
        ws.cell(row=row, column=7, value=f"=SUM(G{cat_internal_rows[0]}:G{cat_internal_rows[-1]})").font = bold_font
        ws.cell(row=row, column=7).number_format = currency_format
        ws.cell(row=row, column=7).fill = cat_total_fill
        ws.cell(row=row, column=8, value="Внешн.").font = bold_font
        ws.cell(row=row, column=9, value=f"=SUM(I{cat_external_rows[0]}:I{cat_external_rows[-1]})").font = bold_font
        ws.cell(row=row, column=9).number_format = currency_format
        ws.cell(row=row, column=9).fill = cat_total_fill
        row += 2

        # Отступ после категории
        row += 1

    # Финальные итоги
    row += 1
    ws[f"E{row}"] = "Итого по всем категориям:"
    ws[f"E{row}"].font = bold_font
    ws[f"E{row}"].fill = total_fill
    ws[f"F{row}"] = "Внутр."
    ws[f"G{row}"] = f"=SUM({','.join([f'G{r}' for r in internal_service_rows])})" if internal_service_rows else 0
    ws[f"G{row}"].number_format = currency_format
    ws[f"G{row}"].font = bold_font
    ws[f"G{row}"].fill = total_fill

    ws[f"H{row}"] = "Внешн."
    ws[f"I{row}"] = f"=SUM({','.join([f'I{r}' for r in external_service_rows])})" if external_service_rows else 0
    ws[f"I{row}"].number_format = currency_format
    ws[f"I{row}"].font = bold_font
    ws[f"I{row}"].fill = total_fill

    # Разница
    row += 1
    ws[f"E{row}"] = "Разница:"
    ws[f"E{row}"].font = bold_font
    ws[f"E{row}"].fill = total_fill
    ws[f"I{row}"] = f"=I{row-1}-G{row-1}"
    ws[f"I{row}"].number_format = currency_format
    ws[f"I{row}"].font = bold_font
    ws[f"I{row}"].fill = total_fill

    # НДС
    if estimate.vat_enabled:
        row += 1
        ws[f"E{row}"] = f"НДС ({estimate.vat_rate}%)"
        ws[f"E{row}"].font = bold_font
        ws[f"E{row}"].fill = total_fill
        ws[f"I{row}"] = f"=I{row-1}*{estimate.vat_rate/100}"
        ws[f"I{row}"].number_format = currency_format
        ws[f"I{row}"].font = bold_font
        ws[f"I{row}"].fill = total_fill

    # Итог с НДС
    row += 1
    ws[f"E{row}"] = "Итого с НДС"
    ws[f"E{row}"].font = bold_font
    ws[f"E{row}"].fill = total_fill
    if estimate.vat_enabled:
        ws[f"I{row}"] = f"=I{row-1}+I{row-2}"
    else:
        ws[f"I{row}"] = f"=I{row-1}"
    ws[f"I{row}"].number_format = currency_format
    ws[f"I{row}"].font = bold_font
    ws[f"I{row}"].fill = total_fill

    # Автоподбор ширины столбцов
    for i, width in enumerate(col_max_width, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width + 7

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
