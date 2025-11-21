"""
API客户端模块 - 统一封装SiliconFlow API调用
"""

from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncIterator
import asyncio

from ..config import (
    MODEL_NAME,
    INTERVIEW_CONFIG,
    PROCESSING_CONFIG,
    STYLE_SUMMARY_CONFIG,
    IMPERSONATION_CONFIG
)


class APIClient:
    """统一的API客户端"""
    
    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = MODEL_NAME
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Optional[str | AsyncIterator]:
        """
        通用聊天完成接口
        
        Args:
            messages: 消息列表 [{"role": "user/system/assistant", "content": "..."}]
            temperature: 温度参数 (0.0-1.0)
            max_tokens: 最大生成token数
            stream: 是否流式输出
            
        Returns:
            如果stream=False，返回完整响应文本
            如果stream=True，返回异步迭代器
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"API调用错误: {e}")
            return None
    
    async def _stream_response(self, response) -> AsyncIterator[str]:
        """处理流式响应"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def interview_completion(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        采访智能体专用 - 流式、高创造力
        """
        return await self.chat_completion(
            messages=messages,
            **INTERVIEW_CONFIG
        )
    
    async def processing_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        信息处理智能体专用 - 非流式、低随机性
        """
        return await self.chat_completion(
            messages=messages,
            **PROCESSING_CONFIG
        )
    
    async def style_summary_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        风格总结智能体专用 - 非流式、中等创造力
        """
        return await self.chat_completion(
            messages=messages,
            **STYLE_SUMMARY_CONFIG
        )
    
    async def impersonation_completion(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        角色扮演智能体专用 - 流式、高拟人性
        """
        return await self.chat_completion(
            messages=messages,
            **IMPERSONATION_CONFIG
        )


# 全局API客户端实例
_api_client: Optional[APIClient] = None


def initialize_api_client(api_key: str, base_url: str):
    """初始化全局API客户端"""
    global _api_client
    _api_client = APIClient(api_key, base_url)


def get_api_client() -> APIClient:
    """获取全局API客户端实例"""
    if _api_client is None:
        raise RuntimeError("API客户端未初始化，请先调用 initialize_api_client()")
    return _api_client
