import fitz
import mobi
import docx
from pathlib import Path
from typing import Optional
from core.ocr_engine import OCRProcessor
from core.cache_manager import CacheManager
from utils.file_convert import convert_to_pdf

class EbookParser:
    def __init__(self):
        self.cache = CacheManager()
        self.ocr = OCRProcessor()
    
    def parse_range(self, file_path: str, 
                   start_page: int, end_page: Optional[int],
                   use_ocr: bool) -> str:
        ext = Path(file_path).suffix.lower()
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
            with fitz.open(path) as doc:
                return doc.page_count
        elif ext in ('.doc', '.docx'):
            doc = docx.Document(path)
            return len(doc.paragraphs) // 50 + 1
        elif ext == '.epub':
            with fitz.open(path) as doc:
                return doc.page_count
        elif ext == '.mobi':
            with mobi.open(path) as mobi_file:
                return len(mobi_file.read().split('\x0c'))
        elif ext == '.chm':
            chm_file = chm.CHMFile()
            chm_file.LoadCHM(path)
            return chm_file.GetTopicsCount()
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
        elif ext in ('.doc', '.docx'):
            return self._parse_word_page(path, page)
        elif ext == '.epub':
            return self._parse_epub_page(path, page)
        elif ext == '.mobi':
            return self._parse_mobi_page(path, page)
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
        #print("2.-----------")
        #print(path)
        with fitz.open(path) as doc:
            pg = doc[page-1]
            text = pg.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            print(pg)
            print(text)
            # 两种方式 如果没有特殊处理 直接使用fitz内置的ocr功能
            # 如果需要更高的识别精度 可以使用ocr引擎
            #if ocr or len(text.strip()) < 50:
            if ocr or self._needs_ocr(text):
                try:
                    # 分区块处理
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

    def _parse_word_page(self, path: str, page: int) -> str:
        pdf_path = convert_to_pdf(path)
        return self._parse_pdf_page(pdf_path, page, False)

    def _parse_epub_page(self, path: str, page: int) -> str:
        with fitz.open(path) as doc:
            return doc[page-1].get_text("text")

    def _parse_mobi_page(self, path: str, page: int) -> str:
        with mobi.open(path) as mobi_file:
            return mobi_file.read().split('\x0c')[page-1]

    def _parse_txt_page(self, path: str, page: int) -> str:
        with open(path, 'r') as f:
            lines = f.readlines()
            start = (page-1)*50
            end = min(page*50, len(lines))
            return ''.join(lines[start:end])

if __name__ == "__main__":
    parser = EbookParser()
    pdf_file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\pdf_resources\\Foundation_of_LLMs.pdf"
    print(parser.parse_range(pdf_file_path, 1, 3, False))