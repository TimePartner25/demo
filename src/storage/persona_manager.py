"""
人物知识库管理器 - 负责本地持久化
"""

import os
import json
from typing import Optional, List, Dict
from pathlib import Path

from ..models import KnowledgeBase, StyleBase, OralHabitsBase


class PersonaManager:
    """人物知识库管理器"""
    
    def __init__(self, base_dir: str = "./personas"):
        """
        Args:
            base_dir: 人物数据存储根目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def list_personas(self) -> List[str]:
        """列出所有已存在的人物"""
        personas = []
        if self.base_dir.exists():
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    personas.append(item.name)
        return sorted(personas)
    
    def persona_exists(self, persona_name: str) -> bool:
        """检查人物是否存在"""
        persona_dir = self.base_dir / persona_name
        return persona_dir.exists()
    
    def load_persona(self, persona_name: str) -> Optional[Dict]:
        """
        加载人物的所有知识库
        
        Returns:
            包含所有知识库和历史的字典，如果不存在则返回None
        """
        persona_dir = self.base_dir / persona_name
        
        if not persona_dir.exists():
            return None
        
        data = {
            "name": persona_name,
            "knowledge_base": None,
            "style_base": None,
            "oral_habits_base": None,
            "history": []
        }
        
        # 加载事实知识库
        facts_file = persona_dir / "facts.json"
        if facts_file.exists():
            with open(facts_file, 'r', encoding='utf-8') as f:
                facts_data = json.load(f)
                data["knowledge_base"] = KnowledgeBase.from_dict(facts_data)
        else:
            data["knowledge_base"] = KnowledgeBase()
        
        # 加载风格库
        style_file = persona_dir / "style.json"
        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                style_data = json.load(f)
                data["style_base"] = StyleBase.from_dict(style_data)
        else:
            data["style_base"] = StyleBase()
        
        # 加载口头习惯库
        habits_file = persona_dir / "habits.json"
        if habits_file.exists():
            with open(habits_file, 'r', encoding='utf-8') as f:
                habits_data = json.load(f)
                data["oral_habits_base"] = OralHabitsBase.from_dict(habits_data)
        else:
            data["oral_habits_base"] = OralHabitsBase()
        
        # 加载历史记录
        history_file = persona_dir / "history.txt"
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                data["history"] = [line.strip() for line in f if line.strip()]
        
        return data
    
    def save_persona(
        self,
        persona_name: str,
        knowledge_base: KnowledgeBase,
        style_base: StyleBase,
        oral_habits_base: OralHabitsBase,
        history: List[str]
    ) -> bool:
        """
        保存人物的所有知识库
        
        Returns:
            保存是否成功
        """
        try:
            persona_dir = self.base_dir / persona_name
            persona_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存事实知识库
            facts_file = persona_dir / "facts.json"
            with open(facts_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存风格库
            style_file = persona_dir / "style.json"
            with open(style_file, 'w', encoding='utf-8') as f:
                json.dump(style_base.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存口头习惯库
            habits_file = persona_dir / "habits.json"
            with open(habits_file, 'w', encoding='utf-8') as f:
                json.dump(oral_habits_base.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存历史记录
            history_file = persona_dir / "history.txt"
            with open(history_file, 'w', encoding='utf-8') as f:
                for item in history:
                    f.write(item + '\n')
            
            return True
            
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def create_new_persona(self, persona_name: str) -> Dict:
        """
        创建新人物（初始化空知识库）
        
        Returns:
            包含空知识库的字典
        """
        return {
            "name": persona_name,
            "knowledge_base": KnowledgeBase(),
            "style_base": StyleBase(),
            "oral_habits_base": OralHabitsBase(),
            "history": []
        }
    
    def delete_persona(self, persona_name: str) -> bool:
        """
        删除人物及其所有数据
        
        Returns:
            删除是否成功
        """
        try:
            persona_dir = self.base_dir / persona_name
            if persona_dir.exists():
                # 删除所有文件
                for file in persona_dir.iterdir():
                    file.unlink()
                # 删除目录
                persona_dir.rmdir()
                return True
            return False
            
        except Exception as e:
            print(f"删除失败: {e}")
            return False
    
    def get_persona_stats(self, persona_name: str) -> Optional[Dict]:
        """
        获取人物知识库统计信息
        
        Returns:
            统计信息字典
        """
        data = self.load_persona(persona_name)
        if not data:
            return None
        
        return {
            "name": persona_name,
            "facts_count": len(data["knowledge_base"]),
            "style_observations": len(data["style_base"]),
            "oral_habits": len(data["oral_habits_base"]),
            "history_length": len(data["history"])
        }
