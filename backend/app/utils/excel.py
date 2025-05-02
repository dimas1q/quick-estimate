from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from app.models.estimate import Estimate
from collections import defaultdict


def generate_excel(estimate: Estimate) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = estimate.name[:31].replace(":", "-")

    currency_format = "₽#,##0.00"

    bold_font = Font(bold=True)
    title_font = Font(size=14, bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Заголовок сметы
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
    title_cell = ws.cell(row=1, column=1, value=estimate.name)
    title_cell.font = title_font
    title_cell.alignment = center_align

    # Основные поля
    fields = [
        ("Клиент", estimate.client.name),
        ("Компания клиента", estimate.client.company),
        ("Контакт", estimate.client.email),
        ("Ответственный", estimate.responsible),
        ("Заметки", estimate.notes),
        ("Дата создания", estimate.date.strftime("%d.%m.%Y %H:%M:%S")),
        ("НДС", "Включён (20%)" if estimate.vat_enabled else "Не включён"),
    ]

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
        "Категория",
        "Название",
        "Описание",
        "Кол-во",
        "Ед. изм.",
        "Цена",
        "Итог",
    ]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border

    row += 1
    grouped = defaultdict(list)
    for item in estimate.items:
        grouped[item.category or "Без категории"].append(item)

    col_max_width = [len(h) for h in headers]

    def update_max(col, val):
        col_max_width[col] = max(col_max_width[col], len(str(val)) if val else 0)

    service_rows = []

    for category, items in grouped.items():

        category_total = 0
        category_start = row
        for item in items:

            total = item.quantity * item.unit_price
            category_total += total
            values = [
                category,
                item.name,
                item.description,
                item.quantity,
                item.unit,
                item.unit_price,
                None,
            ]
            for col, val in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = border
                if col == 6:
                    cell.number_format = currency_format
                if col == 7:
                    cell.value = f"=F{row}*D{row}"
                    cell.number_format = currency_format
                update_max(col - 1, val)

            row += 1
            service_rows.append(row - 1)

        ws.cell(row=row, column=6, value="Итог по категории").font = bold_font
        sum_formula = f"=SUM(G{category_start}:G{row - 1})"
        ws.cell(row=row, column=7, value=sum_formula).font = bold_font
        ws.cell(row=row, column=7).number_format = currency_format
        row += 2

    total = sum(item.quantity * item.unit_price for item in estimate.items)
    vat = total * 0.2 if estimate.vat_enabled else 0
    total_with_vat = total + vat

    if service_rows:
        sum_parts = ",".join([f"G{r}" for r in service_rows])
        ws[f"F{row}"] = "Общая сумма"
        ws[f"G{row}"] = f"=SUM({sum_parts})"
        ws[f"G{row}"].number_format = currency_format
    else:
        ws[f"F{row}"] = "Общая сумма"
        ws[f"G{row}"] = 0
        ws[f"G{row}"].number_format = currency_format

    ws[f"F{row + 1}"] = "НДС (20%)"
    ws[f"G{row + 1}"] = f"=G{row}*0.2"
    ws[f"G{row + 1}"].number_format = currency_format

    ws[f"F{row + 2}"] = "Итого с НДС"
    ws[f"G{row + 2}"] = f"=G{row}+G{row + 1}"
    ws[f"G{row + 2}"].number_format = currency_format

    for r in range(row - 2, row + 3):
        ws[f"F{r}"].font = bold_font
        ws[f"G{r}"].font = bold_font

    update_max(0, label)
    update_max(1, value)
    update_max(5, "Итого с НДС")
    update_max(6, total_with_vat)

    # Автоподбор ширины столбцов
    for i, width in enumerate(col_max_width, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width + 5

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
