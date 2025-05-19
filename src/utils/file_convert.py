from docx2pdf import convert
import subprocess
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

def convert_to_pdf(doc_path):
    try:
        pdf_path = doc_path.rsplit('.', 1)[0] + '.pdf'
        if os.path.exists(pdf_path):
            print(f"PDF文件已存在: {pdf_path}")
            return pdf_path

        convert(doc_path, pdf_path) 
        return pdf_path
    except Exception as e:
        print(f"Word转换失败: {str(e)}")
        return None

def convert_ebook(ebook_path, output_format='pdf'):
    """
    使用Calibre转换CHM/MOBI到PDF/EPUB
    参数:
        ebook_path: 输入文件路径
        output_format: 输出格式 (pdf/epub)
    返回:
        转换后的文件路径或None
    """
    if output_format.lower() not in ['pdf', 'epub']:
        print("输出格式必须是'pdf'或'epub'")
        return None

    ext = ebook_path.rsplit('.', 1)[-1].lower() if '.' in ebook_path else ''
    if ext not in ['chm', 'mobi']:
        print("仅支持CHM或MOBI格式输入")
        return None

    output_path = ebook_path.rsplit('.', 1)[0] + f'.{output_format.lower()}'
    if os.path.exists(output_path):
        print(f"输出文件已存在: {output_path}")
        return output_path

    # 从 .env 文件中获取 ebook-convert 路径
    ebook_convert_path = os.getenv('EBOOK_CONVERT_PATH')
    if not ebook_convert_path:
        print("未在 .env 文件中找到 EBOOK_CONVERT_PATH，请检查。")
        return None

    try:
        args = [ebook_convert_path, ebook_path, output_path]
        if output_format == 'pdf':
            args.append('--pdf-add-toc')  # 添加PDF目录书签
        subprocess.run(args, check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', 'ignore') if e.stderr else ''
        print(f"转换失败: {err_msg}")
    except FileNotFoundError:
        print(f"未找到指定的 ebook-convert 路径: {ebook_convert_path}，请检查 .env 文件。")
    except Exception as e:
        print(f"未知错误: {str(e)}")
    return None