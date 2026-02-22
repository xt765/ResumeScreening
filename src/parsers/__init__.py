"""文档解析器模块。

提供 PDF、DOCX 等格式简历的解析功能，提取文本和图片内容。
"""

from src.parsers.document_parser import SUPPORTED_FORMATS, DocumentParser

__all__ = ["SUPPORTED_FORMATS", "DocumentParser"]
