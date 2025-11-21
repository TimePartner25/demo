"""
工具函数模块
"""

from typing import List, Dict, Any
import json
import re


def safe_json_parse(text: str) -> Dict[str, Any]:
    """
    安全地解析JSON文本
    
    Args:
        text: 可能包含JSON的文本
        
    Returns:
        解析后的字典，如果失败返回空字典
    """
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取JSON部分
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            try:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    
    return {}


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """
    从文本中提取关键词（简单实现）
    
    Args:
        text: 输入文本
        min_length: 最小关键词长度
        
    Returns:
        关键词列表
    """
    # 移除标点符号
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # 分词并过滤
    words = text.split()
    keywords = [w for w in words if len(w) >= min_length]
    
    return keywords


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单的词汇重叠）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度分数 (0-1)
    """
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def format_list_to_text(items: List[str], prefix: str = "-") -> str:
    """
    将列表格式化为文本
    
    Args:
        items: 项目列表
        prefix: 前缀符号
        
    Returns:
        格式化后的文本
    """
    if not items:
        return ""
    
    return "\n".join([f"{prefix} {item}" for item in items])


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def deduplicate_list(items: List[str]) -> List[str]:
    """
    去重列表，保持顺序
    
    Args:
        items: 输入列表
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


def count_tokens_estimate(text: str) -> int:
    """
    估算文本的token数量（粗略估计）
    中文：1字约等于1.5-2个token
    英文：1词约等于1-1.3个token
    
    Args:
        text: 输入文本
        
    Returns:
        估算的token数
    """
    # 简单估算：中文字符 * 1.5 + 英文单词 * 1.2
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    return int(chinese_chars * 1.5 + english_words * 1.2)
