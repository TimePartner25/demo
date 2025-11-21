"""
角色扮演智能体 - 模拟目标人物与他人对话
"""

import asyncio
from typing import List, Dict, Deque, Optional
from collections import deque

from ..models import KnowledgeBase, StyleBase, OralHabitsBase
from ..api import get_api_client
from ..prompts import prompts
from ..utils import log_agent_interaction, append_agent_response


class ImpersonationAgent:
    """扮演智能体"""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        style_base: StyleBase,
        oral_habits_base: OralHabitsBase,
        history: List[str],
        persona_name: str,
        max_recent_dialogue: int = 20
    ):
        """
        Args:
            knowledge_base: 事实知识库
            style_base: 风格知识库
            oral_habits_base: 口头习惯库
            history: 原始对话历史
            persona_name: 角色名称，用于增强提示词代入感（必填）
            max_recent_dialogue: 短期记忆对话轮数
        """
        self.knowledge_base = knowledge_base
        self.style_base = style_base
        self.oral_habits_base = oral_habits_base
        self.history = history
        self.persona_name = persona_name
        
        # 短期对话记忆（与新对话者的对话）
        self.recent_dialogue_queue: Deque[tuple] = deque(maxlen=max_recent_dialogue)
        
        # 上一个AI回复
        self.last_ai_response: Optional[str] = None
        
        # 缓存系统提示词（初始化时生成，后续复用）
        self._cached_system_messages = self._build_system_messages()
    
    async def generate_response(self, user_input_b: str) -> str:
        """
        模拟目标人物回复
        
        Args:
            user_input_b: 对话者B的输入
            
        Returns:
            模拟的人物A的回复
        """
        # 1. 构建消息
        messages = self._build_messages(user_input_b)
        
        # 调试：记录请求
        log_agent_interaction("impersonation", messages, persona_name=self.persona_name)
        
        # 2. 调用API生成回复（流式）
        api_client = get_api_client()
        response_stream = await api_client.impersonation_completion(messages)
        
        # 收集流式响应
        response = ""
        async for chunk in response_stream:
            response += chunk
            print(chunk, end="", flush=True)  # 实时显示
        
        print()  # 换行
        
        # 调试：记录响应
        append_agent_response("impersonation", response)
        
        # 4. 维护短期记忆
        self.last_ai_response = response.strip()
        self.recent_dialogue_queue.append((user_input_b, self.last_ai_response))
        
        return self.last_ai_response
    
    def _retrieve_relevant_facts(self) -> List[Dict[str, str]]:
        """
        检索相关事实
        
        根据README要求：现阶段完整送入knowledge_base的事实
        
        Returns:
            事实列表，格式：[{"content": "事实内容", "category": "分类"}, ...]
        """
        all_facts = self.knowledge_base.get_all_facts()
        return [{"content": fact.content, "category": fact.category} for fact in all_facts]
    
    def _build_system_messages(self) -> List[Dict[str, str]]:
        """
        构建系统提示词消息（初始化时调用，后续复用）
        
        Returns:
            系统消息列表
        """
        messages = []
        
        # 1. 角色扮演系统提示词 - 按5个心理维度组织 + 4类语言习惯 + 高频词统计
        all_traits = self.style_base.get_all_traits_summary()
        speaking_style = self.oral_habits_base.get_speaking_style_summary()
        sentence_patterns = self.oral_habits_base.get_sentence_patterns()
        catchphrases = self.oral_habits_base.get_catchphrases()
        tone_words = self.oral_habits_base.get_tone_words()
        # 获取全部高频词（按频次降序）
        all_high_freq = dict(self.oral_habits_base.high_freq_words)
        high_freq_words = sorted(all_high_freq.items(), key=lambda x: x[1], reverse=True)
        
        system_prompt = prompts.build_impersonation_prompt(
            persona_name=self.persona_name,
            personality=all_traits["personality"],
            values=all_traits["value"],
            emotion_tendency=all_traits["emotion_tendency"],
            behavior_habit=all_traits["behavior_habit"],
            cognition_style=all_traits["cognition_style"],
            speaking_style=speaking_style,
            sentence_patterns=sentence_patterns,
            catchphrases=catchphrases,
            tone_words=tone_words,
            high_freq_words=high_freq_words
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 背景资料（事实）
        relevant_facts = self._retrieve_relevant_facts()
        if relevant_facts:
            facts_text = prompts.format_background_facts(relevant_facts)
            messages.append({"role": "system", "content": facts_text})
        
        # 3. 历史示例（如果历史对话少于50条，提供全部历史；否则不提供）
        if len(self.history) < 50 and self.history:
            history_text = prompts.format_history_examples(self.history)
            messages.append({"role": "system", "content": history_text})
        
        return messages
    
    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        """构建API请求的消息列表"""
        # 使用缓存的系统消息
        messages = self._cached_system_messages.copy()
        
        # 添加最近对话历史（与当前对话者）
        for user_b, ai_a in self.recent_dialogue_queue:
            messages.append({"role": "user", "content": user_b})
            messages.append({"role": "assistant", "content": ai_a})
        
        # 添加当前输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
