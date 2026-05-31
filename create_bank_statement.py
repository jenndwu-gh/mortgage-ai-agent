from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def create_bank_statement(filename, name, account, transactions, monthly_income, monthly_debts, assets):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=16, fontName='Helvetica-Bold', spaceAfter=4)
    sub_style    = ParagraphStyle('sub',    fontSize=10, fontName='Helvetica',      spaceAfter=2, textColor=colors.grey)
    label_style  = ParagraphStyle('label',  fontSize=9,  fontName='Helvetica-Bold', spaceAfter=2)
    normal_style = ParagraphStyle('norm',   fontSize=9,  fontName='Helvetica',      spaceAfter=2)

    story.append(Paragraph("FIRST NATIONAL BANK", header_style))
    story.append(Paragraph("Account Statement — April 1, 2025 to April 30, 2025", sub_style))
    story.append(Spacer(1, 0.2*inch))

    # Account info table
    acct_data = [
        ["Account Holder:", name,        "Account Number:", account],
        ["Account Type:",  "Checking",   "Routing Number:", "021000021"],
        ["Statement Period:", "Apr 2025","Branch:",         "San Francisco, CA"],
    ]
    acct_table = Table(acct_data, colWidths=[1.4*inch, 2.2*inch, 1.4*inch, 2.2*inch])
    acct_table.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('BACKGROUND',(0,0), (-1,-1), colors.HexColor('#F7F7F7')),
        ('BOX',       (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('PADDING',   (0,0), (-1,-1), 6),
    ]))
    story.append(acct_table)
    story.append(Spacer(1, 0.2*inch))

    # Summary box
    story.append(Paragraph("Account Summary", label_style))
    summary_data = [
        ["Opening Balance:", f"${assets - monthly_income + monthly_debts:,.2f}"],
        ["Total Deposits:",  f"${monthly_income:,.2f}"],
        ["Total Withdrawals:", f"${monthly_debts:,.2f}"],
        ["Closing Balance:", f"${assets:,.2f}"],
    ]
    sum_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    sum_table.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('BACKGROUND',(0,-1),(-1,-1), colors.HexColor('#EAF4EA')),
        ('BOX',       (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('PADDING',   (0,0), (-1,-1), 5),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.2*inch))

    # Transactions
    story.append(Paragraph("Transaction History", label_style))
    tx_header = [["Date", "Description", "Debit ($)", "Credit ($)", "Balance ($)"]]
    tx_data   = tx_header + transactions
    tx_table  = Table(tx_data, colWidths=[0.8*inch, 3.2*inch, 1*inch, 1*inch, 1.2*inch])
    tx_table.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',  (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0), (-1,-1), 8.5),
        ('BACKGROUND',(0,0), (-1,0),  colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0),  colors.white),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('BOX',       (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('ALIGN',     (2,0), (-1,-1), 'RIGHT'),
        ('PADDING',   (0,0), (-1,-1), 5),
    ]))
    story.append(tx_table)
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("This statement is for informational purposes only. Please retain for your records.", sub_style))

    doc.build(story)
    print(f"Created: {filename}")

# ── Sarah Chen (A001) — passes pre-approval ──────────────────
sarah_tx = [
    ["04/01", "Opening Balance",              "",         "",        "37,300.00"],
    ["04/02", "ACH DIRECT DEPOSIT - PAYROLL", "",       "4,250.00", "41,550.00"],
    ["04/05", "MORTGAGE PAYMENT - WELLS FARGO","1,850.00","",        "39,700.00"],
    ["04/07", "CHASE AUTO LOAN PAYMENT",       "380.00", "",         "39,320.00"],
    ["04/10", "WHOLEFDS MARKET",               "215.40", "",         "39,104.60"],
    ["04/12", "NAVIENT STUDENT LOAN",           "420.00","",         "38,684.60"],
    ["04/15", "ATM WITHDRAWAL",                "200.00", "",         "38,484.60"],
    ["04/16", "ACH DIRECT DEPOSIT - PAYROLL",  "",      "4,250.00", "42,734.60"],
    ["04/18", "PG&E UTILITIES",                "185.00","",          "42,549.60"],
    ["04/20", "AMAZON PURCHASE",               "89.99", "",          "42,459.61"],
    ["04/22", "RESTAURANT - NOPA SF",          "124.50","",          "42,335.11"],
    ["04/25", "TRANSFER TO SAVINGS",         "2,000.00","",          "40,335.11"],
    ["04/28", "ATM WITHDRAWAL",               "300.00", "",          "40,035.11"],
    ["04/30", "BANK SERVICE FEE",              "35.00", "",          "40,000.00"],
]
create_bank_statement(
    "/mnt/user-data/outputs/bank_statement_A001.pdf",
    "Sarah Chen", "****4892", sarah_tx,
    monthly_income=8500, monthly_debts=2850, assets=40000
)

# ── Tom Rivera (A002) — fails pre-approval ───────────────────
tom_tx = [
    ["04/01", "Opening Balance",               "",        "",        "8,200.00"],
    ["04/02", "ACH DIRECT DEPOSIT - PAYROLL",  "",      "2,500.00", "10,700.00"],
    ["04/05", "RENT PAYMENT",                "1,400.00","",          "9,300.00"],
    ["04/07", "CAPITAL ONE CREDIT CARD",       "450.00","",          "8,850.00"],
    ["04/08", "SYNCHRONY BANK - FURNITURE",    "280.00","",          "8,570.00"],
    ["04/10", "WALMART",                        "98.40","",          "8,471.60"],
    ["04/12", "PAYDAY LOAN REPAYMENT",         "350.00","",          "8,121.60"],
    ["04/15", "ATM WITHDRAWAL",                "100.00","",          "8,021.60"],
    ["04/16", "ACH DIRECT DEPOSIT - PAYROLL",  "",      "2,500.00", "10,521.60"],
    ["04/18", "ELECTRIC BILL",                  "95.00","",         "10,426.60"],
    ["04/20", "OVERDRAFT FEE",                  "35.00","",         "10,391.60"],
    ["04/22", "AFFIRM BNPL PAYMENT",           "189.00","",         "10,202.60"],
    ["04/26", "CASH APP TRANSFER",             "250.00","",          "9,952.60"],
    ["04/30", "CLOSING BALANCE",                "",     "",          "9,952.60"],
]
create_bank_statement(
    "/mnt/user-data/outputs/bank_statement_A002.pdf",
    "Tom Rivera", "****2241", tom_tx,
    monthly_income=5000, monthly_debts=2850, assets=9952
)
