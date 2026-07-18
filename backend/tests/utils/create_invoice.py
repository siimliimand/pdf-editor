from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.units import inch

def create_invoice_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("INVOICE", styles['Title']))
    elements.append(Spacer(1, 12))

    # Header info
    header_data = [
        ["From:", "To:"],
        ["My Company Ltd", "Customer Name"],
        ["123 Business Rd", "456 Client St"],
        ["City, Country", "City, Country"],
        ["Phone: 555-0199", "Ref: #INV-001"]
    ]
    t = Table(header_data, colWidths=[3*inch, 3*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,0), colors.navy),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))

    # Items Table
    data = [['Description', 'Quantity', 'Unit Price', 'Total']]
    for i in range(1, 6):
        data.append([f"Item {i} Description here", str(i), f"${i * 10}.00", f"${i * i * 10}.00"])
    
    data.append(["", "", "Total:", "$550.00"])

    t = Table(data, colWidths=[3.5*inch, 0.75*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))

    # Footer Text with specific color
    p_style = ParagraphStyle('Footer', parent=styles['Normal'], textColor=colors.red)
    elements.append(Paragraph("Thank you for your business!", p_style))
    
    # A box (drawing)
    d = Drawing(100, 50)
    d.add(Rect(0, 0, 100, 50, fillColor=colors.lightblue))
    elements.append(d)

    doc.build(elements)
    print(f"Created {filename}")

if __name__ == "__main__":
    import os
    # Save to ../data/test_invoice.pdf relative to this script
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test_invoice.pdf")
    create_invoice_pdf(output_path)
