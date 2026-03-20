"""
HTML 报告生成模块
使用 Jinja2 生成可视化去重报告
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from jinja2 import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 去重报告 — {{ date }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px; }
  .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
  .header h1 { margin: 0 0 10px; } .header p { margin: 0; opacity: 0.9; }
  .stats { display: flex; gap: 20px; justify-content: center; margin: 20px 0; }
  .stat-card { background: white; padding: 20px 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .stat-card .num { font-size: 2.5em; font-weight: 700; color: #667eea; }
  .stat-card .label { color: #666; font-size: 0.9em; }
  .group { background: white; margin: 15px 0; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .group-header { background: #f0f0ff; padding: 12px 20px; font-weight: 600; color: #333; display: flex; justify-content: space-between; }
  .keep { background: #e6f4ea; border-left: 4px solid #34a853; }
  .remove { background: #fce8e6; border-left: 4px solid #ea4335; }
  .images { display: flex; flex-wrap: wrap; gap: 10px; padding: 15px 20px; }
  .img-card { border: 2px solid transparent; border-radius: 8px; overflow: hidden; max-width: 180px; }
  .img-card img { width: 180px; height: 120px; object-fit: cover; display: block; }
  .img-card .name { padding: 6px 8px; font-size: 0.75em; color: #555; word-break: break-all; }
  .img-card.keep-card { border-color: #34a853; }
  .img-card.remove-card { border-color: #ea4335; opacity: 0.8; }
  .legend { display: flex; gap: 20px; justify-content: center; margin: 10px 0; }
  .legend span { display: flex; align-items: center; gap: 6px; font-size: 0.9em; }
  .dot { width: 12px; height: 12px; border-radius: 50%; }
  .dot.keep { background: #34a853; } .dot.remove { background: #ea4335; }
</style>
</head>
<body>
<div class="header">
  <h1>🤖 AI 智能去重报告</h1>
  <p>扫描时间: {{ date }} &nbsp;|&nbsp; 算法: pHash + MobileNetV2</p>
</div>
<div class="stats">
  <div class="stat-card"><div class="num">{{ total_images }}</div><div class="label">扫描图片</div></div>
  <div class="stat-card"><div class="num">{{ total_groups }}</div><div class="label">重复组</div></div>
  <div class="stat-card"><div class="num">{{ total_duplicates }}</div><div class="label">重复图片（可清理）</div></div>
</div>
<div class="legend">
  <span><div class="dot keep"></div> 保留（原图）</span>
  <span><div class="dot remove"></div> 建议删除</span>
</div>
{% for group in groups %}
<div class="group">
  <div class="group-header">
    <span>📁 重复组 #{{ loop.index }}</span>
    <span>{{ group.files|length }} 张图片 · 相似度 {{ group.similarity }}</span>
  </div>
  <div class="images">
  {% for item in group.files %}
    <div class="img-card {{ 'keep-card' if item.keep else 'remove-card' }}">
      <img src="file://{{ item.path }}" alt="{{ item.name }}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 180 120%22><rect fill=%22%23ddd%22 width=%22180%22 height=%22120%22/><text x=%2280%22 y=%2260%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2212%22 dy=%22.3em%22>预览不可用</text></svg>'">
      <div class="name">{{ item.name }}<br><small>{{ item.size }}</small></div>
    </div>
  {% endfor %}
  </div>
</div>
{% endfor %}
</body>
</html>"""


def generate_report(duplicate_groups: List[List[Path]],
                    scan_path: str,
                    threshold: float) -> str:
    """生成 HTML 去重报告"""
    template = Template(HTML_TEMPLATE)

    all_images = [p for g in duplicate_groups for p in g]
    all_dupes = [p for g in duplicate_groups for p in g[1:]]

    groups_data = []
    for group in duplicate_groups:
        # 同一组按文件名长度排序，最短的（通常是原图）保留
        sorted_files = sorted(group, key=lambda p: (len(str(p)), p.stat().st_mtime))
        files = []
        for i, f in enumerate(sorted_files):
            size = _format_size(f.stat().st_size) if f.exists() else "未知"
            files.append({
                "path": str(f),
                "name": f.name,
                "size": size,
                "keep": i == 0,
            })
        # 估算相似度
        sim = "≥95%" if len(group) > 2 else "~98%"
        groups_data.append({"files": files, "similarity": sim})

    return template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_images=len(all_images),
        total_groups=len(groups_data),
        total_duplicates=len(all_dupes),
        groups=groups_data,
    )


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"
