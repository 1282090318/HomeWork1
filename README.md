CodeAgent —— 基于 LLM 的代码助手 Agent

课程作业 Homework 1：搭建一个简单的代码助手 Agent，掌握 Agent 开发的基础能力（LLM 调用、Prompt 设计、工具集成）。

CodeAgent 是一个轻量但完整的代码助手 Agent。它能够：
- 审查代码：静态分析 Python 代码，指出坏味道并给出改进建议
- 解释代码：解析代码结构，说明类/函数的职责与逻辑
- 执行代码：在受限沙箱中运行 Python 片段以验证想法
- 搜索代码：在代码库中按正则检索

项目零第三方依赖（仅用 Python 标准库），既可在配置 API Key 后由 LLM 自主推理调用工具，也能在无网络/无 Key 环境下通过内置规则引擎完整演示。

特性

| 特性 | 说明 |
|------|------|
| Agent 循环 | 输入 → 推理 → 工具调用 → 输出，支持多轮工具调用 |
| 工具集成 | 内置 read_file / list_dir / run_code / search_code 四种工具 |
| LLM 兼容 | 兼容任意 OpenAI 兼容接口（OpenAI / 通义千问 / 本地 Ollama 等） |
| 上下文记忆 | 对话历史保存在 Memory 中，支持多轮连续对话 |
| 离线降级 | 未配置 Key 时自动切换规则引擎，保证可用、可演示 |
| 错误处理 | 指数退避重试 + 工具异常兜底，不会因单次失败崩溃 |
| 零依赖 | 仅用标准库，克隆即可运行（Python ≥ 3.9） |
| 可测试 | 内置 unittest 单元测试 |

目录结构

CodeAgent/
├── codeagent/              # 核心包
│   ├── __init__.py
│   ├── client.py           # LLMClient：OpenAI 兼容接口封装（重试/超时）
│   ├── tools.py            # 工具集：read_file/list_dir/run_code/search_code
│   ├── agent.py            # Agent 循环 + 上下文记忆
│   ├── offline.py          # 离线规则引擎（代码审查/解释）
│   ├── prompts.py          # 提示词模板
│   └── cli.py              # 命令行入口
├── examples/
│   └── sample.py           # 演示用（带问题的）示例代码
├── tests/
│   └── test_tools.py       # 单元测试
├── main.py                 # 便捷入口
├── requirements.txt        # 依赖说明（无第三方依赖）
├── README.md               # 本文档
└── Design.md               # 设计文档

快速开始

1. 准备环境
   需要 Python 3.9+，无需安装任何第三方包。
   python --version

2. 离线模式（无需 API Key，开箱即用）
   cd CodeAgent
   python main.py test
   python main.py review examples/sample.py
   python main.py explain examples/sample.py
   python main.py search "def " examples
   python main.py run "print(sum(range(10)))"
   python main.py chat

3. 在线模式（启用 LLM 自主推理）
   任意 OpenAI 兼容接口均可，通过三个环境变量切换，无需修改代码：

   # Windows PowerShell（智谱 GLM 示例，本项目已实测）
   $env:OPENAI_API_KEY="你的智谱Key"
   $env:OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
   $env:OPENAI_MODEL="glm-5.3-flashx"
   python main.py chat

   # Linux / macOS
   export OPENAI_API_KEY="sk-xxxx"
   export OPENAI_BASE_URL="https://api.deepseek.com"
   export OPENAI_MODEL="deepseek-chat"
   python main.py chat

   常用服务商配置：
   | 服务 | OPENAI_BASE_URL | OPENAI_MODEL |
   |------|-----------------|--------------|
   | 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 | glm-5.3-flashx |
   | DeepSeek | https://api.deepseek.com | deepseek-chat |
   | OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
   | 本地 Ollama | http://localhost:11434/v1 | qwen2.5:7b |

   在线模式下，LLM 会自主决定调用哪些工具、调用几次，真正体现 Agent 的推理—行动循环；离线模式则使用内置规则引擎给出确定性的分析结果。

   如何确认真的接入了 AI：启动后不再显示“离线模式”提示；输入“审查 examples/sample.py”，
   回答能指出具体行号（说明它实际调用了 read_file），即为在线链路打通。

子命令一览

| 命令 | 作用 |
|------|------|
| chat | 交互式对话（在线/离线自动识别） |
| review <文件/目录> | 审查代码质量 |
| explain <文件> | 解释代码结构与逻辑 |
| search <正则> [路径] | 在代码中搜索 |
| run <代码> | 在沙箱中运行 Python 代码 |
| test | 运行内置自检示例 |

技术栈

- 语言：Python 3.9+
- LLM 接入：标准库 urllib 直接调用 OpenAI Chat Completions（含 function calling）
- 静态分析：标准库 ast / re
- 代码执行：标准库 subprocess（带超时，沙箱隔离）

完全满足作业「技术栈自由选择」要求，且刻意保持零依赖以最大化可移植性。

对应评审标准

| 评审维度 | 权重 | 本项目体现 |
|----------|------|-----------|
| 功能完整性 | 40% | 审查/解释/执行/搜索均可用，含边界处理 |
| Agent 架构 | 30% | 标准 推理→工具→输出 循环 + 上下文记忆 |
| 代码质量 | 20% | 模块化、类型提示、单元测试、错误兜底 |
| 文档 | 10% | README + Design.md + 代码注释 |

License

MIT —— 仅供课程作业与学习使用。
