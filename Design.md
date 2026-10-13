CodeAgent 设计文档（Design）

课程作业 Homework 1 —— 搭建一个简单的代码助手 Agent

本文档说明 CodeAgent 的设计目标、总体架构、关键模块设计与技术决策，可作为项目说明与评审参考。

1. 设计目标

- 掌握 Agent 开发基础能力：LLM 调用、Prompt 设计、工具集成
- 实现一个可运行的 Agent 循环：输入 → 推理 → 工具调用 → 输出
- 至少集成一种工具，并提供命令行交互方式
- 具备上下文记忆、错误处理与重试等工程化能力
- 在无 API Key / 无网络的环境下依然可演示、可评分（离线降级）

2. 总体架构

┌──────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                      │
│    chat / review / explain / search / run / test          │
└───────────────┬──────────────────────────────────────────┘
                │  构建并编排组件
                ↓
┌──────────────────────────────────────────────────────────┐
│                      CodeAgent (agent.py)                 │
│   ┌────────────┐   Agent 循环    ┌────────────────────┐  │
│   │  Memory    │── 消息上下文 ──→│  LLMClient         │  │
│   │ (上下文记忆)│                 │ (推理/工具决策)     │  │
│   └────────────┘                 └─────────┬──────────┘  │
│                                           │ tool_calls   │
│                                           ↓              │
│                                ┌────────────────────┐    │
│                                │  ToolRegistry      │    │
│                                │ (read/list/run/    │    │
│                                │  search)           │    │
│                                └────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                │ 无 Key 时
                ↓
┌──────────────────────────────────────────────────────────┐
│                  OfflineEngine (offline.py)               │
│   基于 ast 的规则引擎：代码审查 / 代码解释 / 工具复用      │
└──────────────────────────────────────────────────────────┘

3. 核心模块设计

3.1 LLMClient（client.py）
- 使用标准库 urllib 直接 POST 到 ${BASE_URL}/chat/completions
- 支持 tools（function calling）参数，让模型自主选择工具
- 重试机制：指数退避（1s → 2s → 4s → 8s 封顶），覆盖网络抖动与 5xx
- 超时控制：timeout 默认 60s，避免无限等待
- 可用判断：available 属性根据是否存在 API Key 决定走在线还是离线

3.2 工具集（tools.py）
每个工具封装为 Tool(name, description, parameters, func)，同时提供：
- 给 LLM 的 JSON Schema 描述（schema）
- 本地执行函数（execute，内部异常被捕获并返回错误文本，避免 Agent 崩溃）

内置工具：
| 工具 | 作用 | 对应作业要求 |
|------|------|------------|
| read_file | 读取源码 | 工具集成 |
| list_dir | 列举目录 | 工具集成 |
| run_code | 沙箱执行 Python（超时 10s） | 工具集成 / 代码执行 |
| search_code | 正则检索代码库 | 工具集成 / 搜索 |

3.3 Agent 循环（agent.py）
循环逻辑（max_iter 上限保护）：
1. 用户输入写入 Memory
2. 携带 Memory + 工具 schema 调用 LLMClient.chat
3. 若返回 tool_calls：将「助手的工具调用意图」与「工具执行结果」分别写入 Memory，回到步骤 2
4. 若返回纯文本：作为最终答复返回

上下文记忆（Memory）：维护 system/user/assistant/tool 四类消息，支持多轮对话；超过 max_messages 时保留 system 并截断最旧消息，控制 token 成本。

3.4 离线规则引擎（offline.py）
- 当无 API Key 时，CodeAgent.run 自动委派给 OfflineEngine.dispatch
- 基于 Python ast 做静态分析：
  - 审查：函数规模、缺失 docstring、裸 except、使用 eval/exec、硬编码密钥、TODO 标记
  - 解释：解析模块说明、导入、类/方法、函数签名与文档
- 复用同一套 ToolRegistry 完成搜索与执行，保证一致性

4. 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| LLM 接入方式 | 标准库 urllib 直连 OpenAI 兼容接口 | 零第三方依赖，克隆即运行，兼容性最好 |
| 工具调用协议 | 标准 function calling | 模型原生支持，结构化参数解析可靠 |
| 离线兜底 | ast 规则引擎 | 无 Key 也能演示「审查/解释」方向，可评分 |
| 代码执行 | subprocess + 超时 | 隔离主进程、防止死循环卡死 |
| 重试 | 指数退避 | 提升对网络/限流的鲁棒性 |

5. 错误处理与重试

- LLM 调用层：网络异常、HTTP 错误、JSON 解析失败时按指数退避重试，全部失败抛出 LLMError
- 工具层：工具内部异常被 Tool.execute 捕获，转换为错误文本回传模型，由模型决定下一步
- Agent 层：顶层 try/except 保证单次错误不会终止交互式会话；max_iter 防止无限循环

6. 扩展方向

- 增加更多工具（git_diff、web_search、unit_test_gen）
- 接入向量检索做仓库级代码问答（RAG）
- 替换 LLMClient 为流式（SSE）实现以支持打字机效果
- 复用现有 Tool 抽象接入 AutoGen / LangChain 等框架

7. 使用方法（速查）

cd CodeAgent
python main.py test
python main.py review examples/sample.py
python main.py explain examples/sample.py
python main.py chat

export OPENAI_API_KEY="sk-xxxx"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
python main.py chat

详见 README.md。
