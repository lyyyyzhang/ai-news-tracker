[README.md](https://github.com/user-attachments/files/26154051/README.md)
# 🚀 AI 产品动态看板

> 实时追踪国内外 AI 产品动态，硅谷一线 + 国内主流媒体双栏展示。

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Deploy](https://img.shields.io/badge/Deploy-Railway-purple)

---

## 📸 功能预览

- 🌐 **硅谷动态**：实时抓取 OpenAI、Huggingface、Google AI 官方博客
- 🇨🇳 **国内动态**：36氪 AI、机器之心、量子位
- 🔍 **全文搜索**：标题 + 描述实时过滤
- 🏷️ **重要度标注**：自动识别重磅发布，高亮展示
- 🌙 **深色模式**：支持亮色 / 暗色主题切换
- 🔄 **自动刷新**：后端每 30 分钟自动抓取一次，无需手动操作

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 标准库（无需额外安装依赖） |
| 前端 | 原生 HTML + CSS + JavaScript |
| 数据源 | RSS / Atom Feed |
| 部署 | Railway（免费套餐） |

---

## 📁 项目结构

```
ai-tracker/
├── server.py        # 后端服务器：RSS 抓取 + API + 静态文件托管
├── index.html       # 前端页面：新闻看板 UI
├── Procfile         # Railway 部署启动命令
└── requirements.txt # Python 依赖（标准库，内容为空）
```

---

## 🚀 本地运行

**前置条件：** 已安装 Python 3.9+

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/ai-news-tracker.git
cd ai-news-tracker

# 2. 启动后端服务器（无需安装任何依赖）
python server.py

# 3. 打开浏览器访问
# http://localhost:8000
```

启动后服务器会自动抓取全部 RSS 源，命令窗口会显示每个来源的抓取结果。

---

## 📡 数据源配置

在 `server.py` 顶部的 `RSS_SOURCES` 字典中修改：

```python
RSS_SOURCES = {
    "siliconValley": [
        {"url": "https://openai.com/blog/rss.xml",        "source": "OpenAI"},
        {"url": "https://huggingface.co/blog/feed.xml",   "source": "Huggingface"},
        {"url": "https://blog.google/technology/ai/rss/", "source": "Google AI"},
        # 在此添加更多硅谷信源 ↑
    ],
    "domestic": [
        {"url": "https://decemberpei.cyou/rssbox/36kr/search/ai",        "source": "36氪 AI"},
        {"url": "https://decemberpei.cyou/rssbox/wechat-jiqizhixin.xml", "source": "机器之心"},
        {"url": "https://decemberpei.cyou/rssbox/wechat-liangziwei.xml", "source": "量子位"},
        # 在此添加更多国内信源 ↑
    ]
}
```

修改后重启 `python server.py` 生效。

---

## ☁️ 部署到 Railway（获取公开网址）

1. 注册 [Railway](https://railway.app)，用 GitHub 账号登录
2. 点击 `New Project` → `Deploy from GitHub repo`
3. 选择本仓库，Railway 自动读取 `Procfile` 完成部署
4. 进入服务 `Settings` → `Networking` → 点击 `Generate Domain`
5. 获得永久公开网址，可直接分享给任何人

---

## 🔌 API 接口

服务器提供两个简单的 API 端点：

| 接口 | 说明 |
|------|------|
| `GET /api/news` | 返回当前缓存的全部新闻数据（JSON） |
| `GET /api/refresh` | 触发后端立即重新抓取所有 RSS 源 |

---

## ⚙️ 配置说明

在 `server.py` 中可调整以下参数：

```python
CACHE_TTL = 30 * 60   # 自动刷新间隔，默认 30 分钟
# 每个 RSS 源最多抓取条数，在 fetch_rss() 函数中修改
for raw in raw_items[:10]:   # 默认每源取 10 条
```

---

## 📄 License

MIT License — 自由使用和修改。
