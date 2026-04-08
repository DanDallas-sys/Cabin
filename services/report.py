import os
import pandas as pd
from sqlalchemy.orm import Session
from models import Transaction


def generate_report(db: Session, user_id: int) -> str:
    """
    Generate an Excel report for a user.
    Returns the absolute file path.
    """
    transactions = (
        db.query(Transaction)
        .filter_by(user_id=user_id)
        .order_by(Transaction.date.desc())
        .all()
    )

    data = []
    for tx in transactions:
        data.append({
            "Date": tx.date.strftime("%Y-%m-%d %H:%M") if tx.date else "",
            "Amount (₦)": tx.amount,
            "Type": tx.type.value if tx.type else "",
            "Category": tx.category or "—",
            "Description": tx.cleaned_narration or tx.narration or "—",
            "Status": tx.status.value if tx.status else "",
            "Confidence": f"{tx.confidence:.0%}" if tx.confidence else "—",
            "Reference": tx.reference,
        })

    df = pd.DataFrame(data)

    # Ensure reports directory exists
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    file_path = os.path.join(reports_dir, f"report_user_{user_id}.xlsx")

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

        # Auto-size columns
        worksheet = writer.sheets["Transactions"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    return file_path
