"""
感知哈希模块
使用 pHash 算法快速计算图片指纹，支持汉明距离比较
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import imagehash
from PIL import Image


SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic"}


def compute_phash(image_path: Path, hash_size: int = 16) -> imagehash.ImageHash | None:
    """计算单张图片的感知哈希值"""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            return imagehash.phash(img, hash_size=hash_size)
    except Exception as e:
        print(f"[WARN] 无法处理 {image_path}: {e}")
        return None


def find_hash_duplicates(
    hashes: Dict[Path, imagehash.ImageHash],
    threshold: int = 10,
) -> List[List[Path]]:
    """
    在哈希字典中找出所有重复组
    threshold: 汉明距离阈值，越小越严格（0=完全相同）
    返回: 重复组列表，每组包含 ≥2 张图片路径
    """
    paths = list(hashes.keys())
    visited = set()
    groups: List[List[Path]] = []

    for i, p1 in enumerate(paths):
        if p1 in visited:
            continue
        group = [p1]
        for j in range(i + 1, len(paths)):
            p2 = paths[j]
            if p2 in visited:
                continue
            dist = hashes[p1] - hashes[p2]
            if dist <= threshold:
                group.append(p2)
                visited.add(p2)
        if len(group) > 1:
            visited.add(p1)
            groups.append(group)

    return groups
