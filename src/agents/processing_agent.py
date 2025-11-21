"""
信息处理智能体 - 后台异步提炼事实信息
"""

import asyncio
from typing import List, Tuple
from queue import Queue, Empty

from ..models import KnowledgeBase
from ..api import get_api_client
from ..prompts import prompts
from ..utils import safe_json_parse, log_agent_interaction


class ProcessingAgent:
    """信息处理智能体 - 后台异步"""
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        qa_fact_cache_queue: Queue,
        batch_size: int = 10
    ):
        """
        Args:
            knowledge_base: 事实知识库
            qa_fact_cache_queue: 待处理的对话队列
            batch_size: 批处理大小
        """
        self.knowledge_base = knowledge_base
        self.qa_fact_cache_queue = qa_fact_cache_queue
        self.batch_size = batch_size
        self.running = False

    async def run(self):
        """后台运行的主循环"""
        self.running = True
        print("[ProcessingAgent] 后台信息处理服务启动")
        
        while self.running:
            try:
                # 检查队列中是否有足够的对话
                if self.qa_fact_cache_queue.qsize() >= self.batch_size:
                    await self._process_batch()
                else:
                    # 队列不足，短暂等待
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"[ProcessingAgent] 处理错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self):
        """处理一批对话"""
        # 从队列中取出batch_size个对话
        fact_batch: List[Tuple[str, str]] = []
        
        for _ in range(self.batch_size):
            try:
                qa_pair = self.qa_fact_cache_queue.get_nowait()
                fact_batch.append(qa_pair)
            except Empty:
                break
        
        if not fact_batch:
            return
        
        print(f"\n[ProcessingAgent] 开始处理 {len(fact_batch)} 条对话...")
        
        # 构建批量对话文本
        dialogue_text = prompts.format_dialogue_batch(fact_batch)
        
        # 调用API提炼事实
        messages = [
            {"role": "system", "content": prompts.FACT_EXTRACTION},
            {"role": "user", "content": dialogue_text}
        ]
        
        api_client = get_api_client()
        response = await api_client.processing_completion(messages)
        
        # 调试：记录交互
        log_agent_interaction("processing", messages, response, batch_size=len(fact_batch))
        
        # 解析响应并存入知识库
        if response:
            await self._extract_and_store_facts(response)
            print(f"[ProcessingAgent] 成功提炼并存储事实，当前知识库大小: {len(self.knowledge_base)}")
    
    def _format_dialogue_batch(self, batch: List[Tuple[str, str]]) -> str:
        """格式化对话批次"""
        formatted = "对话记录：\n\n"
        for i, (question, answer) in enumerate(batch, 1):
            formatted += f"问题{i}: {question}\n"
            formatted += f"回答{i}: {answer}\n\n"
        return formatted
    
    async def _extract_and_store_facts(self, response: str):
        """解析响应并存储事实"""
        data = safe_json_parse(response)
        
        if data:
            facts = data.get("facts", [])
            if facts:
                self.knowledge_base.add_facts(facts)
                print(f"[ProcessingAgent] 成功提取 {len(facts)} 条事实")
            else:
                print(f"[ProcessingAgent] 响应中没有找到事实")
        else:
            print(f"[ProcessingAgent] JSON解析失败")
            print(f"响应内容: {response[:200]}...")
    
    async def flush_remaining(self):
        """强制处理队列中剩余的所有对话（不足batch_size也处理）"""
        remaining_count = self.qa_fact_cache_queue.qsize()
        
        if remaining_count == 0:
            print("[ProcessingAgent] 队列为空，无需处理")
            return
        
        print(f"\n[ProcessingAgent] 正在处理fact缓存队列中剩余的 {remaining_count} 条对话...")
        
        # 取出所有剩余对话
        fact_batch: List[Tuple[str, str]] = []
        while not self.qa_fact_cache_queue.empty():
            try:
                qa_pair = self.qa_fact_cache_queue.get_nowait()
                fact_batch.append(qa_pair)
            except Empty:
                break
        
        if fact_batch:
            # 构建批量对话文本
            dialogue_text = prompts.format_dialogue_batch(fact_batch)
            
            # 调用API提炼事实
            messages = [
                {"role": "system", "content": prompts.FACT_EXTRACTION},
                {"role": "user", "content": dialogue_text}
            ]
            
            api_client = get_api_client()
            response = await api_client.processing_completion(messages)
            
            # 调试：记录交互
            log_agent_interaction("processing", messages, response, 
                                batch_size=len(fact_batch), action="flush_remaining")
            
            # 解析响应并存入知识库
            if response:
                await self._extract_and_store_facts(response)
                print(f"[ProcessingAgent] 剩余对话处理完成，当前知识库大小: {len(self.knowledge_base)}")
    
    def stop(self):
        """停止后台服务"""
        self.running = False
        print("[ProcessingAgent] 后台信息处理服务停止")
