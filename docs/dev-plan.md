# 开发执行计划 — Prompt Recorder

## 阶段总览

| 阶段 | 名称 | 依赖 | 预计产出 |
|------|------|------|---------|
| 0 | 项目初始化 | — | 目录骨架、规范文档 |
| 1 | 基础设施层 | 0 | 数据库、API 封装 |
| 2 | 服务层 | 1 | 分类、优化逻辑 |
| 3 | UI 基础窗口 | 2 | 主窗口、输入区 |
| 4 | UI 结果与历史 | 3 | 结果面板、历史列表、完整交互 |
| 5 | UI 设置与分类 | 4 | 设置对话框、分类管理 |
| 6 | 入口与收尾 | 5 | main.py、样式微调 |

## 阶段 0：项目初始化 ✓

- [x] 创建目录结构
- [x] requirements.txt
- [x] config.json 模板
- [x] docs/requirements.md
- [x] docs/tech-spec.md
- [x] docs/design-spec.md
- [x] docs/dev-plan.md
- [x] devlog/ 文件夹
- [x] CLAUDE.md

## 阶段 1：基础设施层

- [ ] `src/db/database.py` — SQLite 管理
- [ ] `src/api/deepseek_client.py` — API 封装
- [ ] 配置加载工具
- [ ] 验证脚本

## 阶段 2：服务层

- [ ] `src/services/categorizer.py`
- [ ] `src/services/optimizer.py`
- [ ] 验证脚本

## 阶段 3：UI 基础窗口

- [ ] `src/ui/theme.py`
- [ ] `src/ui/main_window.py`
- [ ] `src/ui/input_panel.py`

## 阶段 4：UI 结果与历史

- [ ] `src/ui/result_panel.py`
- [ ] `src/ui/history_panel.py`
- [ ] 完整交互链路串联

## 阶段 5：UI 设置与分类

- [ ] `src/ui/settings_dialog.py`
- [ ] `src/ui/category_manager.py`
- [ ] 优化开关降级流程

## 阶段 6：入口与收尾

- [ ] `main.py`
- [ ] 首次启动配置检查
- [ ] 整体样式微调
