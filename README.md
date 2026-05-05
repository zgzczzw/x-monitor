# X Monitor —— X/Twitter 博主推文监控

实时监控指定 X（Twitter）博主的新推文，自动翻译并通过 Bark 推送到 iPhone。

![界面预览](https://img.shields.io/badge/Vue3-前端-42b883) ![FastAPI](https://img.shields.io/badge/FastAPI-后端-009688) ![SQLite](https://img.shields.io/badge/SQLite-存储-003b57)

## 功能

- **博主监控**：添加任意数量的 X 博主，定时拉取最新推文
- **增量采集**：记录每个博主的最新 Tweet ID，只处理真正的新推文，不会重复推送
- **自动翻译**：集成 MyMemory 免费翻译接口，推文原文 + 中文对照展示
- **Bark 推送**：新推文实时推送到 iPhone（支持配置多个设备）
- **可视化管理**：Web 界面管理博主列表、Bark 设备、采集间隔、时区等配置

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · APScheduler · SQLite |
| 前端 | Vue 3 · Element Plus · Vite |
| 推文数据 | [twitterapi.io](https://twitterapi.io) |
| 翻译 | [MyMemory](https://mymemory.translated.net)（免费，无需 Key）|
| 推送 | [Bark](https://bark.day.app)（iOS）|

## 快速开始

### 1. 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 13002
```

### 2. 前端（构建后由后端托管，无需单独启动）

```bash
cd frontend
npm install
npm run build
```

构建产物在 `frontend/dist/`，FastAPI 启动后自动托管，访问 `http://localhost:13002` 即可。

## 配置

所有配置均在 Web 界面「系统设置」页完成，无需修改文件：

| 配置项 | 说明 |
|--------|------|
| Twitter API Key | 在 [twitterapi.io](https://twitterapi.io) 申请，约 $0.15/1k 条 |
| 监控博主 | 在「博主监控」页添加/删除，支持任意数量 |
| Bark 设备 | 支持多设备，打开 Bark App 复制 Key |
| 采集间隔 | 1～60 分钟可调，默认 5 分钟 |
| 时区 | 影响推文时间显示，默认 Asia/Shanghai |

## 推送格式

```
标题：@elonmusk 发了新推文
内容：This is the original tweet text...

🀄 这是推文的中文翻译内容...
```

## 目录结构

```
├── backend/
│   ├── collectors/       # 推文采集
│   ├── routers/          # API 路由
│   ├── services/         # Bark 推送、翻译
│   ├── main.py           # 入口，同时托管前端静态文件
│   ├── scheduler.py      # 定时采集调度
│   └── models.py         # 数据库模型
└── frontend/
    └── src/
        ├── views/        # 页面：博主监控、系统设置
        ├── api/          # API 调用封装
        └── lib/          # 时区工具
```

## 注意事项

- API Key、Bark Device Key 等敏感信息存储在 SQLite 数据库中，不在代码里，`.db` 文件已加入 `.gitignore`
- twitterapi.io 无 Webhook 推送（需单独订阅），目前采用轮询方式
- MyMemory 免费翻译每日 1000 次，填写邮箱可提升至 10000 次

## License

MIT
