import argparse
import os
import sys
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
from core.ebook_parser import EbookParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
load_dotenv()

class EbookService:
    def __init__(self):
        self.ebook_parser = EbookParser()
        self.mcp = FastMCP(
            "EbookReader",
            dependencies=["pymupdf", "python-docx", "pychm", "mobi"],
            instructions="多格式电子书解析服务",
            encoding='utf-8'
        )
        self._register_tools()

    def _register_tools(self):
        """完整工具注解实现"""
        @self.mcp.tool(
            name="parse_ebook",
            annotations={
                "title": "电子书解析工具",
                "readOnlyHint": True,
                "destructiveHint": False
            }
        )
        async def parse_ebook(
            file_path: Annotated[str, Field(description="电子书文件路径", max_length=255)],
            start_page: Annotated[int, Field(description="起始页码", ge=1)],
            end_page: Annotated[int, Field(description="结束页码", ge=1)],
            use_ocr: Annotated[bool, Field(description="是否启用OCR识别")] = False
        ) -> str:
            """
            解析6种格式电子书（PDF/EPUB/Word/MOBI/TXT/CHM）
            
            参数:
                file_path: 电子书文件绝对路径
                start_page: 起始页码(从1开始)
                end_page: 结束页码
                use_ocr: 是否对扫描版PDF启用OCR
            
            返回:
                解析后的文本内容
            """
            try:
                logging.info(f"开始解析电子书，文件路径: {file_path}，起始页码: {start_page}，结束页码: {end_page}，是否使用OCR: {use_ocr}")
                # 调用 EbookParser 的 parse_range 方法
                result = self.ebook_parser.parse_range(file_path, start_page, end_page, use_ocr)
                logging.info(f"电子书解析完成，文件路径: {file_path}")
                return result
            except Exception as e:
                logging.error(f"解析电子书失败，文件路径: {file_path}，错误信息: {str(e)}", exc_info=True)
                raise ValueError(f"解析电子书失败: {str(e)}")   

    def run(self, transport="stdio", port=8000):
        """启动MCP服务"""
        if transport == "stdio":
            logging.info(f"Starting MCP service in stdio mode on port {port}")
            self.mcp.run(transport=transport)
        else:
            logging.info(f"Starting MCP service in {transport} mode on port {port}")
            self.mcp.run(transport=transport, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sse", "stdio"], default=os.getenv("TRANSPORT_MODE"))
    parser.add_argument("--port", type=int, default=os.getenv("SSE_PORT", 8000))
    args = parser.parse_args()
    EbookService().run(transport=args.mode, port=args.port)