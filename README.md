# 多格式电子书解析服务

本项目是一个多格式电子书解析服务，支持解析包括 PDF、EPUB、Word、MOBI、TXT 和 CHM 在内的六种格式的电子书。同时，还支持使用 OCR 对扫描版 PDF 进行文字识别。

## 项目结构
```plaintext
.env.example
README.md
requirements.txt
src/
  core/
    __pycache__/
    cache_manager.py
    ebook_parser.py
    ocr_engine.py
  readbooks_server.py
  utils/
    __pycache__/
    file_convert.py
test/
  test_server.py