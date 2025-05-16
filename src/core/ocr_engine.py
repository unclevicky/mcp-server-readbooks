import pytesseract
from PIL import Image, ImageEnhance
import io
import numpy as np
import os
import cv2
import re
from typing import Union

class OCRProcessor:
    def __init__(self):
        self._setup_tesseract()
        self.correction_rules = {
            r'ﬁ': 'fi', r'ﬂ': 'fl', r'\$分刀': '分析', 
            r'′`': "'", r'WS MEN': 'Wittgenstein'
        }

    def _setup_tesseract(self):
        """自动配置Tesseract路径"""
        default_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract'
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
        else:
            pytesseract.pytesseract.tesseract_cmd = 'tesseract'

    def process(self, image_input: Union[bytes, 'fitz.Pixmap', Image.Image]) -> str:
        """主处理流程"""
        try:
            # 输入标准化
            image = self._normalize_input(image_input)
            
            # 图像增强
            enhanced = self._enhance_image(image)
            
            # 动态语言选择
            lang = self._detect_language(enhanced)
            
            # OCR执行
            text = self._run_ocr(enhanced, lang)
            
            # 后处理
            return self._postprocess(text)
            
        except Exception as e:
            raise RuntimeError(f"OCR处理失败: {str(e)}")

    def _normalize_input(self, input_data):
        """输入标准化"""
        if isinstance(input_data, bytes):
            return Image.open(io.BytesIO(input_data))
        elif hasattr(input_data, 'samples'):  # fitz.Pixmap
            return Image.frombytes('RGB', 
                                 (input_data.width, input_data.height),
                                 input_data.samples)
        elif isinstance(input_data, Image.Image):
            return input_data
        else:
            raise ValueError("不支持的输入类型")

    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """六步图像增强"""
        # 转换为OpenCV格式
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 1. 自适应阈值
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 10
        )
        
        # 2. 噪声去除
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 3. 锐化
        sharpen = cv2.filter2D(cleaned, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
        
        # 4. 对比度增强
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        limg = cv2.merge([clahe.apply(l), a, b])
        
        # 转换回PIL
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        return Image.fromarray(final)

    # 在_detect_language方法中增加
    def _detect_language(self, image: Image.Image) -> str:
        sample = pytesseract.image_to_string(image, lang='chi_sim+eng')[:100]
        chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', sample)) / len(sample) if sample else 0
        return 'chi_sim+eng' if chinese_ratio > 0.3 else 'eng+chi_sim'

    def _run_ocr(self, image: Image.Image, lang: str) -> str:
        """执行OCR核心"""
        config = (
            '--psm 6 --oem 1 '
            '-c preserve_interword_spaces=1 '
            '-c tessedit_char_blacklist=|\\`~'
        )
        return pytesseract.image_to_string(
            image, 
            lang=lang,
            config=config,
            timeout=30
        )

    def _postprocess(self, text: str) -> str:
        """五步文本净化"""
        # 1. 应用校正规则
        for pattern, replacement in self.correction_rules.items():
            text = re.sub(pattern, replacement, text)
        
        # 2. 合并断行
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # 3. 去除孤行字符
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
        
        # 4. 段落重组
        cleaned = []
        for line in lines:
            if cleaned and not line[0].isupper() and len(cleaned[-1]) < 60:
                cleaned[-1] += ' ' + line
            else:
                cleaned.append(line)
                
        # 5. 统一引号
        return '\n'.join(cleaned).replace('“', '"').replace('”', '"')