"""
风格总结智能体 - 后台异步提炼风格和语言习惯
"""

import asyncio
from typing import List, Tuple
from queue import Queue, Empty

from ..models import StyleBase, OralHabitsBase
from ..api import get_api_client
from ..prompts import prompts
from ..utils import safe_json_parse, log_agent_interaction


class StyleSummaryAgent:
    """风格总结智能体 - 后台异步"""
    
    def __init__(
        self,
        style_base: StyleBase,
        oral_habits_base: OralHabitsBase,
        qa_style_cache_queue: Queue,
        batch_size: int = 10
    ):
        """
        Args:
            style_base: 风格知识库
            oral_habits_base: 口头习惯库
            qa_style_cache_queue: 待处理的对话队列
            batch_size: 批处理大小
        """
        self.style_base = style_base
        self.oral_habits_base = oral_habits_base
        self.qa_style_cache_queue = qa_style_cache_queue
        self.batch_size = batch_size
        self.running = False

    async def run(self):
        """后台运行的主循环"""
        self.running = True
        print("[StyleSummaryAgent] 后台风格分析服务启动")
        
        while self.running:
            try:
                # 检查队列中是否有足够的对话
                if self.qa_style_cache_queue.qsize() >= self.batch_size:
                    await self._process_batch()
                else:
                    # 队列不足，短暂等待
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"[StyleSummaryAgent] 处理错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self):
        """处理一批对话"""
        # 从队列中取出batch_size个对话
        style_batch: List[Tuple[str, str]] = []
        
        for _ in range(self.batch_size):
            try:
                qa_pair = self.qa_style_cache_queue.get_nowait()
                style_batch.append(qa_pair)
            except Empty:
                break
        
        if not style_batch:
            return
        
        print(f"\n[StyleSummaryAgent] 开始分析 {len(style_batch)} 条对话的风格...")
        
        # 构建批量对话文本
        dialogue_text = prompts.format_dialogue_batch_for_style(style_batch)
        
        # 获取已有的高频词统计
        current_high_freq = dict(self.oral_habits_base.high_freq_words)
        known_words_text = prompts.format_known_high_freq_words(current_high_freq)
        
        # 调用API提炼风格（包含已知高频词）
        messages = [
            {"role": "system", "content": prompts.STYLE_EXTRACTION},
            {"role": "system", "content": known_words_text},
            {"role": "user", "content": dialogue_text}
        ]
        
        api_client = get_api_client()
        response = await api_client.style_summary_completion(messages)
        
        # 调试：记录交互
        log_agent_interaction("style_summary", messages, response, batch_size=len(style_batch))
        
        # 解析响应并存入知识库
        if response:
            await self._extract_and_store_styles(response)
            print(f"[StyleSummaryAgent] 成功提炼并存储风格数据")
    
    async def _extract_and_store_styles(self, response: str):
        """解析响应并存储风格数据"""
        data = safe_json_parse(response)
        
        if data:
            # 存储口头习惯
            oral_habits = data.get("oral_habits", [])
            if oral_habits:
                self.oral_habits_base.add_habits(oral_habits)
                print(f"[StyleSummaryAgent] 提取 {len(oral_habits)} 条口头习惯")
            
            # 存储风格观察
            style_observations = data.get("style_observations", [])
            if style_observations:
                self.style_base.add_observations(style_observations)
                print(f"[StyleSummaryAgent] 提取 {len(style_observations)} 条风格观察")
            
            # 更新高频词（AI返回的是累积后的完整结果，直接覆写）
            high_freq_words = data.get("high_freq_words", {})
            if high_freq_words:
                # 清空旧数据，使用AI返回的累积结果
                self.oral_habits_base.high_freq_words.clear()
                self.oral_habits_base.high_freq_words.update(high_freq_words)
                print(f"[StyleSummaryAgent] 覆写高频词统计，当前共 {len(high_freq_words)} 个词")
        else:
            print(f"[StyleSummaryAgent] JSON解析失败")
            print(f"响应内容: {response[:200]}...")
    
    async def flush_remaining(self):
        """强制处理队列中剩余的所有对话（不足batch_size也处理）"""
        remaining_count = self.qa_style_cache_queue.qsize()
        
        if remaining_count == 0:
            print("[StyleSummaryAgent] 队列为空，无需处理")
            return
        
        print(f"\n[StyleSummaryAgent] 正在分析style缓存队列中剩余的 {remaining_count} 条对话...")
        
        # 取出所有剩余对话
        style_batch: List[Tuple[str, str]] = []
        while not self.qa_style_cache_queue.empty():
            try:
                qa_pair = self.qa_style_cache_queue.get_nowait()
                style_batch.append(qa_pair)
            except Empty:
                break
        
        if style_batch:
            # 构建批量对话文本
            dialogue_text = prompts.format_dialogue_batch_for_style(style_batch)
            
            # 获取已有的高频词统计
            current_high_freq = dict(self.oral_habits_base.high_freq_words)
            known_words_text = prompts.format_known_high_freq_words(current_high_freq)
            
            # 调用API提炼风格（包含已知高频词）
            messages = [
                {"role": "system", "content": prompts.STYLE_EXTRACTION},
                {"role": "system", "content": known_words_text},
                {"role": "user", "content": dialogue_text}
            ]
            
            api_client = get_api_client()
            response = await api_client.style_summary_completion(messages)
            
            # 调试：记录交互
            log_agent_interaction("style_summary", messages, response, 
                                batch_size=len(style_batch), action="flush_remaining")
            
            # 解析响应并存入知识库
            if response:
                await self._extract_and_store_styles(response)
                print(f"[StyleSummaryAgent] 剩余对话分析完成")
    
    def stop(self):
        """停止后台服务"""
        self.running = False
        print("[StyleSummaryAgent] 后台风格分析服务停止")
