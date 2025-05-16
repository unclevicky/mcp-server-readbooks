from docx2pdf import convert
import os

def convert_to_pdf(doc_path: str) -> str:
    """Word转PDF实现"""
    pdf_path = f"{os.path.splitext(doc_path)[0]}.pdf"
    convert(doc_path, pdf_path)
    return pdf_path