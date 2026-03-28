"""
Dateiparser-Tool
Unterstützt Textextraktion aus PDF-, Markdown- und TXT-Dateien
"""

import os
from pathlib import Path
from typing import List, Optional


def _read_text_with_fallback(file_path: str) -> str:
    """
    Textdatei lesen, bei UTF-8-Fehler automatisch Kodierung erkennen.
    
    Verwendet eine mehrstufige Fallback-Strategie:
    1. Zuerst UTF-8-Dekodierung versuchen
    2. Mit charset_normalizer Kodierung erkennen
    3. Auf chardet als Fallback zurückgreifen
    4. Abschließend UTF-8 + errors='replace' als Sicherheitsnetz
    
    Args:
        file_path: Dateipfad
        
    Returns:
        Dekodierter Textinhalt
    """
    data = Path(file_path).read_bytes()
    
    # 首先尝试 UTF-8
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # 尝试使用 charset_normalizer 检测编码
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass
    
    # 回退到 chardet
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass
    
    # 最终兜底：使用 UTF-8 + replace
    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """文件解析器"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Text aus Datei extrahieren
        
        Args:
            file_path: Dateipfad
            
        Returns:
            Extrahierter Textinhalt
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Datei existiert nicht: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Nicht unterstütztes Dateiformat: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        
        raise ValueError(f"无法处理的文件格式: {suffix}")
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Text aus PDF extrahieren"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("需要安装PyMuPDF: pip install PyMuPDF")
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """Text aus Markdown extrahieren, unterstützt automatische Kodierungserkennung"""
        return _read_text_with_fallback(file_path)
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Text aus TXT extrahieren, unterstützt automatische Kodierungserkennung"""
        return _read_text_with_fallback(file_path)
    
    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        Text aus mehreren Dateien extrahieren und zusammenführen
        
        Args:
            file_paths: Liste der Dateipfade
            
        Returns:
            Zusammengeführter Text
        """
        all_texts = []
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== Dokument {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== Dokument {i}: {file_path} (Extraktion fehlgeschlagen: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 50
) -> List[str]:
    """
    Text in kleine Blöcke aufteilen
    
    Args:
        text: Originaltext
        chunk_size: Zeichenanzahl pro Block
        overlap: Überlappende Zeichenanzahl
        
    Returns:
        Liste der Textblöcke
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Versuchen, an Satzgrenzen aufzuteilen
        if end < len(text):
            # Nach dem nächsten Satzendezeichen suchen
            for sep in ['。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Nächster Block beginnt an der Überlappungsposition
        start = end - overlap if end < len(text) else len(text)
    
    return chunks

