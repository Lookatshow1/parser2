"""
Mock PDF Invoice Generator

Creates simple text-based "invoices" for demo purposes.
In production, use a library like ReportLab or weasyprint.
"""
import os
from datetime import datetime

def generate_mock_invoice(
    organization_name: str,
    invoice_number: str,
    amount: float,
    currency: str = "RUB"
) -> str:
    """
    Generate a simple mock invoice text file.
    Returns the file path.
    """
    timestamp = datetime.utcnow()
    
    content = f"""
================================================================================
                              INVOICE / СЧЁТ
================================================================================

Invoice Number / Номер счёта:   {invoice_number}
Date / Дата:                    {timestamp.strftime('%d.%m.%Y')}
Due Date / Срок оплаты:         {timestamp.strftime('%d.%m.%Y')}

--------------------------------------------------------------------------------
FROM / ОТ:
  AdTech Platform LLC
  123 Demo Street
  Moscow, Russia

TO / КОМУ:
  {organization_name}

--------------------------------------------------------------------------------
DESCRIPTION / ОПИСАНИЕ                                              AMOUNT
--------------------------------------------------------------------------------
  Advertising Services Prepayment                    {currency} {amount:,.2f}
  Предоплата рекламных услуг

--------------------------------------------------------------------------------
                                              TOTAL / ИТОГО:  {currency} {amount:,.2f}
================================================================================

Payment Instructions / Инструкции по оплате:
  This is a mock invoice for demo purposes.
  В реальной системе здесь будут реквизиты для оплаты.

Thank you for your business!
Спасибо за сотрудничество!

================================================================================
"""
    
    # Save to temp directory
    invoices_dir = "/tmp/invoices"
    os.makedirs(invoices_dir, exist_ok=True)
    
    filename = f"{invoice_number}.txt"
    filepath = os.path.join(invoices_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath


def generate_invoice_html(
    organization_name: str,
    invoice_number: str,
    amount: float,
    currency: str = "RUB"
) -> str:
    """
    Generate HTML invoice content that can be converted to PDF.
    """
    timestamp = datetime.utcnow()
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice {invoice_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .total {{ font-size: 24px; font-weight: bold; text-align: right; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>INVOICE / СЧЁТ</h1>
        <p>№ {invoice_number} от {timestamp.strftime('%d.%m.%Y')}</p>
    </div>
    
    <div class="section">
        <h3>Получатель / Recipient:</h3>
        <p>{organization_name}</p>
    </div>
    
    <table>
        <thead>
            <tr><th>Описание / Description</th><th>Сумма / Amount</th></tr>
        </thead>
        <tbody>
            <tr>
                <td>Предоплата рекламных услуг<br/>Advertising Services Prepayment</td>
                <td>{currency} {amount:,.2f}</td>
            </tr>
        </tbody>
    </table>
    
    <div class="total">
        ИТОГО / TOTAL: {currency} {amount:,.2f}
    </div>
    
    <div class="section" style="margin-top: 50px; font-size: 12px; color: #666;">
        <p>This is a mock invoice for demonstration purposes.</p>
        <p>Это демонстрационный счёт для тестирования.</p>
    </div>
</body>
</html>
"""
