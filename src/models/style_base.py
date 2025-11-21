"""
风格库数据模型 - 存储性格、价值观、情绪特征
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class StyleObservation:
    """风格观察记录"""
    trait_type: str  # 特质类型：personality, value, emotion, behavior
    description: str  # 描述内容
    context: Optional[str] = None  # 观察到的上下文
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0  # 置信度 0-1


class StyleBase:
    """性格与风格知识库"""
    
    def __init__(self):
        self.observations: List[StyleObservation] = []
        self.core_traits: Dict[str, str] = {}  # 核心特质总结
        
    def add_observation(self, trait_type: str, description: str, 
                       context: Optional[str] = None, confidence: float = 1.0):
        """添加单个风格观察"""
        obs = StyleObservation(
            trait_type=trait_type,
            description=description,
            context=context,
            confidence=confidence
        )
        self.observations.append(obs)
        
    def add_observations(self, observations: List[Dict]):
        """批量添加风格观察"""
        for obs_data in observations:
            self.add_observation(
                trait_type=obs_data.get("trait_type", "general"),
                description=obs_data.get("description", ""),
                context=obs_data.get("context"),
                confidence=obs_data.get("confidence", 1.0)
            )
            
    def set_core_trait(self, trait_name: str, description: str):
        """设置核心特质总结"""
        self.core_traits[trait_name] = description
        
    def get_observations_by_type(self, trait_type: str) -> List[StyleObservation]:
        """按类型获取观察记录"""
        return [obs for obs in self.observations if obs.trait_type == trait_type]
    
    def get_personality_summary(self) -> str:
        """获取个性总结 (personality)"""
        personality_obs = self.get_observations_by_type("personality")
        if self.core_traits.get("personality"):
            return self.core_traits["personality"]
        return "; ".join([obs.description for obs in personality_obs[:5]])
    
    def get_values_summary(self) -> str:
        """获取价值观总结 (value)"""
        values_obs = self.get_observations_by_type("value")
        if self.core_traits.get("values"):
            return self.core_traits["values"]
        return "; ".join([obs.description for obs in values_obs[:5]])
    
    def get_emotion_tendency_summary(self) -> str:
        """获取情绪倾向总结 (emotion_tendency)"""
        emotion_obs = self.get_observations_by_type("emotion_tendency")
        if self.core_traits.get("emotion_tendency"):
            return self.core_traits["emotion_tendency"]
        return "; ".join([obs.description for obs in emotion_obs[:5]])
    
    def get_behavior_habit_summary(self) -> str:
        """获取行为习惯总结 (behavior_habit)"""
        behavior_obs = self.get_observations_by_type("behavior_habit")
        if self.core_traits.get("behavior_habit"):
            return self.core_traits["behavior_habit"]
        return "; ".join([obs.description for obs in behavior_obs[:5]])
    
    def get_cognition_style_summary(self) -> str:
        """获取认知风格总结 (cognition_style)"""
        cognition_obs = self.get_observations_by_type("cognition_style")
        if self.core_traits.get("cognition_style"):
            return self.core_traits["cognition_style"]
        return "; ".join([obs.description for obs in cognition_obs[:5]])
    
    def get_all_traits_summary(self) -> Dict[str, str]:
        """
        获取所有5个维度的特质总结
        
        Returns:
            字典格式：{
                "personality": "...",
                "value": "...",
                "emotion_tendency": "...",
                "behavior_habit": "...",
                "cognition_style": "..."
            }
        """
        return {
            "personality": self.get_personality_summary(),
            "value": self.get_values_summary(),
            "emotion_tendency": self.get_emotion_tendency_summary(),
            "behavior_habit": self.get_behavior_habit_summary(),
            "cognition_style": self.get_cognition_style_summary()
        }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "observations": [asdict(obs) for obs in self.observations],
            "core_traits": self.core_traits
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StyleBase":
        """从字典加载"""
        sb = cls()
        for obs_data in data.get("observations", []):
            sb.observations.append(StyleObservation(**obs_data))
        sb.core_traits = data.get("core_traits", {})
        return sb
    
    def __len__(self):
        return len(self.observations)
    
    def __repr__(self):
        return f"StyleBase(observations={len(self.observations)}, core_traits={len(self.core_traits)})"
