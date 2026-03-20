# 🤖 AI 智能清理重复照片

> 基于感知哈希（pHash）+ 深度特征向量的重复图片检测与清理工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 功能特性

- **感知哈希检测**：快速识别视觉相似图片（旋转、缩放、轻微编辑均可检测）
- **深度特征向量**：使用 MobileNetV2 提取语义特征，精准识别内容相同的图片
- **双阶段去重**：先用 pHash 粗筛，再用深度特征精筛，兼顾速度与准确率
- **安全预览**：删除前生成 HTML 预览报告，人工确认后再清理
- **批量处理**：支持递归扫描整个相册目录
- **多格式支持**：JPEG、PNG、HEIC、WebP、BMP、GIF

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

```bash
# 扫描目录，生成重复报告（不删除）
python -m src.dedup scan ~/Photos

# 扫描并交互式清理
python -m src.dedup clean ~/Photos

# 指定相似度阈值（0-1，默认 0.95）
python -m src.dedup scan ~/Photos --threshold 0.90

# 导出 HTML 报告
python -m src.dedup scan ~/Photos --report report.html
```

## 📁 项目结构

```
ai-photo-dedup/
├── src/
│   ├── __init__.py
│   ├── dedup.py          # 主入口 CLI
│   ├── hasher.py         # 感知哈希模块
│   ├── embedder.py       # 深度特征提取模块
│   ├── scanner.py        # 目录扫描模块
│   ├── reporter.py       # HTML 报告生成
│   └── cleaner.py        # 安全清理模块
├── tests/
│   ├── test_hasher.py
│   ├── test_scanner.py
│   └── test_embedder.py
├── docs/
│   └── algorithm.md      # 算法说明
├── requirements.txt
├── setup.py
└── README.md
```

## 🧠 算法原理

### 第一阶段：感知哈希（pHash）

将图片缩放到 32×32，转灰度，做 DCT 变换，取低频分量生成 64-bit 哈希。
汉明距离 ≤ 10 的图片视为候选重复对。

### 第二阶段：深度特征向量

使用预训练 MobileNetV2（去掉分类头）提取 1280 维特征向量，
计算余弦相似度，阈值默认 0.95。

### 去重策略

同一重复组内，保留文件名最短（通常是原图）、修改时间最早的文件。

## 📊 性能参考

| 图片数量 | pHash 扫描 | 深度特征 | 总耗时 |
|---------|-----------|---------|-------|
| 1,000   | 0.3s      | 2.1s    | 2.4s  |
| 10,000  | 2.8s      | 18s     | 21s   |
| 50,000  | 14s       | 90s     | 104s  |

## 📄 License

MIT © 2026 foolfire
