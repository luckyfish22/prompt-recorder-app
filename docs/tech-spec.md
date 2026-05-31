# 技术规范 — Prompt Recorder

## 技术栈

| 层面 | 技术 | 版本要求 |
|------|------|---------|
| 语言 | Python | >= 3.10 |
| GUI | PyQt6 | >= 6.5.0 |
| AI SDK | openai | >= 1.0.0 |
| 数据库 | SQLite3 | 内置 |
| 配置 | JSON | 内置 |

## DeepSeek API 对接

- **接口地址**：`https://api.deepseek.com/v1`
- **SDK 方式**：使用 `openai` Python SDK，设置 `base_url` 指向 DeepSeek
- **调用模型**：默认 `deepseek-chat`
- **认证**：API Key 通过 `config.json` 读取

```python
from openai import OpenAI

client = OpenAI(
    api_key="<api_key>",
    base_url="https://api.deepseek.com/v1"
)
```

## 数据库

- **引擎**：SQLite3（Python 内置 `sqlite3` 模块）
- **文件位置**：项目根目录 `prompts.db`
- **编码**：UTF-8

### 表结构

```sql
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT NOT NULL,
    optimized_text TEXT,
    category_id INTEGER,
    is_optimized INTEGER DEFAULT 0,
    optimization_note TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category_id);
CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at DESC);
```

## 项目架构

```
main.py (入口)
  └─ src/app.py (应用初始化)
       ├─ src/db/database.py (数据层)
       ├─ src/api/deepseek_client.py (API 层)
       ├─ src/services/categorizer.py (分类服务)
       ├─ src/services/optimizer.py (优化服务)
       └─ src/ui/ (UI 层)
            ├─ main_window.py
            ├─ input_panel.py
            ├─ result_panel.py
            ├─ history_panel.py
            ├─ settings_dialog.py
            └─ category_manager.py
```

## 数据流

1. `input_panel` 接收用户输入 → 发出信号
2. `main_window` 接收信号 → 调用 `categorizer.classify()` → 调用 `optimizer.optimize()`（若开启）
3. 服务层通过 `deepseek_client` 调用 API
4. 结果回传 `main_window` → 更新 `result_panel`
5. 用户确认后 → `database.save_prompt()` → 刷新 `history_panel`

## 配置管理

- 配置类负责读写 `config.json`
- 启动时加载到内存，设置变更时即时写回
- 提供 `get(key)` / `set(key, value)` 接口
