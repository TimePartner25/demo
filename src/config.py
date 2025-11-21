"""
配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# ==================== API配置 ====================
API_KEY = os.getenv("SILICONFLOW_API_KEY", "sk-kxojlpqqivfrqpfnirsbimqwarggbshfxpozmahykaxuepnl")
API_BASE_URL = "https://api.siliconflow.cn/v1"

# 模型配置
MODEL_NAME = "moonshotai/Kimi-K2-Instruct-0905"

# ==================== 模型参数配置 ====================
# 采访智能体 - 流式、高创造力
# temperature: 0.7-0.9 (高随机性)
# stream: true (强制流式)
# max_tokens: 200-500 (保持互动节奏)
INTERVIEW_CONFIG = {
    "temperature": 0.8,
    "max_tokens": 100,
    "stream": True
}

# 信息处理智能体 - 非流式、低随机性、高准确性
# temperature: 0.1-0.4 (低随机性，保证事实准确)
# stream: false (非流式，一次性获取完整JSON)
# max_tokens: 1000-4000 (给予足够分析空间)
PROCESSING_CONFIG = {
    "temperature": 0.3,
    "max_tokens": 2000,
    "stream": False
}

# 风格总结智能体 - 非流式、中等创造力、宏观总结
# temperature: 0.7 (中等随机性，用于归纳性格)
# stream: false (非流式，等待完整总结)
# max_tokens: 4000+ (或更大，上下文庞大)
STYLE_SUMMARY_CONFIG = {
    "temperature": 0.6,
    "max_tokens": 2000,
    "stream": False
}

# 角色扮演智能体 - 流式、高拟人性
# temperature: 0.7-0.9 (高随机性)
# stream: true (强制流式)
# max_tokens: 200-500 (保持互动节奏)
IMPERSONATION_CONFIG = {
    "temperature": 0.9,
    "max_tokens": 100,
    "stream": True
}

# ==================== 存储配置 ====================
PERSONAS_DIR = PROJECT_ROOT / "personas"

# ==================== 批处理配置 ====================
BATCH_SIZE = 10  # 每批处理的对话数量

# ==================== 对话配置 ====================
MAX_RECENT_DIALOGUE = 20  # 短期记忆保留的对话轮数

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"

# ==================== 调试配置 ====================
# 调试模式：启用时会记录所有提示词和响应到 prompt_catch/ 目录
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# 提示词捕获目录
PROMPT_CATCH_DIR = PROJECT_ROOT / "prompt_catch"
