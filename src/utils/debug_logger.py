"""
调试日志记录器 - 记录所有提示词和AI响应
仅在 DEBUG_MODE=True 时生效
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from threading import Lock

from ..config import DEBUG_MODE, PROMPT_CATCH_DIR


class DebugLogger:
    """调试日志记录器 - 单例模式"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.enabled = DEBUG_MODE
        self.session_dir: Optional[Path] = None
        self.agent_files = {}  # {agent_type: file_handle}
        self.request_counters = {}  # {agent_type: count}
        
        if self.enabled:
            self._init_session()
    
    def _init_session(self):
        """初始化调试会话目录"""
        if not self.enabled:
            return
        
        # 创建会话目录（基于时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = PROMPT_CATCH_DIR / f"session_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[DebugLogger] 调试会话已启动，日志目录: {self.session_dir}")
    
    def log_request_response(
        self,
        agent_type: str,
        messages: List[Dict[str, str]],
        response: str,
        metadata: dict = None
    ):
        """
        记录请求和响应
        
        Args:
            agent_type: 智能体类型 (interview/processing/style_summary/impersonation)
            messages: 发送给AI的完整消息列表
            response: AI的响应
            metadata: 额外的元数据
        """
        if not self.enabled or not self.session_dir:
            return
        
        try:
            # 获取或创建agent文件
            if agent_type not in self.agent_files:
                agent_file = self.session_dir / f"{agent_type}.log"
                self.agent_files[agent_type] = agent_file
                self.request_counters[agent_type] = 0
                
                # 写入文件头
                with open(agent_file, "w", encoding="utf-8") as f:
                    f.write(f"{'='*100}\n")
                    f.write(f"Agent Type: {agent_type}\n")
                    f.write(f"Session Start: {datetime.now().isoformat()}\n")
                    f.write(f"{'='*100}\n\n")
            
            # 增加计数
            self.request_counters[agent_type] += 1
            count = self.request_counters[agent_type]
            
            # 追加记录
            agent_file = self.agent_files[agent_type]
            with open(agent_file, "a", encoding="utf-8") as f:
                # 写入分隔符和元数据
                f.write(f"\n{'#'*100}\n")
                f.write(f"Request #{count} - {datetime.now().isoformat()}\n")
                if metadata:
                    f.write(f"Metadata: {json.dumps(metadata, ensure_ascii=False)}\n")
                f.write(f"{'#'*100}\n\n")
                
                # 写入请求（提示词）
                f.write(f"{'='*50} REQUEST {'='*50}\n\n")
                for i, msg in enumerate(messages, 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    f.write(f"[Message {i}] Role: {role}\n")
                    f.write(f"{'-'*100}\n")
                    f.write(f"{content}\n")
                    f.write(f"{'-'*100}\n\n")
                
                # 写入响应
                f.write(f"\n{'='*50} RESPONSE {'='*50}\n\n")
                f.write(f"{response}\n")
                f.write(f"\n{'='*100}\n\n")
        
        except Exception as e:
            # 静默失败，不影响主流程
            print(f"[DebugLogger] 记录失败: {e}")
    
    def log_request_only(
        self,
        agent_type: str,
        messages: List[Dict[str, str]],
        metadata: dict = None
    ):
        """
        仅记录请求（用于流式响应场景）
        
        Args:
            agent_type: 智能体类型
            messages: 发送给AI的完整消息列表
            metadata: 额外的元数据
        """
        if not self.enabled or not self.session_dir:
            return
        
        try:
            # 获取或创建agent文件
            if agent_type not in self.agent_files:
                agent_file = self.session_dir / f"{agent_type}.log"
                self.agent_files[agent_type] = agent_file
                self.request_counters[agent_type] = 0
                
                # 写入文件头
                with open(agent_file, "w", encoding="utf-8") as f:
                    f.write(f"{'='*100}\n")
                    f.write(f"Agent Type: {agent_type}\n")
                    f.write(f"Session Start: {datetime.now().isoformat()}\n")
                    f.write(f"{'='*100}\n\n")
            
            # 增加计数
            self.request_counters[agent_type] += 1
            count = self.request_counters[agent_type]
            
            # 追加记录
            agent_file = self.agent_files[agent_type]
            with open(agent_file, "a", encoding="utf-8") as f:
                # 写入分隔符和元数据
                f.write(f"\n{'#'*100}\n")
                f.write(f"Request #{count} - {datetime.now().isoformat()}\n")
                if metadata:
                    f.write(f"Metadata: {json.dumps(metadata, ensure_ascii=False)}\n")
                f.write(f"{'#'*100}\n\n")
                
                # 写入请求（提示词）
                f.write(f"{'='*50} REQUEST {'='*50}\n\n")
                for i, msg in enumerate(messages, 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    f.write(f"[Message {i}] Role: {role}\n")
                    f.write(f"{'-'*100}\n")
                    f.write(f"{content}\n")
                    f.write(f"{'-'*100}\n\n")
                
                # 标记响应待补充
                f.write(f"\n{'='*50} RESPONSE (STREAMING) {'='*50}\n\n")
        
        except Exception as e:
            print(f"[DebugLogger] 记录失败: {e}")
    
    def append_response(self, agent_type: str, response: str):
        """
        追加流式响应
        
        Args:
            agent_type: 智能体类型
            response: AI的完整响应
        """
        if not self.enabled or not self.session_dir:
            return
        
        try:
            agent_file = self.agent_files.get(agent_type)
            if agent_file:
                with open(agent_file, "a", encoding="utf-8") as f:
                    f.write(f"{response}\n")
                    f.write(f"\n{'='*100}\n\n")
        
        except Exception as e:
            print(f"[DebugLogger] 追加响应失败: {e}")
    
    def close(self):
        """关闭调试会话"""
        if self.enabled and self.session_dir:
            print(f"[DebugLogger] 调试会话结束，日志已保存至: {self.session_dir}")
            self.agent_files.clear()


# 全局单例
_debug_logger = DebugLogger()


# 便捷函数
def log_agent_interaction(agent_type: str, messages: List[Dict[str, str]], 
                          response: str = None, **metadata):
    """
    记录智能体交互
    
    Args:
        agent_type: 智能体类型
        messages: 消息列表
        response: AI响应（可选，如果是流式可以后续追加）
        **metadata: 元数据
    """
    if response is not None:
        _debug_logger.log_request_response(agent_type, messages, response, metadata)
    else:
        _debug_logger.log_request_only(agent_type, messages, metadata)


def append_agent_response(agent_type: str, response: str):
    """追加流式响应"""
    _debug_logger.append_response(agent_type, response)


def close_debug_session():
    """关闭调试会话"""
    _debug_logger.close()
