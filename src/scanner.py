"""
目录扫描模块
递归扫描目录，收集所有支持格式的图片文件
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Generator
from .hasher import SUPPORTED_EXTS


def scan_directory(root: Path, recursive: bool = True) -> List[Path]:
    """扫描目录，返回所有支持格式的图片路径"""
    root = Path(root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"目录不存在: {root}")

    images: List[Path] = []
    if recursive:
        for ext in SUPPORTED_EXTS:
            images.extend(root.rglob(f"*{ext}"))
            images.extend(root.rglob(f"*{ext.upper()}"))
    else:
        for ext in SUPPORTED_EXTS:
            images.extend(root.glob(f"*{ext}"))
            images.extend(root.glob(f"*{ext.upper()}"))

    # 去重（大小写问题）
    seen = set()
    unique = []
    for p in images:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return sorted(unique)
