### 一、核心架构总览

系统被重构为一个多智能体、异步处理的架构，以实现流畅的对话和高效的信息提炼。

#### 1. 核心阶段

1. **采访阶段 (Interview Phase)** ：专职对话的智能体与“人类 A”进行流畅的多轮对话，同时后台异步提炼事实、性格和风格库。
2. **扮演阶段 (Impression Phase)** ：加载所有知识库，由另一个智能体模拟“人类 A”与“人类 B”对话。

#### 2. 核心智能体

1. **采访智能体 (InterviewAgent)** ：负责阶段一，主动与人类 A 对话，保持互动流畅性，并具备策略性提问能力。
2. **信息处理智能体 (ProcessingAgent)** ：(后台异步) 负责阶段一，持续从对话中 **只提炼事实** 。
3. **风格总结智能体 (StyleSummaryAgent)** ：(后台异步)负责阶段一，持续从对话中 **只**进行风格总结。
4. **对话扮演智能体 (ImpersonationAgent)** ：负责阶段二，模拟人类 A 进行对话。

#### 3. 核心数据结构

- `history`: `list[str]`。 **只存储人类 A 的完整回答历史** 。
- `knowledge_base`: `KnowledgeBase` 实例。用于存储提炼出的结构化 **事实** 。
- `qa_cache_queue`: `Queue[tuple(str, str)]`。 **问答对话缓存队列** ，用于异步信息整理。
- `recent_dialogue_queue`: `deque[tuple(str, str)]` (max_len=20)。 **最近对话队列** ，用于保持对话流畅。
- `style_base`: `StyleBase` 实例。存储核心性格与价值观 (由 `StyleSummaryAgent` 生成)。
- `oral_habits_base`: `OralHabitsBase` 实例。存储语言习惯库，如口头禅、句式 (由 `StyleSummaryAgent` 生成)。

### 二、阶段一：采访与信息处理 (异步并行)

采访（前台）和事实处理（后台）同时发生。

#### 模块 2.1：采访智能体 (InterviewAgent) - 前台交互

**职责** ：与人类 A 保持自然、流畅、有策略的对话，主动拓宽话题范围。

**关键属性** ：

- `system_prompt`：一个专门用于“策略性采访”的系统提示词。

  - _示例_ ：“你是一个专业采访者。你已经知道了以下信息：[已经获得的事实]。请基于这些已知信息和最近的对话，去探索一些**新的**或者**尚未深入**的领域。”

- `recent_dialogue_queue`：(输入) 作为调用 AI 时的 `messages` 短期记忆。
- `knowledge_base`：(输入) 用于轻量级 RAG，辅助策略性提问。
- `qa_fact_cache_queue`：(输出) 将完成的对话发送到此队列等待处理。
- `qa_style_cache_queue`：(输出) 将完成的对话发送到此队列等待处理。
- `history`：(输出) 将人类 A 的回答存入此列表。

  **交互接口 (方法)** ：

- `process_chat(self, user_answer: str) -> str`：

  - 功能：核心的对话交互。
  - 输入：人类 A 对上一个问题的回答。
  - **中间过程** ：

  1. 获取 AI 的上一个问题 `last_ai_question`。
  2. **存入 History** ：将 `user_answer` 添加到 `history` 列表。
  3. **存入缓存队列** ：将 (`last_ai_question`, `user_answer`) 放入 `qa_fact_cache_queue`,` qa_style_cache_queue`。
  4. **维护短期记忆** ：将 (`last_ai_question`, `user_answer`) 放入 `recent_dialogue_queue`。
  5. **策略性提问) ：**从 `knowledge_base` 中**获得**已知事实 (例如: "已知信息: [事实 1, 事实 2]")。
  6. **调用 API** ：将 `system_prompt`、`检索到的已知事实` 和 `recent_dialogue_queue` (作为 message 历史) 发送给 AI API。
  7. **AI 任务** ：AI 的唯一任务是根据上下文，生成一个自然的“下一个问题”。

  - 输出：AI 生成的“下一个问题”。

#### 模块 2.2：信息处理智能体 (ProcessingAgent) - 后台异步

**职责** ：作为后台服务运行，持续监控 `qa_fact_cache_queue`， **每累计 10 个对话** ，就批量提炼一次 **客观事实** 。

**关键属性** ：

- `qa_fact_cache_queue`：(输入) 从此队列获取待处理的对话。
- `knowledge_base`：(输出) 存入提炼出的事实。
- `fact_extraction_prompt`：一个专门用于“从对话中提炼事实”的系统提示词。

  **工作流程 (批量异步循环)** ：

1. (后台) 检查 `qa_fact_cache_queue` 中的 Q&A 对数量是否达到 10。
2. **若未达到** ：保持等待 (例如短暂 `sleep` 后继续检查)。
3. **若达到 10 个** ：
   a. 从队列中安全地取出 10 个 (`ai_question`, `user_answer`) 对话，组成 `fact_batch`。
   b. 调用 AI API，使用 `fact_extraction_prompt` 指示 AI 仅从 `fact_batch` 中提炼所有“事实”。
4. 将返回的“事实”**追加**存入 `knowledge_base`。
5. 返回步骤 1，等待下一个 10 个。

#### 模块 2.3：风格总结智能体 (StyleSummaryAgent) - 后台异步

**职责** ：作为后台服务运行，持续监控 `qa_style_cache_queue`。 **每累计 10 个对话** ，就批量提炼一次“ **微观风格和习惯** ”。

**关键属性** ：

- `qa_style_cache_queue`：(输入) 从此队列获取待处理的对话。
- `oral_habits_base`：(输出) **增量存入**提炼出的语言习惯。
- `style_base`：(输出) **增量存入**“风格观察”记录。
- `style_extraction_prompt`：一个专门用于“从批量对话中提炼风格和习惯”的系统提示词。

  **工作流程 (批量异步循环)** ：

1. (后台) 检查 `qa_style_cache_queue` 中的 Q&A 对数量是否达到 10。
2. **若未达到** ：保持等待。
3. **若达到 10 个** ：
   a. 从队列中安全地取出 10 个 (`ai_question`, `user_answer`) 对话，组成 `style_batch`。
   b. 调用 AI API，使用 `style_extraction_prompt` 指示 AI 从 `style_batch` 中：
   i. **AI 任务 (A)** ：提炼语言习惯 (如高频词、口头禅、句式、语气词)。
   ii. **AI 任务 (B)** ：提炼人物性格、价值观 ，还有情绪色彩(如：“在谈论[话题 X]时，表现出[情绪 Y]”)。
4. 将 (A) 的结果**追加**存入 `oral_habits_base`。
5. 将 (B) 的结果**追加**存入 `style_base` 。
6. 返回步骤 1，等待下一个 10 个。

### 四、阶段二：对话扮演智能体 (ImpersonationAgent)

加载阶段一和阶段二生成的所有知识库，负责模拟人类 A 与人类 B 对话。

**关键属性** ：

- `knowledge_base`：(输入) 阶段一填充完毕的**事实**知识库。
- `style_base`：(输入) 阶段二生成的**性格与风格**知识库。
- `oral_habits_base`：(输入) 阶段二生成的**语言习惯**库。
- `recent_dialogue_queue`：(内部维护) 存储与人类 B 的最近 20 条对话。
- `system_prompt`：一个专门用于“角色扮演”的系统提示词。
- **如果 history 中 QA 小于 50，则要送入 history 来辅助回答**

  **交互接口 (方法)** ：

- `__init__(self, knowledge_base, style_base, oral_habits_base)`：

  - 加载所有必需的数据源。

    - - `generate_response(self, user_input_b: str) -> str`：
      - 功能：模拟人类 A 回复人类 B。
      - 输入：人类 B 的一句话。
      - **中间过程** ：

      1. **信息检索 (RAG)** ：完整送入 `knowledge_base `的事实。
      2. **风格加载** ：完整送入 `style_base` 加载核心性格描述。
      3. **习惯加载** ：从 `oral_habits_base` 加载语言习惯（口头禅等）。
      4. **记忆维护** ：将 (AI 上句, `user_input_b`) 存入 `recent_dialogue_queue`。
      5. **构建 Prompt** ：
         - **System Prompt (性格)** : [从 `style_base` 加载”]
         - **System Prompt (语言风格)** : [从 `oral_habits_base` 加载，例如：“你说话时，经常使用[‘其实’、‘然后’]，喜欢用[短句]。”]
         - **背景资料 (Facts)** : [从 `knowledge_base` 加载]。
         - **最近对话 (Memory)** : [来自 `recent_dialogue_queue` 的内容]。
         - 如果 history 中 QA 小于 50，则要送入 history 来辅助回答
      6. 调用 AI API，严格基于以上信息进行回复。

      - 输出：AI 扮演人类 A 的回复。

### 五、附录：知识库持久化与管理 (V1.0 - 文本存储)

本部分规定了知识库（KB）在现阶段（V1.0）的本地存储、加载和管理要求。

#### 1. 存储格式

- **格式** ：所有知识库 (`knowledge_base`, `style_base`, `oral_habits_base`) 均以**JSON 文本文件**的形式存储在本地。
- **结构** ：
- 每个“人物”对应一个专属文件夹（例如 `./personas/zhangsan/`）。
- 文件夹内包含：`facts.json` (对应 `knowledge_base`), `style.json` (对应 `style_base`), `habits.json` (对应 `oral_habits_base`)。
- `history` 作为一个原始语料库，也应被保存为 `history.txt`。

#### 2. 程序启动流程

- 程序启动时，系统应自动扫描本地的“人物”文件夹（如 `./personas/`）。
- 向用户显示一个 **已存在的人物知识库列表** 。
- 用户必须做出选择：
- **(A) 加载已有知识库** ：
- 用户从列表中选择一个“人物”（例如 "zhangsan"）。
- 程序读取该人物文件夹下所有的 `.json` 和 `.txt` 文件，将其内容解析并加载到内存中对应的知识库实例。
- **(B) 新建知识库** ：
- 用户输入一个新“人物”的名称（例如 "lisi"）。
- 程序在内存中初始化一套全新的、空的知识库实例，并准备好新的存储路径（如 `./personas/lisi/`）。

#### 3. 程序结束与保存

- 在采访阶段或扮演阶段结束，退出程序时，系统必须处理数据保存。
- 如果内存中的知识库相比上次加载时 **发生了更改** （例如，`InterviewAgent` 收集了新事实或 `StyleSummaryAgent` 刚运行完毕）：
- 系统应**主动询问**用户：“知识库已更新，是否保存对 [人物名称] 的更改？”
- **用户选择“是”** ：程序将内存中所有知识库实例序列化为 JSON/Text，并**覆盖**保存到对应的本地文件中。
- **用户选择“否”** ：本次运行中产生的新数据将被 **丢弃** ，本地文件保持不变。

#### 4. 知识库管理

- 程序应提供一个简单的管理功能（可在启动流程中实现）。
- 用户应能够选择一个已存在的知识库，并执行**删除**操作。
- **安全要求** ：删除操作必须有 **二次弹窗确认** （例如：“您确定要永久删除 [人物名称] 的所有数据吗？此操作不可撤销。”），以防止误删。

### 六、附录：API 集成规范与请求模板 (修正版)

本部分合并并取代了原附录 6 和 7，提供了基于 SiliconFlow API (兼容 OpenAI) 的统一规范与 Python 请求模板。

#### 1. 通用规范

- **模型** ：统一使用 `moonshotai/Kimi-K2-Instruct-0905`。
- **集成** ：所有 API 调用**必须**使用异步 I/O (Async I/O) 模式发起。
- **初始化模板** ：

```
from openai import AsyncOpenAI
# 客户端初始化 (全局一次)
client = AsyncOpenAI(
    api_key="sk-kxojlpqqivfrqpfnirsbimqwarggbshfxpozmahykaxuepnl",
    base_url="https://api.siliconflow.cn/v1"
)
```

- **请求模板** ：

```
response_stream = await client.chat.completions.create(
    model="moonshotai/Kimi-K2-Instruct-0905",
    messages=[{
        {"role": "system", "content": "（模型指令，设定AI角色，描述模型应一般如何行为和响应）"},
        {"role": "user", "content": "（用户输入，将最终用户的消息传递给模型）"},
        {"role": "assistant", "content": "（模型生成的历史回复，为模型提供示例，说明它应该如何回应当前请求）"}
    }],
    max_tokens=输出限制
    temperature=创造力,
    stream=是否流式
)
```

#### 2. 类型一：实时对话智能体 (InterviewAgent, ImpersonationAgent)

**目标** ：低延迟、高拟人性、流式+情绪。

**规范** ：

- **`temperature`** : `0.7 - 0.9` (高随机性)。
- **`stream`** : `true` (强制流式，联动 TTS)。
- **`max_tokens`** : `200 - 500` (保持互动节奏)。

#### 3. 类型二：后台分析智能体 (ProcessingAgent, CompressionAgent)

**目标** ：高准确性、低随机性、结果可控。

**规范** ：

- **`temperature`** : `0.1 - 0.4` (低随机性，保证事实准确)。
- **`stream`** : `false` (非流式，一次性获取完整 JSON)。
- **`max_tokens`** : `1000 - 4000` (给予足够分析空间)。

#### 4. 类型三：一次性总结智能体 (StyleSummaryAgent)

**目标** ：宏观总结、高分析力、中等创造力。

**规范** ：

- **`temperature`** : `0.7` (中等随机性，用于归纳性格)。
- **`stream`** : `false` (非流式，等待完整总结)。
- **`max_tokens`** : `4000+` (或更大，上下文庞大)。

```

```

```

```
