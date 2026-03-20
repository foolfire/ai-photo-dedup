"""
测试文件: scanner 模块
"""
import pytest
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner import scan_directory


def test_scan_directory():
    """测试目录扫描"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # 创建测试文件
        (tmp / "1.jpg").touch()
        (tmp / "2.png").touch()
        (tmp / "3.txt").touch()  # 不支持的格式

        images = scan_directory(tmp, recursive=False)
        assert len(images) == 2
        assert all(p.suffix.lower() in {".jpg", ".png"} for p in images)
