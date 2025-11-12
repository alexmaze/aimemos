"""文件处理服务，用于提取不同格式文件的纯文本内容。"""

import os
from pathlib import Path
from typing import Optional


class FileHandler:
    """文件处理器，用于提取文本内容。"""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """从文件中提取纯文本内容。
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的纯文本内容
            
        Raises:
            ValueError: 不支持的文件格式
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.txt', '.md']:
            return FileHandler._extract_text_plain(file_path)
        elif file_ext in ['.doc', '.docx']:
            return FileHandler._extract_text_docx(file_path)
        elif file_ext == '.pdf':
            return FileHandler._extract_text_pdf(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    @staticmethod
    def _extract_text_plain(file_path: str) -> str:
        """提取纯文本或Markdown文件的内容。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gb2312') as f:
                return f.read()
    
    @staticmethod
    def _extract_text_docx(file_path: str) -> str:
        """提取Word文档的文本内容。"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs]
            return '\n'.join(paragraphs)
        except ImportError:
            raise ValueError("需要安装 python-docx 库来处理 Word 文档")
        except Exception as e:
            raise ValueError(f"处理 Word 文档时出错: {str(e)}")
    
    @staticmethod
    def _extract_text_pdf(file_path: str) -> str:
        """提取PDF文件的文本内容。"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text_parts.append(page.extract_text())
            
            return '\n'.join(text_parts)
        except ImportError:
            raise ValueError("需要安装 pypdf 库来处理 PDF 文件")
        except Exception as e:
            raise ValueError(f"处理 PDF 文件时出错: {str(e)}")
    
    @staticmethod
    def is_supported_format(filename: str) -> bool:
        """检查文件格式是否支持。"""
        ext = Path(filename).suffix.lower()
        return ext in ['.txt', '.md', '.doc', '.docx', '.pdf']
    
    @staticmethod
    def get_file_format(filename: str) -> str:
        """获取文件格式（扩展名，不含点）。"""
        return Path(filename).suffix.lower().lstrip('.')
