# 简介

## 1. 核心智能体

1. **[采访智能体 (InterviewAgent)](src/agents/interview_agent.py)** ：负责阶段一，主动与人类 A 对话，保持互动流畅性，并具备策略性提问能力。
2. **[信息处理智能体 (ProcessingAgent)](src/agents/processing_agent.py)** ：(后台异步) 负责阶段一，分批次从对话中 **只提炼事实** 。
3. **[风格总结智能体 (StyleSummaryAgent)](src/agents/style_summary_agent.py)** ：(后台异步)负责阶段一，分批次从对话中 **只进行风格总结** 。
4. **[对话扮演智能体 (ImpersonationAgent)](src/agents/impersonation_agent.py)** ：负责阶段二，模拟人类 A 进行对话。

## 2. 配置

1. 各类配置在 **[src/config.py](src/config.py)** 中
2. 所有提示词在 **[src/prompts.py](src/prompts.py)** 中

## 3. 项目结构示意

```
redemo/
├─ README.md                # 项目简介
├─ arch.md                  # 项目规划文档
├─ main.py                  # 程序入口与交互逻辑
├─ requirements.txt         # Python 依赖列表
├─ personas/                # 人格数据与历史记录
├─ src/
│  ├─ __init__.py          # 包初始化
│  ├─ config.py            # 全局配置项
│  ├─ prompts.py           # 提示词与生成模板
│  ├─ agents/
│  │  ├─ __init__.py
│  │  ├─ interview_agent.py      # 采访智能体
│  │  ├─ impersonation_agent.py  # 角色扮演智能体
│  │  ├─ processing_agent.py     # 事实提取智能体
│  │  └─ style_summary_agent.py  # 风格总结智能体
│  ├─ api/
│  │  ├─ __init__.py
│  │  └─ client.py               # OpenAI 兼容 API 客户端
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ knowledge_base.py       # 事实知识库
│  │  ├─ oral_habits_base.py     # 语言习惯库
│  │  └─ style_base.py           # 风格特质库
│  ├─ storage/
│  │  ├─ __init__.py
│  │  └─ persona_manager.py      # 人格数据读写
│  └─ utils/
│     ├─ __init__.py
│     ├─ debug_logger.py         # 调试日志记录
│     └─ helpers.py              # 通用辅助函数
└─ .gitignore                    # Git 忽略列表
```
