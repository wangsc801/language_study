# language-learning-quiz

多语言"选词填空"出题服务：确定性工作（标注 / 选项洗牌 / 规则校验 / 存储）交给 Python，
LLM 只负责创作并返回精简 JSON，大幅降低 token 消耗、杜绝"正确答案全选 A"等问题。

目前内置 **日语** 引擎（动词变位），架构支持随时扩展更多语言。
架构设计见 [`specification/architecture.md`](specification/architecture.md)。

## 快速开始

```powershell
# 安装依赖
python -m pip install -e .

# 配置 LLM（OpenAI 兼容接口，如 DeepSeek / Ollama / vLLM）—— 两种方式二选一：
# ① 环境变量
$env:LLM_API_KEY = "sk-..."
$env:LLM_MODEL   = "gpt-4o-mini"          # 默认值
$env:LLM_BASE_URL = "https://api.openai.com/v1"
# ② 启动后打开 http://localhost:8000/settings 网页填写并保存

# 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 主要接口（`{lang}` 为语言代码，如 `ja`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 存活检查 |
| GET | `/settings` | LLM 配置前端页面（API Key / Base URL / 模型，含保存、重置、测试连接） |
| GET | `/api/settings` | 查看当前 LLM 配置（Key 已掩码） |
| POST | `/api/settings` | 更新 LLM 配置（`save:true` 时持久化到 `data/llm_settings.json`） |
| POST | `/api/settings/reset` | 重置为环境变量默认值 |
| POST | `/api/settings/test` | 用当前配置测试一次 LLM 连接 |
| POST | `/api/{lang}/quiz/generate` | 生成一批题目（默认 5 道，自动避开历史高频 Top-20 动词） |
| GET | `/api/{lang}/verbs/frequent` | 历史高频词（`since_days` 可选时间窗） |
| GET | `/api/{lang}/quiz/history` | 历史题目（分页） |
| GET | `/api/{lang}/quiz/{id}` | 单题详情 |

生成请求示例：

```jsonc
POST /api/ja/quiz/generate
{ "num_questions": 5, "avoid_verbs": ["する", "食べる"] }   // avoid_verbs 可选；也可省略用 auto_exclude(默认20)

// 响应
{ "batch_id": "……", "questions": [ {
    "category": "五段动词",
    "type": "鼻音便",
    "verb": "遊ぶ",
    "verbFurigana": "遊(あそ)ぶ",
    "sentence": "友達と遊んでから、家に帰ります。",
    "sentenceFurigana": "友達(ともだち)と遊(あそ)んでから、家(いえ)に帰(かえ)ります。",
    "sentenceQuiz": "友達(ともだち)と_____から、家(いえ)に帰(かえ)ります。",
    "translation": "和朋友玩完就回家。",
    "rightAnswer": "遊んで",
    "incorrectAnswers": ["遊って", "遊びて", "遊いて"],
    "options": ["遊びて", "遊んで", "遊いて", "遊って"],   // Python 已洗牌
    "optionsFurigana": ["遊(あそ)びて", "遊(あそ)んで", "遊(ゆー)いて", "遊(ゆー)って"],
    "answerPosition": 2                                  // 1-based
} ] }
```

批改（阶段二）在 OpenClaw 侧完成：直接比对该 JSON 中的 `rightAnswer`/`options`，无需再消耗 LLM token。

## 目录结构

```
language_learning_quiz/
├── main.py                 # FastAPI 入口（uvicorn main:app）
├── app/
│   ├── config.py           # 环境默认配置（LLM 默认值、DB 路径）
│   ├── schemas.py          # 通用 Pydantic 模型（语言无关）
│   ├── llm.py              # 通用 OpenAI 兼容 client
│   ├── database.py         # SQLite（含 language 列，按语言过滤）
│   ├── engines/
│   │   ├── base.py         # LanguageEngine 抽象基类
│   │   ├── __init__.py     # REGISTRY + get_engine(code)（加新语言=注册一行）
│   │   └── japanese/       # 日语引擎：prompt / furigana / 校验规则 / 字面量
│   ├── services/
│   │   ├── quiz_service.py # 通用出题流水线（编排引擎）
│   │   └── runtime_settings.py  # 运行时 LLM 配置 + 持久化
│   ├── routers/
│   │   ├── quiz.py         # /api/{lang}/quiz/...
│   │   ├── verbs.py        # /api/{lang}/verbs/frequent
│   │   └── settings.py     # /api/settings...
│   └── static/settings.html# LLM 配置前端页面
├── tests/                  # test_furigana / test_quiz
├── scripts/smoke_e2e.py    # 用桩 LLM 跑通整条流水线
├── specification/          # 设计文档
├── data/                   # SQLite + llm_settings.json（gitignore）
└── pyproject.toml
```

## 扩展一门新语言（日语为范例）

1. 在 `app/engines/` 下新建包（如 `chinese/`），实现 `LanguageEngine`：
   - `build_messages`：定义出题 prompt
   - `validate_raw`：自己的字面量/构成规则校验
   - `enrich`：自己的标注逻辑（如拼音）+ 洗牌
2. 在 `app/engines/__init__.py` 注册一行：`"zh": ChineseLanguageEngine`。

通用基础设施（LLM client、DB、HTTP 路由、设置页）无需改动。

## 测试与校验

```powershell
python -m pytest -q
python -m ruff check .
python -W ignore scripts\smoke_e2e.py   # 用桩 LLM 跑通整条流水线（需 PYTHONPATH=.）
```

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | 空 | LLM API Key |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容端点 |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名 |
| `LLM_TIMEOUT` | `60` | 单次请求超时（秒） |
| `LLM_JSON_MODE` | `true` | 是否发送 `response_format` |
| `DB_PATH` | `data/quizzes.db` | SQLite 路径 |
| `SETTINGS_DIR` | `data` | 运行时设置文件所在目录 |

### 运行时设置（`/settings` 页面）

页面填写后保存的配置写入 `data/llm_settings.json`（已加入 `.gitignore`），优先于环境变量；
点"重置为环境变量"会删除该文件、回退到环境变量默认值。API Key 不会出现在 GET 响应中，仅展示末 4 位。