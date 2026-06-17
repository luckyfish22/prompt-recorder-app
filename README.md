# Prompt Recorder

> 本地优先的 Prompt 管理利器 —— 分类整理、拖拽排序、AI 智能优化，让每一次提示词都值得复用。

本工具全流程基于 Claude Code（AI Agent）辅助开发。

---

## ✨ 功能

- **📝 Prompt 捕获** —— 随手记录，自动保存到本地 SQLite 数据库
- **📂 分类管理** —— 树形文件夹，支持拖拽移动和嵌套子文件夹
- **🤖 AI 优化润色** —— 集成 DeepSeek API，一键优化 Prompt 的清晰度和结构
- **🏷️ 自动标题** —— AI 根据内容自动生成简洁标题（限 20 字）
- **🖱️ 拖拽排序** —— 提示词和文件夹均支持拖拽重排
- **🪟 悬浮窗** —— 始终置顶的迷你窗口，支持中英互译和命令行关键词解释
- **🔍 快速检索** —— 搜索历史 Prompt，一键复制复用
- **⚙️ 系统驻留** —— 启动后最小化到系统托盘，全局热键呼出

---

## 🛠 技术栈

| 层面 | 技术 |
|------|------|
| GUI 框架 | PyQt5 |
| 数据库 | SQLite |
| AI 接口 | DeepSeek API（兼容 OpenAI SDK） |
| 打包 | Python 原生（`pythonw main.py` 无控制台窗口） |

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（可选，不配也能用基础功能）
# 在 src/api/ 下创建 .env 文件：
#   DEEPSEEK_API_KEY=your_key_here
#   DEEPSEEK_BASE_URL=https://api.deepseek.com

# 3. 启动
python main.py
```

启动后窗口最小化到系统托盘，左键点托盘图标呼出悬浮窗，右键打开菜单。

---

## 📁 项目结构

```
prompt_recorder/
├── main.py                   # 入口：系统托盘、单实例锁、主窗口
├── requirements.txt
├── src/
│   ├── api/
│   │   └── deepseek_client.py   # DeepSeek API 封装
│   ├── db/
│   │   └── database.py          # SQLite CRUD
│   ├── services/
│   │   └── optimizer.py         # AI 优化 / 分类 / 标题生成
│   ├── ui/
│   │   ├── main_window.py       # 主窗口
│   │   ├── floating_window.py   # 悬浮窗
│   │   ├── folder_tree.py       # 文件夹树形侧边栏
│   │   ├── history_panel.py     # 历史 Prompt 列表
│   │   ├── analysis_dialog.py   # AI 优化结果弹窗
│   │   ├── settings_dialog.py   # 设置窗口
│   │   └── theme.py             # 全局配色与字体
│   └── config_loader.py         # 配置文件读写
└── docs/
    ├── requirements.md           # 功能需求文档
    ├── tech-spec.md              # 技术架构文档
    └── design-spec.md            # UI 设计规范
```

---

## 💡 开发背景

我日常重度使用 AI Agent 开发，发现 Prompt 管理存在三个痛点：

1. 好的 Prompt 写了就丢，下次找不到
2. Prompt 可以优化但懒得反复润色
3. 切换工具窗口打断了工作流

于是用 Claude Code 全流程 vibe coding 开发了这个工具。所有功能都围绕「不打断工作流」设计 —— 悬浮窗、系统托盘、全局热键，都是在实际使用中迭代出来的。

---

## 📌 备注

- 本仓库为个人开源作品，欢迎提 Issue 交流
- 属于 [AI Agent 开发工具体系](https://github.com/luckyfish22/AI-toolkit) 的一部分
