from docx2pdf import convert

def convert_to_pdf(doc_path):
    try:
        # 假设保存路径为原文件路径加上 .pdf 扩展名
        pdf_path = doc_path.rsplit('.', 1)[0] + '.pdf'
        convert(doc_path, pdf_path)
        return pdf_path
    except Exception as e:
        print(f"文件转换失败: {str(e)}")
        return None
