"""One-off script to generate sample policy PDF for RAG testing."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent / "fr8labs_freight_policy.pdf"

SECTIONS = [
    ("Fr8Labs Global Freight Forwarding", "title"),
    ("Standard Operating Policy & Customer Guidelines", "subtitle"),
    ("Document Ref: F8-POL-2025-001 | Version 3.2 | Effective: 1 January 2025", "meta"),
    ("1. PURPOSE AND SCOPE", "heading"),
    (
        "This policy defines standard terms, transit commitments, documentation "
        "requirements, and claims procedures for ocean, air, and multimodal shipments "
        "handled by Fr8Labs and its appointed agents. It applies to all quotations (QT), "
        "booking confirmations, and house bills of lading (HBL) unless superseded by a "
        "signed customer master service agreement.",
        "body",
    ),
    ("2. QUOTATION VALIDITY", "heading"),
    (
        "All spot quotations remain valid for fourteen (14) calendar days from issue. "
        "Rates assume general cargo and standard free time unless noted. Rate adjustments "
        "apply if cargo weight or volume varies by more than 10% from quoted figures. "
        "BAF, CAF, and PSS are pass-through charges and may apply at shipment time.",
        "body",
    ),
    ("3. STANDARD TRANSIT TIMES (INDICATIVE)", "heading"),
    (
        "Mumbai to Singapore (ocean): 14-16 days standard, 10-12 days express. "
        "Mumbai to Rotterdam (ocean): 28-32 days standard, 24-26 days express. "
        "Chennai to Dubai (ocean): 8-10 days standard. "
        "Shanghai to Los Angeles (ocean): 18-22 days standard. "
        "Delhi to Frankfurt (air): 3-5 days standard, 2-3 days express. "
        "Bangalore to Hong Kong (air): 2-4 days standard. "
        "Transit begins at cargo receipt at origin, not quotation date. "
        "Customs holds and vessel rollovers are excluded from commitments.",
        "body",
    ),
    ("4. DOCUMENTATION REQUIREMENTS", "heading"),
    (
        "Commercial Invoice: minimum 3 copies ocean, 2 air; must show HS code and Incoterm. "
        "Packing List: required for all shipments; weights within 2% tolerance of invoice. "
        "Certificate of Origin: mandatory for ASEAN-India FTA and EU GSP claims. "
        "Fumigation Certificate: required for wooden packaging on Australia/NZ lanes. "
        "Dangerous Goods Declaration: booking 72 hours before cut-off for DG cargo. "
        "LC shipments: draft BL approval 5 business days before ETD.",
        "body",
    ),
    ("5. LIABILITY AND INSURANCE", "heading"),
    (
        "Fr8Labs forwarder liability is limited to USD 2.00 per kg or goods value, "
        "whichever is lower, unless agreed otherwise in writing. "
        "All-risk cargo insurance available at 0.35% of invoice value plus freight "
        "(minimum USD 50 per shipment). Visible damage must be noted on delivery receipt. "
        "Concealed damage claims within 3 business days of delivery.",
        "body",
    ),
    ("6. FREE TIME AND DETENTION", "heading"),
    (
        "Import FCL: 7 days combined free time at destination unless carrier tariff differs. "
        "Import LCL: 5 days at CFS; then USD 18/CBM/day storage. "
        "Export: 5 days from empty container release; day 6 onward USD 45/20ft or USD 75/40ft per day. "
        "Fr8Labs notifies consignee at day 3 of remaining free time.",
        "body",
    ),
    ("7. PROHIBITED CARGO", "heading"),
    (
        "Not accepted without prior Compliance approval: explosives, standalone lithium batteries "
        "above IATA Section II limits, live animals, counterfeit goods, sanctioned-party cargo, "
        "and personal effects over USD 5,000 on commercial lanes.",
        "body",
    ),
    ("8. PAYMENT TERMS", "heading"),
    (
        "Credit customers: net 30 days. New customers: prepayment until credit approved. "
        "Disbursement invoices due within 7 days. Late payment fee: 1.5% per month.",
        "body",
    ),
    ("9. CLAIMS PROCEDURE", "heading"),
    (
        "Notify claims@fr8labs.co within 7 days of delivery. Submit form F8-CLM-01 with "
        "invoice, packing list, photos, and survey report if applicable. "
        "Acknowledgement within 2 business days with reference CLM-YYYY-NNNNN. "
        "Settlement target: 45 days from complete documentation. "
        "Maximum filing deadline: 9 months from delivery.",
        "body",
    ),
    ("10. CONTACTS", "heading"),
    (
        "Operations: ops@fr8labs.co | Documentation: docs@fr8labs.co | "
        "Claims: claims@fr8labs.co | Customer Success: customersuccess@fr8labs.co. "
        "Office hours: Mon-Fri 09:00-18:00 IST/GST.",
        "body",
    ),
]


def main() -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    for text, kind in SECTIONS:
        if kind == "title":
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 8, text)
            pdf.ln(2)
        elif kind == "subtitle":
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 7, text)
            pdf.ln(2)
        elif kind == "meta":
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 5, text)
            pdf.ln(4)
        elif kind == "heading":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, text)
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, text)
            pdf.ln(2)

    pdf.output(str(OUT))
    print(f"Created {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
