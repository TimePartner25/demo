"""
口头习惯库数据模型 - 存储语言风格、口头禅、句式特征
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import Counter


@dataclass
class OralHabit:
    """口头习惯记录"""
    habit_type: str  # catchphrase, sentence_pattern, tone_word, speaking_style
    content: str  # 具体内容
    frequency: int = 1  # 出现频率
    examples: List[str] = field(default_factory=list)  # 示例
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class OralHabitsBase:
    """语言习惯知识库"""
    
    def __init__(self):
        self.habits: List[OralHabit] = []
        self.high_freq_words: Counter = Counter()  # 高频词统计
        
    def add_habit(self, habit_type: str, content: str, 
                  frequency: int = 1, examples: Optional[List[str]] = None):
        """添加单个口头习惯"""
        habit = OralHabit(
            habit_type=habit_type,
            content=content,
            frequency=frequency,
            examples=examples or []
        )
        self.habits.append(habit)
        
    def add_habits(self, habits: List[Dict]):
        """批量添加口头习惯"""
        for habit_data in habits:
            self.add_habit(
                habit_type=habit_data.get("habit_type", "general"),
                content=habit_data.get("content", ""),
                frequency=habit_data.get("frequency", 1),
                examples=habit_data.get("examples", [])
            )
            
    def update_word_frequency(self, words: Dict[str, int]):
        """更新高频词统计"""
        self.high_freq_words.update(words)
        
    def get_habits_by_type(self, habit_type: str) -> List[OralHabit]:
        """按类型获取习惯"""
        return [h for h in self.habits if h.habit_type == habit_type]
    
    def get_catchphrases(self) -> List[str]:
        """
        获取口头禅列表（描述性内容）
        
        Returns:
            [content, ...] 描述性内容列表
        """
        habits = self.get_habits_by_type("catchphrase")
        return [h.content for h in habits]
    
    def get_tone_words(self) -> List[str]:
        """
        获取语气词列表（描述性内容）
        
        Returns:
            [content, ...] 描述性内容列表
        """
        habits = self.get_habits_by_type("tone_word")
        return [h.content for h in habits]
    
    def get_top_words(self, n: int = 20) -> List[tuple]:
        """获取高频词 Top N"""
        return self.high_freq_words.most_common(n)
    
    def get_sentence_patterns(self) -> List[str]:
        """获取句式特点列表"""
        habits = self.get_habits_by_type("sentence_pattern")
        return [h.content for h in habits]
    
    def get_speaking_style_summary(self) -> str:
        """获取说话风格总结"""
        styles = self.get_habits_by_type("speaking_style")
        return "; ".join([s.content for s in styles])
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "habits": [asdict(habit) for habit in self.habits],
            "high_freq_words": dict(self.high_freq_words)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OralHabitsBase":
        """从字典加载"""
        ohb = cls()
        for habit_data in data.get("habits", []):
            ohb.habits.append(OralHabit(**habit_data))
        ohb.high_freq_words = Counter(data.get("high_freq_words", {}))
        return ohb
    
    def __len__(self):
        return len(self.habits)
    
    def __repr__(self):
        return f"OralHabitsBase(habits={len(self.habits)}, unique_words={len(self.high_freq_words)})"
