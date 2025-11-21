# RE-DEMO 项目架构文档

## 📋 目录

- [项目概述](#项目概述)
- [核心设计理念](#核心设计理念)
- [系统架构](#系统架构)
- [模块详解](#模块详解)
- [数据流](#数据流)
- [提示词工程](#提示词工程)
- [技术栈](#技术栈)
- [扩展性设计](#扩展性设计)

---

## 项目概述

RE-DEMO 是一个基于大语言模型的 **AI 人格克隆与模拟系统**，通过深度对话采集和多维度分析，构建出能够高度还原目标人物语言风格、性格特征和思维模式的数字分身。

### 核心功能

1. **智能采访**：朋友式自然对话，深度挖掘人物信息
2. **知识提取**：自动提炼事实、风格和语言习惯
3. **人格重建**：基于 5 维心理特质和 4 类语言习惯构建人格模型
4. **角色扮演**：高精度模拟目标人物进行对话

### 技术特点

- **异步多智能体架构**：采访、处理、分析并行运行
- **批处理优化**：10 条对话批次处理，提升效率
- **RAG 轻量检索**：基于事实的上下文增强
- **时间感知系统**：根据时间、星期、季节调整对话风格
- **双模式运行**：采访模式 + 模拟模式无缝切换

---

## 核心设计理念

### 1. 分离关注点（Separation of Concerns）

```
用户交互层 → 智能体层 → 数据存储层
     ↓            ↓           ↓
  main.py    4个专业智能体   3个知识库
```

每个智能体专注单一职责，互不干扰但协同工作。

### 2. 知识三元组

```
事实（Facts） + 风格（Style） + 语言习惯（Oral Habits）
     ↓               ↓                    ↓
  Who/What        How to think        How to speak
```

完整的人格模型 = 客观事实 + 主观特质 + 表达方式

### 3. 异步批处理

```
采访智能体（前台实时交互）
        ↓
    队列缓存
        ↓
后台智能体（批量处理）
   ↙         ↘
事实提取    风格分析
```

前台流畅对话，后台高效处理。

### 4. 提示词工程化

```
静态模板 + 动态上下文 + 结构化输出
     ↓            ↓             ↓
  PROMPTS    Knowledge Base    JSON
```

所有提示词集中管理，便于维护和优化。

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层                            │
│                        (main.py)                             │
│  ┌──────────────┐              ┌──────────────┐             │
│  │  采访模式     │              │  模拟模式     │             │
│  │ (Interview)  │              │(Impersonation)│             │
│  └──────────────┘              └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                       智能体层 (Agents)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │InterviewAgent│  │ProcessingAgent│ │StyleSummaryAgent│    │
│  │   (前台)     │  │   (后台)     │  │   (后台)     │         │
│  │   实时交互    │  │  事实提取    │  │  风格分析    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         ↓                ↓                  ↓                │
│    Queue(20轮)      Queue(10条)        Queue(10条)          │
│         ↓                ↓                  ↓                │
│  ┌──────────────────────────────────────────────┐           │
│  │         ImpersonationAgent (前台)              │           │
│  │            角色扮演与模拟                       │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层 (Models)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │KnowledgeBase│  │  StyleBase  │  │OralHabitsBase│         │
│  │  事实知识库  │  │  风格知识库  │  │  语言习惯库  │         │
│  │             │  │             │  │             │         │
│  │ • Facts     │  │ • 5维心理   │  │ • 4类习惯   │         │
│  │ • Category  │  │   特质      │  │ • 高频词    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   持久化层 (Storage)                          │
│              PersonaManager (JSON 文件存储)                   │
│                   personas/{name}/                           │
│           • persona.json (完整人格数据)                       │
│           • history.txt (对话历史)                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    API 层 (External)                         │
│              SiliconFlow API (OpenAI Compatible)             │
│              Model: moonshotai/Kimi-K2-Instruct-0905         │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块详解

### 1. 主程序 (main.py)

**职责**：

- 用户交互入口
- 模式切换控制
- 生命周期管理

**核心流程**：

```python
1. 初始化环境 (API key, DEBUG_MODE)
2. 加载或创建 Persona
3. 初始化 4 个智能体
4. 启动后台任务
5. 进入主循环:
   - 采访模式: InterviewAgent 交互
   - 模拟模式: ImpersonationAgent 交互
6. 优雅退出:
   - 处理剩余队列
   - 保存所有数据
```

**关键代码结构**：

```python
async def main():
    # 1. 环境准备
    load_dotenv()

    # 2. 人格管理
    persona_manager = PersonaManager("personas")

    # 3. 初始化知识库
    knowledge_base = KnowledgeBase()
    style_base = StyleBase()
    oral_habits_base = OralHabitsBase()

    # 4. 初始化智能体
    interview_agent = InterviewAgent(...)
    processing_agent = ProcessingAgent(...)
    style_summary_agent = StyleSummaryAgent(...)
    impersonation_agent = ImpersonationAgent(...)

    # 5. 后台任务
    style_task = asyncio.create_task(style_summary_agent.run())

    # 6. 主循环
    while True:
        if mode == "interview":
            # 采访模式
        elif mode == "impersonate":
            # 模拟模式
```

---

### 2. 智能体层 (src/agents/)

#### 2.1 InterviewAgent (采访智能体)

**职责**：前台实时交互，采集用户信息

**特性**：

- 朋友式对话风格
- 动态温度调整（根据用户回应风格）
- 短期记忆（最近 20 轮对话）
- 轻量级 RAG（检索已知事实）
- 时间感知（北京时间 + 场景规则）

**消息构建**：

```python
messages = [
    {"role": "system", "content": INTERVIEW_SYSTEM},           # 角色定位
    {"role": "system", "content": format_time_context()},      # 时间上下文
    {"role": "system", "content": format_known_facts(facts)},  # 已知事实
    # ... 最近 20 轮对话历史
    {"role": "user", "content": user_answer}                   # 当前输入
]
```

**工作流程**：

```
用户回答 → 存入 history
    ↓
构建 QA pair → 放入两个队列
    ↓
检索相关事实 → 构建消息
    ↓
调用 API → 流式输出
    ↓
维护短期记忆 → 返回下一个问题
```

---

#### 2.2 ProcessingAgent (事实处理智能体)

**职责**：批量提取客观事实

**特性**：

- 批处理（10 条对话为一批）
- JSON 结构化输出
- 主谓宾完整性校验
- 分类标签自动标注

**提取标准**：

```
✅ 合格的事实：
- 我是一名软件工程师，主要做后端开发
- 我毕业于清华大学计算机系，2015年本科毕业
- 下雨天，我的心情好一点

❌ 不合格的回答：
- "有啊"（无实质内容）
- "没有"（纯否定）
- "在图书馆"（缺主语）
```

**输出格式**：

```json
{
  "facts": [
    {
      "content": "我是一名软件工程师，主要做后端开发",
      "category": "职业"
    }
  ]
}
```

---

#### 2.3 StyleSummaryAgent (风格分析智能体)

**职责**：批量分析语言风格和性格特质

**特性**：

- 异步后台运行
- 批处理（10 条对话为一批）
- 5 维心理特质提炼
- 4 类语言习惯识别
- 高频词累积统计

**分析维度**：

**A. 语言习惯 (oral_habits)**

| 类型             | 说明     | 存储方式 | 示例                           |
| ---------------- | -------- | -------- | ------------------------------ |
| catchphrase      | 口头禅   | 描述性   | "频繁使用'其实吧'、'怎么说呢'" |
| tone_word        | 语气词   | 描述性   | "喜欢在句末使用'吧'、'呢'"     |
| sentence_pattern | 句式特点 | 描述性   | "习惯用短句；经常使用反问句"   |
| speaking_style   | 说话风格 | 描述性   | "幽默风趣；温和礼貌"           |

**B. 性格特质 (style_observations)**

| 维度             | 类型      | 说明                               |
| ---------------- | --------- | ---------------------------------- |
| personality      | 静态      | 内在核心倾向（外向乐观、内向谨慎） |
| value            | 静态      | 是非对错准绳（重视效率、家庭至上） |
| emotion_tendency | 动态      | 常见情感倾向（谈及工作时兴奋）     |
| behavior_habit   | 动态/外显 | 社会互动倾向（喜欢主动提问）       |
| cognition_style  | 静态/内在 | 信息处理方式（擅长归纳总结）       |

**C. 高频词统计 (high_freq_words)**

```python
# 累积计数算法
已知统计: {"其实": 10, "然后": 8}
本批次统计: {"其实": 5, "然后": 4, "工作": 3}
       ↓
返回结果: {"其实": 15, "然后": 12, "工作": 3}
```

**输出格式**：

```json
{
  "oral_habits": [
    {
      "habit_type": "catchphrase",
      "content": "频繁使用'其实吧'、'怎么说呢'等过渡性短语",
      "examples": ["其实吧，我觉得...", "怎么说呢，应该是..."]
    }
  ],
  "style_observations": [
    {
      "trait_type": "personality",
      "description": "外向乐观，善于表达",
      "context": "回答问题时总是充满热情，喜欢分享细节"
    }
  ],
  "high_freq_words": {
    "其实": 15,
    "然后": 12,
    "工作": 3
  }
}
```

---

#### 2.4 ImpersonationAgent (角色扮演智能体)

**职责**：模拟目标人物进行对话

**特性**：

- 完全第一人称代入
- 5 维 + 4 类完整人格设定
- 知识边界严格控制（反编造）
- 时间场景感知
- 短期对话记忆（最近 20 轮）

**系统提示词构建**：

```python
# 1. 角色基础设定
prompt = f"""
# 角色扮演任务：你是【{persona_name}】

【个性 (personality)】: {personality}
【价值观 (value)】: {values}
【情绪倾向 (emotion_tendency)】: {emotion_tendency}
【行为习惯 (behavior_habit)】: {behavior_habit}
【认知风格 (cognition_style)】: {cognition_style}

【语言风格与习惯】
- (总体说话风格): {speaking_style}
- (句式特点): {sentence_patterns}
- (口头禅): {catchphrases}
- (语气词): {tone_words}

【高频词统计】
{high_freq_words}

--- 场景行为调整规则 ---
周内/周末、季节、时段影响...

--- 绝对执行规则 ---
1. 第一人称代入
2. 知识边界控制
3. 简洁真实
...
"""

# 2. 背景事实
format_background_facts(facts)

# 3. 历史示例（<50条时）
format_history_examples(history)
```

**消息结构**：

```python
messages = [
    # 系统消息（初始化时缓存）
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": background_facts},
    {"role": "system", "content": history_examples},

    # 最近对话历史
    {"role": "user", "content": "用户提问1"},
    {"role": "assistant", "content": "AI回答1"},
    # ... 最近 20 轮

    # 当前输入
    {"role": "user", "content": current_input}
]
```

---

### 3. 数据模型层 (src/models/)

#### 3.1 KnowledgeBase (事实知识库)

**数据结构**：

```python
@dataclass
class Fact:
    content: str       # 事实内容
    category: str      # 分类标签
    timestamp: str     # 时间戳
    confidence: float  # 置信度
```

**核心方法**：

```python
add_fact(content, category)           # 添加单条事实
add_facts(facts: List[Dict])          # 批量添加
get_all_facts() -> List[Fact]         # 获取全部
get_facts_by_category(category)       # 按类别筛选
to_dict() / from_dict()               # 序列化
```

**特点**：

- 去重机制（避免重复存储）
- 分类管理（身份、家庭、教育等 20+ 类别）
- 时间追踪（记录提取时间）

---

#### 3.2 StyleBase (风格知识库)

**数据结构**：

```python
@dataclass
class StyleObservation:
    trait_type: str       # 特质类型（5维之一）
    description: str      # 描述
    context: str          # 原始语境
    timestamp: str        # 时间戳
    confidence: float     # 置信度
```

**核心方法**：

```python
add_observation(trait_type, description, context)
get_personality_summary() -> str          # 个性总结
get_values_summary() -> str               # 价值观总结
get_emotion_tendency_summary() -> str     # 情绪倾向总结
get_behavior_habit_summary() -> str       # 行为习惯总结
get_cognition_style_summary() -> str      # 认知风格总结
get_all_traits_summary() -> Dict          # 全部维度
```

**特点**：

- 5 维分类管理
- 自动聚合总结
- 支持核心特质标记

---

#### 3.3 OralHabitsBase (语言习惯库)

**数据结构**：

```python
@dataclass
class OralHabit:
    habit_type: str          # 习惯类型（4类之一）
    content: str             # 描述性内容
    frequency: int           # 频率（保留但不使用）
    examples: List[str]      # 示例
    timestamp: str           # 时间戳
```

**核心方法**：

```python
add_habit(habit_type, content, examples)
get_catchphrases() -> List[str]           # 口头禅
get_tone_words() -> List[str]             # 语气词
get_sentence_patterns() -> List[str]      # 句式特点
get_speaking_style_summary() -> str       # 说话风格

# 高频词统计
high_freq_words: Counter                  # 词频统计器
update_word_frequency(words: Dict)        # 更新频率
get_top_words(n) -> List[tuple]           # 获取 Top N
```

**特点**：

- 4 类语言习惯描述性存储
- 高频词独立频率统计
- 自动去重和聚合

---

### 4. 持久化层 (src/storage/)

#### PersonaManager

**职责**：人格数据的加载、保存和管理

**目录结构**：

```
personas/
└── {persona_name}/
    ├── persona.json      # 完整人格数据
    └── history.txt       # 对话历史
```

**persona.json 结构**：

```json
{
  "name": "张三",
  "created_at": "2025-11-21T18:00:00",
  "last_updated": "2025-11-21T20:30:00",
  "knowledge_base": {
    "facts": [...]
  },
  "style_base": {
    "observations": [...],
    "core_traits": {}
  },
  "oral_habits_base": {
    "habits": [...],
    "high_freq_words": {}
  }
}
```

**核心方法**：

```python
list_personas() -> List[str]              # 列出所有人格
load_persona(name) -> Dict                # 加载人格
save_persona(name, data)                  # 保存人格
delete_persona(name)                      # 删除人格
persona_exists(name) -> bool              # 检查存在
```

---

### 5. 提示词管理 (src/prompts.py)

**设计理念**：

- 集中管理所有提示词
- 静态模板 + 动态参数
- 详细文档注释
- 跳转链接标注

**提示词列表**：

| 提示词常量                     | 用途           | 智能体             |
| ------------------------------ | -------------- | ------------------ |
| `INTERVIEW_SYSTEM`             | 采访系统提示词 | InterviewAgent     |
| `INTERVIEW_START`              | 开场白生成     | InterviewAgent     |
| `FACT_EXTRACTION`              | 事实提取       | ProcessingAgent    |
| `STYLE_EXTRACTION`             | 风格分析       | StyleSummaryAgent  |
| `build_impersonation_prompt()` | 角色扮演       | ImpersonationAgent |

**辅助方法**：

```python
format_known_facts(facts)                 # 格式化事实
format_dialogue_batch(batch)              # 格式化对话批次
format_background_facts(facts)            # 格式化背景资料
format_history_examples(history)          # 格式化历史示例
format_known_high_freq_words(words)       # 格式化高频词
get_beijing_time()                        # 获取北京时间
format_time_context()                     # 格式化时间上下文
```

---

### 6. API 层 (src/api/)

#### APIClient

**职责**：与 LLM API 交互

**特性**：

- 流式响应支持
- 统一错误处理
- 可配置参数

**核心方法**：

```python
async def interview_completion(messages):
    """采访智能体 API 调用"""
    return stream_response

async def processing_completion(messages):
    """事实处理 API 调用"""
    return json_response

async def style_summary_completion(messages):
    """风格分析 API 调用"""
    return json_response

async def impersonation_completion(messages):
    """角色扮演 API 调用"""
    return stream_response
```

**配置**：

```python
endpoint = "https://api.siliconflow.cn/v1"
model = "moonshotai/Kimi-K2-Instruct-0905"
temperature = 0.7
max_tokens = 2000
```

---

### 7. 工具层 (src/utils/)

#### 7.1 DebugLogger (调试日志)

**职责**：记录所有 AI 交互

**目录结构**：

```
prompt_catch/
└── session_{YYYYMMDD_HHMMSS}/
    ├── interview.log
    ├── impersonation.log
    ├── processing.log
    └── style_summary.log
```

**功能**：

- 按 session 组织
- 记录 request + response
- 支持流式追加
- 环境变量控制（DEBUG_MODE）

**使用**：

```python
log_agent_interaction("interview", messages, response)
append_agent_response("interview", chunk)
```

---

#### 7.2 Helpers (辅助工具)

```python
safe_json_parse(text)           # 安全 JSON 解析
load_api_key()                  # 加载 API key
```

---

## 数据流

### 采访模式完整流程

```
用户输入 "我是一名程序员"
         ↓
InterviewAgent.process_chat()
         ↓
1. 存入 history: ["我是一名程序员"]
         ↓
2. 构建 QA pair: (question, "我是一名程序员")
         ↓
3. 放入队列:
   - qa_fact_cache_queue.put(qa_pair)
   - qa_style_cache_queue.put(qa_pair)
         ↓
4. 检索已知事实: []（首次为空）
         ↓
5. 构建消息:
   [
     {"role": "system", "content": INTERVIEW_SYSTEM},
     {"role": "system", "content": "【当前时间】2025年11月21日 18:00"},
     {"role": "user", "content": "我是一名程序员"}
   ]
         ↓
6. 调用 API → 流式输出: "哇，程序员！平时主要用什么语言开发呀？"
         ↓
7. 维护短期记忆: recent_dialogue_queue.append((q, a))
         ↓
返回下一个问题

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

后台异步处理（当队列达到 10 条时）:

ProcessingAgent:
  qa_fact_cache_queue (10条)
         ↓
  调用 FACT_EXTRACTION
         ↓
  {"facts": [{"content": "我是一名程序员", "category": "职业"}]}
         ↓
  knowledge_base.add_facts([...])

StyleSummaryAgent:
  qa_style_cache_queue (10条)
         ↓
  调用 STYLE_EXTRACTION
         ↓
  {
    "oral_habits": [...],
    "style_observations": [...],
    "high_freq_words": {"程序员": 3, "开发": 2}
  }
         ↓
  oral_habits_base.add_habits([...])
  style_base.add_observations([...])
  oral_habits_base.update_word_frequency({...})
```

---

### 模拟模式完整流程

```
用户输入 "你平时喜欢做什么？"
         ↓
ImpersonationAgent.generate_response()
         ↓
1. 构建消息（使用缓存的系统消息）:
   [
     # 系统消息（初始化时缓存）
     {"role": "system", "content": 角色设定},
     {"role": "system", "content": 背景事实},
     {"role": "system", "content": 历史示例},

     # 最近对话历史
     ...

     # 当前输入
     {"role": "user", "content": "你平时喜欢做什么？"}
   ]
         ↓
2. 调用 API → 流式输出
         ↓
AI 回复（基于人格模型）:
  "我啊，平时喜欢写代码，其实吧（口头禅），
   看技术博客也是常事（行为习惯），
   周末的话（时间感知）会去健身房放松一下（周末行为）。"
         ↓
3. 维护短期记忆: recent_dialogue_queue.append((user_input, ai_response))
         ↓
返回 AI 回复
```

---

## 提示词工程

### 设计原则

1. **角色定位清晰**

   ```
   # 角色与核心任务：带着目标进行朋友式对话的采访者
   ```

2. **任务指令明确**

   ```
   --- 绝对执行指令 ---
   1. 唯一信息源：...
   2. 内容纯净度：...
   3. 仅输出 JSON：...
   ```

3. **约束条件严格**

   ```
   **重要：habit_type 必须且只能使用以上4个标准值之一**
   ```

4. **示例引导充分**

   ```
   以下是合格的 Content 示例：
   - 我叫李明，今年30岁
   - 我是一名软件工程师
   ```

5. **输出格式结构化**
   ```json
   {
     "facts": [...],
     "oral_habits": [...],
     "style_observations": [...]
   }
   ```

---

### 时间感知系统

#### 实现方式

```python
# 1. 获取北京时间
def get_beijing_time() -> str:
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    return f"{now.year}年{now.month}月{now.day}日 {weekday} {now.hour:02d}:{now.minute:02d}"

# 2. 格式化时间上下文
def format_time_context() -> str:
    time_str = get_beijing_time()
    return f"""【当前时间（北京时间）】
{time_str}

请根据这个时间感受当下的场景氛围。"""
```

#### 场景行为调整规则

**1. 周内/周末影响**

- 周一至周五：体现进度、紧迫感、计划性
- 周六日：体现闲适、自由、社交

**2. 季节影响**

- 自动识别月份
- 融入季节性元素（晚秋寒冷、年末总结）

**3. 时段情绪与语调**
| 时段 | 情绪特征 | 对话主题倾向 |
|------|---------|------------|
| 深夜 (22:00-05:00) | 沉静、思考 | 内在反思、放松、夜间活动 |
| 清晨 (05:00-09:00) | 清新、精力充沛 | 计划、新的一天 |
| 午后 (14:00-17:00) | 轻松、闲适 | 适度疲惫、休息 |
| 傍晚 (17:00-22:00) | 放松、总结 | 社交、一天回顾 |

---

### 知识边界控制（反编造）

**核心规则**：

```
你的全部知识来源仅限于你收到的所有 SYSTEM 消息。

如果 SYSTEM 消息中未包含的关于你自己的相关事实，
你必须诚实地回答："我不确定/我不太记得了"，
绝不推测或编造任何信息。

但全局性的客观知识（如自然科学知识），
可以根据角色的事实考虑怎么回答。
```

**实现效果**：

```
用户："你昨天去哪了？"
AI：  "我不太记得了，昨天的事情有点模糊。"
     （如果背景资料中没有昨天的信息）

用户："你会 Python 吗？"
AI：  "会的，我平时主要用 Python 做后端开发。"
     （如果背景资料中有相关事实）

用户："地球为什么是圆的？"
AI：  "这是因为重力作用，质量足够大的天体会在引力作用下形成球形..."
     （全局客观知识，可以回答）
```

---

## 技术栈

### 核心技术

| 技术        | 版本   | 用途         |
| ----------- | ------ | ------------ |
| Python      | 3.8+   | 主要开发语言 |
| asyncio     | stdlib | 异步编程     |
| OpenAI SDK  | latest | API 调用     |
| dataclasses | stdlib | 数据模型     |
| Queue       | stdlib | 进程间通信   |
| JSON        | stdlib | 数据序列化   |

### 外部依赖

```
openai==1.54.5              # API 客户端
python-dotenv==1.0.1        # 环境变量管理
```

### API 提供商

- **SiliconFlow API**
  - 端点: https://api.siliconflow.cn/v1
  - 模型: moonshotai/Kimi-K2-Instruct-0905
  - 兼容 OpenAI 接口

---

## 扩展性设计

### 1. 模块化架构

```
每个智能体独立运行
     ↓
通过队列松耦合
     ↓
可独立替换或升级
```

**优势**：

- 可以替换单个智能体而不影响其他
- 可以增加新的智能体（如情感分析、记忆检索等）
- 可以调整批处理大小和队列容量

---

### 2. 可插拔知识库

```python
class KnowledgeBase:
    def add_fact(self, ...): pass
    def get_all_facts(self): pass
    def to_dict(self): pass
```

**扩展方向**：

- 向量数据库（FAISS, Milvus）
- 图数据库（Neo4j）
- 关系数据库（PostgreSQL）

---

### 3. 多模型支持

```python
# 当前
model = "moonshotai/Kimi-K2-Instruct-0905"

# 可扩展
models = {
    "interview": "gpt-4",
    "processing": "gpt-3.5-turbo",
    "style": "claude-3-opus",
    "impersonation": "gpt-4"
}
```

---

### 4. 多语言支持

**当前架构已预留**：

- 提示词集中管理
- 可以添加语言参数
- 国际化提示词模板

```python
INTERVIEW_SYSTEM_EN = """..."""
INTERVIEW_SYSTEM_ZH = """..."""
```

---

### 5. 高级 RAG

**当前**：简单的事实检索

**可扩展**：

- 语义检索（向量相似度）
- 混合检索（关键词 + 语义）
- 重排序（Rerank）
- 上下文压缩

```python
# 未来扩展
def retrieve_relevant_facts(query, top_k=5):
    embeddings = get_embeddings(query)
    results = vector_db.search(embeddings, top_k)
    reranked = rerank_model.rerank(query, results)
    return reranked
```

---

### 6. 多人格管理

**当前**：单人格存储

**可扩展**：

- 人格对比分析
- 人格融合（综合多个人的特点）
- 人格演化追踪
- 人格关系图谱

---

### 7. API 网关化

**可扩展为 Web 服务**：

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/interview")
async def interview(user_input: str):
    response = await interview_agent.process_chat(user_input)
    return {"response": response}

@app.post("/impersonate")
async def impersonate(persona_name: str, user_input: str):
    response = await impersonation_agent.generate_response(user_input)
    return {"response": response}
```

---

## 性能优化

### 1. 批处理优化

- 10 条对话批量处理
- 减少 API 调用次数
- 提高吞吐量

### 2. 缓存策略

**系统消息缓存**：

```python
# ImpersonationAgent 初始化时缓存
self._cached_system_messages = self._build_system_messages()
```

**避免重复构建**，提升响应速度。

### 3. 异步并发

```python
# 后台任务并发运行
style_task = asyncio.create_task(style_summary_agent.run())
processing_agent.run()  # 同步批处理
```

### 4. 流式响应

```python
async for chunk in response_stream:
    print(chunk, end="", flush=True)
```

实时显示，提升用户体验。

---

## 安全性考虑

### 1. API Key 保护

```python
# 环境变量存储
SILICONFLOW_API_KEY=your-key-here

# 文件权限控制
chmod 600 .env
```

### 2. 输入验证

```python
# JSON 解析安全
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        return None
```

### 3. 知识边界

- 严格限制 AI 回答范围
- 防止信息编造
- 保护隐私数据

---

## 未来规划

### 短期（1-3 个月）

- [ ] 向量数据库集成（语义检索）
- [ ] Web UI 界面
- [ ] 多人格并行管理
- [ ] 性能监控和日志分析

### 中期（3-6 个月）

- [ ] 多模态支持（图片、语音）
- [ ] 实时流式对话 WebSocket
- [ ] 人格演化追踪
- [ ] API 网关和权限管理

### 长期（6-12 个月）

- [ ] 分布式部署
- [ ] 多语言支持
- [ ] 人格市场和分享
- [ ] 高级情感计算

---

## 总结

RE-DEMO 采用 **多智能体异步批处理架构**，通过：

1. **前后台分离**：实时交互 + 后台处理
2. **知识三元组**：事实 + 风格 + 语言习惯
3. **提示词工程**：结构化、可维护的提示词管理
4. **时间感知**：动态场景适配
5. **模块化设计**：高扩展性和可维护性

构建了一个 **高精度、可扩展、工程化** 的 AI 人格克隆系统。

---

**文档版本**: v1.0  
**最后更新**: 2025-11-21  
**维护者**: RE-DEMO Team
