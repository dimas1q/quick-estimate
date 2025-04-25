from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO
from app.models.estimate import Estimate
from collections import defaultdict


def generate_excel(estimate: Estimate) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = estimate.name[:31].replace(":", "-")

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
        ("Клиент", estimate.client_name),
        ("Компания клиента", estimate.client_company),
        ("Контакт", estimate.client_contact),
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

    for category, items in grouped.items():
        category_total = 0
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
                total,
            ]
            for col, val in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = border
                if col == 7:
                    cell.font = Font(bold=True)
                col_max_width[col - 1] = max(
                    col_max_width[col - 1], len(str(val)) if val else 0
                )
            row += 1
        ws.cell(row=row, column=6, value="Итог по категории").font = bold_font
        ws.cell(row=row, column=7, value=category_total).font = bold_font
        row += 2

    total = sum(item.quantity * item.unit_price for item in estimate.items)
    vat = total * 0.2 if estimate.vat_enabled else 0
    total_with_vat = total + vat

    ws[f"F{row}"] = "Общая сумма"
    ws[f"G{row}"] = total
    row += 1
    ws[f"F{row}"] = "НДС (20%)"
    ws[f"G{row}"] = vat
    row += 1
    ws[f"F{row}"] = "Итого с НДС"
    ws[f"G{row}"] = total_with_vat

    for r in range(row - 2, row + 1):
        ws[f"F{r}"].font = bold_font
        ws[f"G{r}"].font = bold_font

    # Автоподбор ширины столбцов
    for i, width in enumerate(col_max_width, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width + 2

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
