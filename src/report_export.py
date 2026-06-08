from io import BytesIO

import pandas as pd


def build_excel_report(metrics: pd.DataFrame, recommendations: pd.DataFrame) -> bytes:
    """Return an in-memory Excel workbook for download in Streamlit."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        recommendations.to_excel(writer, sheet_name="price_recommendations", index=False)
        metrics.to_excel(writer, sheet_name="daily_metrics", index=False)

        workbook = writer.book
        for sheet in workbook.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 40)

    return output.getvalue()
