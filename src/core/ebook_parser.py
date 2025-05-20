import fitz
from pathlib import Path
from typing import Optional
from core.ocr_engine import OCRProcessor
from core.cache_manager import CacheManager
from utils.file_convert import convert_to_pdf
from utils.file_convert import convert_ebook

class EbookParser:
    def __init__(self):
        self.cache = CacheManager()
        self.ocr = OCRProcessor()
    
    def parse_range(self, file_path: str, 
                   start_page: int, end_page: Optional[int],
                   use_ocr: bool) -> str:
        ext = Path(file_path).suffix.lower()
        # 修正 strip 方法调用
        if ext.strip() not in ('.pdf', '.doc', '.docx', '.epub', '.mobi', '.chm', '.txt'):
            raise ValueError(f"不支持的格式：{ext}")
        original_ext = ext
        # 如果是word转换为PDF
        if ext in ('.doc', '.docx'):
            file_path = convert_to_pdf(file_path)
            if file_path is None:
                print("Word 文件转换失败，无法继续解析。")
                return ""
            ext = '.pdf'

        # 如果是chm或mobi转换为PDF
        if ext in ('.chm', '.mobi'):
            file_path = convert_ebook(file_path)
            if file_path is None:
                print("文件转换失败，无法继续解析。")
                return ""
            ext = '.pdf'

        total = self._get_total_pages(ext, file_path)
        end = end_page or total
        
        # 页码有效性校验
        if start_page < 1 or end > total or start_page > end:
            raise ValueError(f"无效的页码范围 (1-{total})")
        
        # 缓存检查
        cache_key = f"{file_path}-{start_page}-{end}"
        if cached := self.cache.get(cache_key):
            return cached
            
        # 分页解析
        content = []
        for p in range(start_page, end+1):
            page_content = self._parse_single(ext, file_path, p, use_ocr)
            content.append(f"=== Page {p}/{total} ===\n{page_content}")
        
        result = "\n".join(content)
        self.cache.set(cache_key, result)
        return result

    def _get_total_pages(self, ext: str, path: str) -> int:
        """获取总页数"""
        if ext == '.pdf':
            try:
                with fitz.open(path) as doc:
                    return doc.page_count
            except Exception as e:
                print(f"打开 PDF 文件 {path} 失败: {str(e)}")
                return 0
        elif ext == '.epub':
            with fitz.open(path) as doc:
                return doc.page_count
        elif ext == '.txt':
            with open(path, 'r') as f:
                return (len(f.readlines()) + 49) // 50
        else:
            raise ValueError(f"不支持的格式：{ext}")

    def _parse_single(self, ext: str, path: str, 
                     page: int, ocr: bool) -> str:
        """单页解析逻辑"""
        if ext == '.pdf':
            #print("1.-----------")
            #print(path)
            return self._parse_pdf_page(path, page, ocr)
        elif ext == '.epub':
            return self._parse_epub_page(path, page)
        elif ext == '.txt':
            return self._parse_txt_page(path, page)
        else:
            raise ValueError(f"不支持的格式：{ext}")
    
    def _needs_ocr(self, text: str) -> bool:
        """判断是否需要OCR"""
        if len(text.strip()) < 50:
            return True
        
        # 检测异常字符
        abnormal_chars = sum(1 for c in text if ord(c) > 0xff)
        return abnormal_chars / len(text) > 0.3

    def _parse_pdf_page(self, path: str, page: int, ocr: bool) -> str:
        try:
            with fitz.open(path) as doc:
                if doc.page_count == 0:
                    print(f"PDF 文件 {path} 为空")
                    return ""
                if page > doc.page_count:
                    print(f"请求的页码 {page} 超出文件总页数 {doc.page_count}")
                    return ""
                pg = doc[page - 1]
                if pg is None:
                    print(f"PDF 文件 {path} 的第 {page} 页获取失败")
                    return ""
                text = pg.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                print(pg)
                print(text)
                if ocr or self._needs_ocr(text):
                    try:
                        blocks = pg.get_text("blocks", flags=fitz.TEXT_PRESERVE_IMAGES)
                        for b in blocks:
                            if b[6] == 1:  # 图像块
                                clip = fitz.Rect(b[:4])
                                pix = pg.get_pixmap(
                                    matrix=fitz.Matrix(300/72, 300/72), 
                                    clip=clip,
                                    colorspace="rgb",
                                    alpha=False
                                )
                                ocr_text = self.ocr.process(pix)
                                text += ocr_text
                    except Exception as e:
                        print(f"OCR处理失败: {str(e)}")
                return text
        except Exception as e:
            print(f"解析 PDF 文件 {path} 失败: {str(e)}")
            return ""

    def _parse_epub_page(self, path: str, page: int) -> str:
        with fitz.open(path) as doc:
            return doc[page-1].get_text("text")

    def _parse_txt_page(self, path: str, page: int) -> str:
        with open(path, 'r') as f:
            lines = f.readlines()
            start = (page-1)*50
            end = min(page*50, len(lines))
            return ''.join(lines[start:end])

if __name__ == "__main__":
    parser = EbookParser()
    #file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\pdf_resources\\Foundation_of_LLMs.pdf"
    #file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\resources\\易经入门.docx"
    #file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\resources\\阅读的方法 - 罗振宇.epub"
    #file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\resources\\哈佛学子“无我”专注力.mobi"
    file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\resources\\通往奴役之路.chm"
    print(parser.parse_range(file_path, 1, 3, False))