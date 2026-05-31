# CLAUDE.md — Prompt Recorder 项目指引

## 项目简介

一款 Windows 桌面工具，用于记录和管理提示词。对接 DeepSeek API，自动分类和优化提示词。Python + PyQt6 + SQLite。

## 规范文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) | 完整功能需求 |
| 技术规范 | [docs/tech-spec.md](docs/tech-spec.md) | 技术栈、架构、API 对接方式 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | 配色、布局、字体、交互规范 |
| 开发计划 | [docs/dev-plan.md](docs/dev-plan.md) | 分阶段执行计划与进度 |
| 配置文件 | [config.json](config.json) | API Key、模型、分类、开关 |
| 开发日志 | [devlog/](devlog/) | 每天自动记录完成/待办事项 |

## 工作约定

1. **分阶段推进**：严格按照 dev-plan.md 的阶段顺序执行，每个阶段独立可验证，完成后需用户确认再进入下一阶段
2. **先读规范再写代码**：修改任何代码前，先确认需求文档和技术规范
3. **保持扩展性**：服务层与 UI 解耦，配置驱动，不写死逻辑
4. **开发日志**：每次会话结束时更新 devlog/YYYY-MM-DD.md
5. **颜色/样式**：严格使用 design-spec.md 中定义的配色和间距，保持 Claude 风格一致
6. **不要过度设计**：只实现当前阶段和已规划的需求，不为未确认的需求预留代码

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py
```
