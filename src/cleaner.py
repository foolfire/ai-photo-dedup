"""
安全清理模块
提供预览模式、确认交互、回收站移动等功能
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import shutil
import os


def select_keep_remove(group: List[Path]) -> Tuple[Path, List[Path]]:
    """
    从重复组中选择保留和删除的图片
    策略：保留文件名最短、修改时间最早的
    """
    # 按文件名长度排序，然后按修改时间
    sorted_files = sorted(group, key=lambda p: (len(str(p)), p.stat().st_mtime))
    keep = sorted_files[0]
    remove = sorted_files[1:]
    return keep, remove


def preview_duplicates(duplicate_groups: List[List[Path]]) -> Dict:
    """生成清理预览信息"""
    preview = {
        "total_groups": len(duplicate_groups),
        "total_duplicates": sum(len(g) - 1 for g in duplicate_groups),
        "total_size": 0,
        "actions": [],
    }

    for group in duplicate_groups:
        keep, remove = select_keep_remove(group)
        group_info = {
            "keep": keep,
            "remove": remove,
            "remove_size": sum(p.stat().st_size for p in remove if p.exists()),
        }
        preview["actions"].append(group_info)
        preview["total_size"] += group_info["remove_size"]

    return preview


def move_to_trash(file_path: Path, trash_dir: Path | None = None) -> bool:
    """
    将文件移动到回收站（或指定目录）
    macOS: 使用 ~/.Trash
    Linux: 使用 ~/.local/share/Trash/files
    """
    if trash_dir is None:
        if os.uname().sysname == "Darwin":
            trash_dir = Path.home() / ".Trash"
        else:
            trash_dir = Path.home() / ".local/share/Trash/files"

    trash_dir.mkdir(parents=True, exist_ok=True)

    try:
        dest = trash_dir / file_path.name
        # 处理重名
        counter = 1
        stem = dest.stem
        suffix = dest.suffix
        while dest.exists():
            dest = trash_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(file_path), str(dest))
        return True
    except Exception as e:
        print(f"[ERROR] 移动失败 {file_path}: {e}")
        return False


def execute_cleanup(actions: List[Dict], dry_run: bool = True) -> Dict:
    """
    执行清理操作
    dry_run: True 仅预览，False 实际移动
    """
    results = {
        "moved": [],
        "failed": [],
        "saved_bytes": 0,
    }

    for action in actions:
        for remove_path in action["remove"]:
            if dry_run:
                print(f"[DRY-RUN] 将删除: {remove_path}")
                results["moved"].append(remove_path)
                results["saved_bytes"] += action["remove_size"]
            else:
                if move_to_trash(remove_path):
                    print(f"[MOVED] {remove_path} → Trash")
                    results["moved"].append(remove_path)
                    results["saved_bytes"] += action["remove_size"]
                else:
                    results["failed"].append(remove_path)

    return results
