"""
知识库数据模型 - 存储事实性信息
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


@dataclass
class Fact:
    """单个事实条目"""
    content: str  # 事实内容
    category: Optional[str] = None  # 事实分类（如：工作、爱好、家庭等）
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_qa_index: Optional[int] = None  # 来源对话索引
    

class KnowledgeBase:
    """事实知识库"""
    
    def __init__(self):
        self.facts: List[Fact] = []
        
    def add_fact(self, content: str, category: Optional[str] = None, 
                 source_qa_index: Optional[int] = None):
        """添加单个事实"""
        fact = Fact(
            content=content,
            category=category,
            source_qa_index=source_qa_index
        )
        self.facts.append(fact)
        
    def add_facts(self, facts: List[Dict]):
        """批量添加事实"""
        for fact_data in facts:
            if isinstance(fact_data, dict):
                self.add_fact(
                    content=fact_data.get("content", ""),
                    category=fact_data.get("category"),
                    source_qa_index=fact_data.get("source_qa_index")
                )
            elif isinstance(fact_data, str):
                self.add_fact(content=fact_data)
                
    def get_facts_by_category(self, category: str) -> List[Fact]:
        """按分类检索事实"""
        return [f for f in self.facts if f.category == category]
    
    def get_all_facts(self) -> List[Fact]:
        """获取所有事实"""
        return self.facts
    
    def search_facts(self, keyword: str) -> List[Fact]:
        """简单的关键词搜索"""
        return [f for f in self.facts if keyword.lower() in f.content.lower()]
    
    def to_dict(self) -> Dict:
        """转换为字典格式以便序列化"""
        return {
            "facts": [asdict(fact) for fact in self.facts]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeBase":
        """从字典加载"""
        kb = cls()
        for fact_data in data.get("facts", []):
            kb.facts.append(Fact(**fact_data))
        return kb
    
    def __len__(self):
        return len(self.facts)
    
    def __repr__(self):
        return f"KnowledgeBase(facts={len(self.facts)})"
