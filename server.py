#!/usr/bin/env python3
"""
AI 动态追踪 - 后端服务器
运行方式: python server.py
访问地址: http://localhost:8000
"""

import json
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import os

# ============================================================
# RSS 源配置
# ============================================================
RSS_SOURCES = {
    "siliconValley": [
        {"url": "https://openai.com/blog/rss.xml",           "source": "OpenAI"},
        {"url": "https://api.xgo.ing/rss/user/fc16750ce50741f1b1f05ea1fb29436f",      "source": "Huggingface"},
        {"url": "https://blog.google/technology/ai/rss/",    "source": "Google AI"},
        {"url": "https://api.xgo.ing/rss/user/a4bfe44bfc0d4c949da21ebd3f5f42a5",    "source": "Fei-Fei Li"},
        {"url": "https://api.xgo.ing/rss/user/ef7c70f9568d45f4915169fef4ce90b4",    "source": "MetaAI"},
        {"url": "https://api.xgo.ing/rss/user/05f1492e43514dc3862a076d3697c390",    "source": "NVIDIA"},
    ],
    "domestic": [
        {"url": "https://api.xgo.ing/rss/user/80032d016d654eb4afe741ff34b7643d",       "source": "Qwen"},
        {"url": "https://api.xgo.ing/rss/user/6e8e7b42cb434818810f87bcf77d86fb",       "source": "Hunyuan"},
        {"url": "https://api.xgo.ing/rss/user/68b610deb24b47ae9a236811563cda86",       "source": "DeepSeek"},
        {"url": "https://api.xgo.ing/rss/user/6d7d398dd80b48d79669c92745d32cf6",       "source": "Skywork"},
        {"url": "https://decemberpei.cyou/rssbox/wechat-jiqizhixin.xml", "source": "机器之心"},
        {"url": "https://decemberpei.cyou/rssbox/wechat-liangziwei.xml", "source": "量子位"},
    ]
}

# 缓存：每2小时自动刷新一次
CACHE = {"data": None, "updated_at": 0}
CACHE_TTL = 120 * 60  # 120 分钟（秒）

# ============================================================
# RSS 抓取 & 解析
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def clean_html(text):
    """去除 HTML 标签和多余空白"""
    text = re.sub(r'<[^>]+>', '', text or '')
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return ' '.join(text.split())[:300]

def parse_date(date_str):
    """解析 RSS 时间字符串，返回 ISO 格式"""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()

def extract_tags(text):
    """从标题中提取关键标签"""
    keywords = ['AI', 'GPT', 'Claude', 'Gemini', 'LLM', '大模型', '开源',
                '发布', '更新', '上线', '功能', '突破', 'Agent', 'Sora']
    found = [k for k in keywords if k.lower() in text.lower()]
    return found[:3]

def calc_importance(title):
    """判断重要性"""
    high_kw = ['发布', '推出', '上线', '突破', '重磅', 'launch', 'release',
               'announce', 'introduce', 'new', '新']
    return 'high' if any(k.lower() in title.lower() for k in high_kw) else 'medium'

def fetch_rss(url, source_name, timeout=15):
    """抓取单个 RSS 源，返回文章列表"""
    items = []
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            xml_bytes = resp.read()
        
        root = ET.fromstring(xml_bytes)
        
        # 兼容 RSS 2.0 和 Atom
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        # 尝试 RSS <item>
        rss_items = root.findall('.//item')
        
        # 尝试 Atom <entry>
        atom_items = root.findall('.//atom:entry', ns) or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        raw_items = rss_items if rss_items else atom_items
        
        for raw in raw_items[:10]:  # 每源最多取 10 条
            def get(tag, attr=None):
                # 普通标签
                el = raw.find(tag)
                if el is None:
                    # 尝试加 atom 命名空间
                    el = raw.find(f'{{http://www.w3.org/2005/Atom}}{tag}')
                if el is None:
                    return ''
                if attr:
                    return el.get(attr, '')
                return (el.text or '').strip()
            
            title = get('title') or '无标题'
            desc  = clean_html(get('description') or get('summary') or get('content'))
            link  = get('link') or get('link', 'href') or '#'
            pub   = get('pubDate') or get('published') or get('updated') or ''
            
            if not title.strip() or not desc.strip():
                continue
            
            items.append({
                "id":         f"{source_name}-{hash(link)}",
                "title":      title[:120],
                "company":    source_name,
                "description": desc,
                "tags":       extract_tags(title),
                "credibility": "first-hand",
                "importance": calc_importance(title),
                "time":       parse_date(pub),
                "link":       link,
            })
        
        print(f"  ✅ {source_name}: {len(items)} 条")
    except (URLError, HTTPError) as e:
        print(f"  ❌ {source_name}: 网络错误 {e}")
    except ET.ParseError as e:
        print(f"  ❌ {source_name}: XML 解析失败 {e}")
    except Exception as e:
        print(f"  ❌ {source_name}: 未知错误 {e}")
    
    return items

def fetch_all():
    """抓取全部 RSS 源，返回整合数据"""
    print(f"\n🔄 开始抓取 RSS... [{datetime.now().strftime('%H:%M:%S')}]")
    result = {"siliconValley": [], "domestic": [], "updatedAt": datetime.now().isoformat()}
    
    for item in RSS_SOURCES["siliconValley"]:
        result["siliconValley"].extend(fetch_rss(item["url"], item["source"]))
    
    for item in RSS_SOURCES["domestic"]:
        result["domestic"].extend(fetch_rss(item["url"], item["source"]))
    
    sv  = len(result["siliconValley"])
    dom = len(result["domestic"])
    print(f"📊 完成: 硅谷 {sv} 条 / 国内 {dom} 条\n")
    return result

def get_cached_data():
    """返回缓存数据；如果过期则重新抓取"""
    now = time.time()
    if CACHE["data"] is None or (now - CACHE["updated_at"]) > CACHE_TTL:
        CACHE["data"] = fetch_all()
        CACHE["updated_at"] = now
    return CACHE["data"]

# 后台定时刷新线程
def auto_refresh():
    while True:
        time.sleep(CACHE_TTL)
        print("⏰ 定时自动刷新触发")
        CACHE["data"] = fetch_all()
        CACHE["updated_at"] = time.time()

# ============================================================
# HTTP 请求处理
# ============================================================
class Handler(SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # 过滤掉静态文件的日志，只保留 API 日志
        if '/api/' in (args[0] if args else ''):
            print(f"  [{self.address_string()}] {args[0]} {args[1]}")
    
    def do_GET(self):
        # API: 获取新闻数据
        if self.path == '/api/news':
            self.send_json(get_cached_data())
        
        # API: 强制刷新
        elif self.path == '/api/refresh':
            print("🔁 手动刷新触发")
            CACHE["data"] = fetch_all()
            CACHE["updated_at"] = time.time()
            self.send_json({"ok": True, "updatedAt": CACHE["data"]["updatedAt"]})
        
        # 静态文件（index.html）
        else:
            super().do_GET()
    
    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    import os
    PORT = int(os.environ.get('PORT', 8000))
    
    # 确保在 server.py 所在目录运行，index.html 必须与 server.py 同目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 启动时先抓一次数据
    CACHE["data"] = fetch_all()
    CACHE["updated_at"] = time.time()
    
    # 启动后台定时刷新线程
    t = threading.Thread(target=auto_refresh, daemon=True)
    t.start()
    
    print(f"🚀 服务器已启动: http://localhost:{PORT}")
    print(f"📰 在浏览器打开 http://localhost:{PORT} 查看网站")
    print(f"🔄 每 {CACHE_TTL // 60} 分钟自动刷新一次数据")
    print("按 Ctrl+C 停止服务器\n")
    
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
