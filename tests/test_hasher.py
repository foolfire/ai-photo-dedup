"""
测试文件: hasher 模块
"""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hasher import compute_phash, find_hash_duplicates


def test_phash_computation():
    """测试 pHash 计算"""
    # 使用临时测试图片
    # 实际测试需要真实图片
    pass


def test_duplicate_detection():
    """测试重复检测逻辑"""
    # 创建模拟哈希
    from PIL import Image
    import tempfile
    import imagehash

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试图片
        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="red")
        img3 = Image.new("RGB", (100, 100), color="blue")

        p1 = Path(tmpdir) / "1.jpg"
        p2 = Path(tmpdir) / "2.jpg"
        p3 = Path(tmpdir) / "3.jpg"

        img1.save(p1)
        img2.save(p2)
        img3.save(p3)

        h1 = compute_phash(p1)
        h2 = compute_phash(p2)
        h3 = compute_phash(p3)

        assert h1 is not None
        assert h1 - h2 == 0  # 完全相同
        assert h1 - h3 > 10  # 不同颜色
