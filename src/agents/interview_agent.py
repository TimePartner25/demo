"""
采访智能体 - 负责与用户进行流畅的多轮对话
"""

import asyncio
from typing import List, Dict, Deque, Optional
from collections import deque
from queue import Queue

from ..models import KnowledgeBase
from ..api import get_api_client
from ..prompts import prompts
from ..utils import log_agent_interaction, append_agent_response


class InterviewAgent:
    """采访智能体 - 前台交互"""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        qa_fact_cache_queue: Queue,
        qa_style_cache_queue: Queue,
        history: List[str],
        max_recent_dialogue: int = 20
    ):
        """
        Args:
            knowledge_base: 事实知识库
            qa_fact_cache_queue: 事实处理队列
            qa_style_cache_queue: 风格处理队列
            history: 用户完整回答历史
            max_recent_dialogue: 短期记忆对话轮数
        """
        self.knowledge_base = knowledge_base
        self.qa_fact_cache_queue = qa_fact_cache_queue
        self.qa_style_cache_queue = qa_style_cache_queue
        self.history = history
        
        # 短期对话记忆（最近N轮）
        self.recent_dialogue_queue: Deque[tuple] = deque(maxlen=max_recent_dialogue)
        
        # 上一个AI问题
        self.last_ai_question: Optional[str] = None
        
        # 缓存系统消息（初始化时生成，后续复用）
        self._cached_system_message = {"role": "system", "content": prompts.INTERVIEW_SYSTEM}

    async def process_chat(self, user_answer: str) -> str:
        """
        处理用户回答并生成下一个问题
        
        Args:
            user_answer: 用户对上一个问题的回答
            
        Returns:
            AI生成的下一个问题
        """
        # 1. 存入历史记录
        self.history.append(user_answer)
        
        # 2. 如果有上一个问题，放入缓存队列
        if self.last_ai_question:
            qa_pair = (self.last_ai_question, user_answer)
            self.qa_fact_cache_queue.put(qa_pair)
            self.qa_style_cache_queue.put(qa_pair)
            
            # 3. 维护短期记忆
            self.recent_dialogue_queue.append(qa_pair)
        
        # 4. 轻量级RAG - 检索已知事实
        known_facts = self._retrieve_known_facts()
        
        # 5. 构建消息
        messages = self._build_messages(known_facts)
        
        # 调试：记录请求
        log_agent_interaction("interview", messages, action="process_chat")
        
        # 6. 调用API获取下一个问题（流式）
        api_client = get_api_client()
        response_stream = await api_client.interview_completion(messages)
        
        # 收集流式响应
        next_question = ""
        async for chunk in response_stream:
            next_question += chunk
            print(chunk, end="", flush=True)  # 实时显示
        
        print()  # 换行
        
        # 调试：记录响应
        append_agent_response("interview", next_question)
        
        # 7. 保存本次AI问题
        self.last_ai_question = next_question.strip()
        
        return self.last_ai_question
    
    def _retrieve_known_facts(self, top_k: int = 5) -> List[str]:
        """
        轻量级检索已知事实
        
        TODO: 可以实现更复杂的语义检索
        目前简单返回全部事实
        """
        all_facts = self.knowledge_base.get_all_facts()
        if not all_facts:
            return []
        
        # 返回最近的top_k条事实
        recent_facts = all_facts[-top_k:]
        return [fact.content for fact in recent_facts]
    
    def _build_messages(self, known_facts: List[str]) -> List[Dict[str, str]]:
        """构建 API请求的消息列表"""
        # 使用缓存的系统消息
        messages = [self._cached_system_message]
        
        # 添加时间上下文
        time_context = prompts.format_time_context()
        messages.append({"role": "system", "content": time_context})
        
        # 添加已知信息上下文
        if known_facts:
            context = prompts.format_known_facts(known_facts)
            messages.append({"role": "system", "content": context})
        
        # 添加最近对话历史
        for ai_q, user_a in self.recent_dialogue_queue:
            messages.append({"role": "assistant", "content": ai_q})
            messages.append({"role": "user", "content": user_a})
        
        return messages
    
    async def start_interview(self) -> str:
        """开始采访，生成第一个问题"""
        messages = [
            self._cached_system_message,
            {"role": "system", "content": prompts.format_time_context()},
            {"role": "system", "content": prompts.INTERVIEW_START}
        ]
        
        # 调试：记录请求
        log_agent_interaction("interview", messages, action="start_interview")
        
        api_client = get_api_client()
        response_stream = await api_client.interview_completion(messages)
        
        first_question = ""
        async for chunk in response_stream:
            first_question += chunk
            print(chunk, end="", flush=True)
        
        print()
        
        # 调试：记录响应
        append_agent_response("interview", first_question)
        
        self.last_ai_question = first_question.strip()
        return self.last_ai_question
