"""测试MCP服务的客户端脚本"""

import asyncio
import json
import os  # 新增：导入os模块用于获取环境变量
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# 获取当前PYTHONPATH（若不存在则为空字符串）
current_pythonpath = os.environ.get("PYTHONPATH", "")
# 拼接新的PYTHONPATH（原路径 + 项目src目录）
new_pythonpath = f"{current_pythonpath};d:/09.coding/ai/aicoding/MCP/Server/mcp-server-readbooks/src"

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="E:\\soft/tools\\anaconda3\\envs\\llm_learn\\python",  # Executable
    args=["D:\\09.coding\\ai\\aicoding\\MCP\\Server\\mcp-server-readbooks/src/readbooks_server.py"],  # Optional command line arguments
    env={
        "PYTHONPATH": new_pythonpath,  # 使用动态拼接的路径
        "TRANSPORT_MODE": "stdio",  # 确保使用stdio传输模式
        "PYTHONIOENCODING": "utf-8"  # 确保使用UTF-8编码
        #"SSE_PORT": "8000"  # 确保端口正确
    },  # Optional environment variables
)

async def test_readbooks_service():
    """测试fetch服务功能"""
    print("开始测试MCP服务...")
    
    # 创建MCP客户端
    async with stdio_client(server_params) as (read, write):
        print("已创建stdio客户端，获取read/write流")  # 添加调试日志
        async with ClientSession(read, write) as session:
            print("已创建ClientSession，开始初始化连接")  # 添加调试日志
            # Initialize the connection
            await session.initialize()
            print("连接初始化完成")  # 添加调试日志
    
            # 测试pdf
            pdf_file_path = "D:\\09.coding\\ai\\aicoding\\MCP\\Client\\books2llm\\pdf_resources\\Foundation_of_LLMs.pdf"  # 替换为实际的PDF文件路径
            start_page = 1  # 替换为实际的页码
            end_page = 3  # 替换为实际的页码
            use_ocr = False  # 替换为实际的OCR使用情况

            # 检查文件是否存在
            if not os.path.exists(pdf_file_path):
                print(f"错误: 文件 {pdf_file_path} 不存在")
                return False

            print("开始测试pdf...")
            
            try:
                # List available tools（获取包含工具列表的结果对象）
                tools_result = await session.list_tools()
                tools = tools_result.tools  # 从结果对象中提取工具列表
                
                for tool in tools:  # 遍历实际的工具列表
                    print(f"工具名称: {tool.name}")
                    print(f"工具描述: {tool.description}")
                    # 修复：inputSchema 是字典，直接使用 json.dumps 处理
                    print(f"参数: {json.dumps(tool.inputSchema, indent=2)}")  # 移除 .dict() 调用
                    print("-" * 40)  # 分隔线

                print("工具调用测试开始:")  # 打印工具调用结果
                try:
                    print(f"准备调用工具，参数: 文件路径 {pdf_file_path}，起始页码 {start_page}，结束页码 {end_page}，是否使用OCR {use_ocr}")
                    # 调用工具（假设工具名称为 parse_ebook）    
                    response = await session.call_tool(
                        "parse_ebook",  # 替换为实际的工具名称
                        {
                            "file_path": pdf_file_path,  # 替换为实际的文件路径
                            "start_page": start_page,  # 替换为实际的页码
                            "end_page": end_page,  # 替换为实际的页码   
                            "use_ocr": use_ocr  # 替换为实际的OCR使用情况
                        }   
                    )
                    print("工具调用结果:")  # 打印工具调用结果
                    print(response)  # 打印工具调用结果

                    # 检查是否为错误响应
                    if response.isError:
                        error_message = response.content[0].text if response.content else "未知错误"
                        print(f"\n获取失败! 错误信息: {error_message}")
                        return False  # 提前终止测试
                    
                    # 成功响应解析：content 是 TextContent 列表，text 字段为 JSON 格式的 Markdown 内容
                    if response.content:
                        # 提取第一个内容块的 text 字段（假设是 JSON 字符串）
                        content_text = response.content[0].text
                        print(content_text)  # 打印工具调用结果   
                    
                    print("\n测试完成!")
                    return True
                except Exception as e:
                    print(f"调用 'parse_ebook' 工具时发生异常: {str(e)}")
                    import traceback
                    traceback.print_exc()  # 打印完整的异常堆栈信息
                    return False
            except Exception as e:
                print(f"测试失败: {str(e)}")
                return False

if __name__ == "__main__":
    asyncio.run(test_readbooks_service())