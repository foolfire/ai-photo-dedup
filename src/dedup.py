"""
AI 智能去重 — CLI 主入口
用法:
    python -m src.dedup scan <目录> [--threshold 0.95]
    python -m src.dedup clean <目录> [--dry-run]
    python -m src.dedup report <目录> [--output report.html]
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import List
import click
from tqdm import tqdm

from .scanner import scan_directory
from .hasher import compute_phash, find_hash_duplicates
from .embedder import ImageEmbedder, find_embedding_duplicates
from .reporter import generate_report
from .cleaner import preview_duplicates, select_keep_remove, execute_cleanup


@click.group()
def cli():
    """🤖 AI 智能清理重复照片"""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--threshold", "-t", default=0.95, help="深度特征相似度阈值 (0-1)")
@click.option("--hash-threshold", "-ht", default=10, help="pHash 汉明距离阈值")
@click.option("--report", "-r", default=None, help="输出 HTML 报告文件路径")
def scan(directory: str, threshold: float, hash_threshold: int, report: str | None):
    """扫描目录，找出重复图片"""
    scan_path = Path(directory)
    click.echo(f"🔍 扫描目录: {scan_path}")

    # 第一步：扫描图片
    images = scan_directory(scan_path)
    click.echo(f"📷 找到 {len(images)} 张图片")

    if len(images) < 2:
        click.echo("⚠️ 图片不足 2 张，无法检测重复")
        return

    # 第二步：pHash 粗筛
    click.echo("🧠 计算感知哈希...")
    hashes = {}
    for img_path in tqdm(images, desc="pHash"):
        h = compute_phash(img_path)
        if h:
            hashes[img_path] = h

    phash_groups = find_hash_duplicates(hashes, threshold=hash_threshold)
    click.echo(f"📊 pHash 阶段: 发现 {len(phash_groups)} 组候选重复")

    if not phash_groups:
        click.echo("✅ 未发现重复图片")
        return

    # 第三步：深度特征精筛
    click.echo("🧠 深度特征提取...")
    all_candidates = [p for g in phash_groups for p in g]
    embedder = ImageEmbedder()
    embeddings = {}

    batch_size = 32
    for i in tqdm(range(0, len(all_candidates), batch_size), desc="Embedding"):
        batch = all_candidates[i:i+batch_size]
        embeddings.update(embedder.embed_batch(batch))

    final_groups = find_embedding_duplicates(embeddings, threshold=threshold)
    click.echo(f"🎯 最终: 发现 {len(final_groups)} 组重复")

    # 输出报告
    if report:
        html = generate_report(final_groups, str(scan_path), threshold)
        Path(report).write_text(html)
        click.echo(f"📄 报告已生成: {report}")

    # 预览
    preview = preview_duplicates(final_groups)
    click.echo(f"\n📈 统计:")
    click.echo(f"   - 重复组: {preview['total_groups']}")
    click.echo(f"   - 可清理: {preview['total_duplicates']} 张")
    click.echo(f"   - 可节省: {_format_size(preview['total_size'])}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--threshold", "-t", default=0.95, help="相似度阈值")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际删除")
def clean(directory: str, threshold: float, dry_run: bool):
    """交互式清理重复图片"""
    scan_path = Path(directory)
    click.echo(f"🧹 清理模式: {scan_path}")

    images = scan_directory(scan_path)
    click.echo(f"📷 扫描 {len(images)} 张图片...")

    # 简化版：直接用 pHash（skip embedder for speed in clean mode）
    hashes = {}
    for img_path in tqdm(images, desc="Hashing"):
        h = compute_phash(img_path)
        if h:
            hashes[img_path] = h

    groups = find_hash_duplicates(hashes, threshold=10)
    click.echo(f"📊 发现 {len(groups)} 组重复")

    # 生成清理动作
    actions = []
    for group in groups:
        keep, remove = select_keep_remove(group)
        actions.append({"keep": keep, "remove": remove, "remove_size": sum(p.stat().st_size for p in remove)})

    if not actions:
        click.echo("✅ 无需清理")
        return

    preview = preview_duplicates(groups)
    click.echo(f"\n📈 将清理 {preview['total_duplicates']} 张图片，节省 {_format_size(preview['total_size'])}")

    if dry_run:
        click.echo("\n🔍 预览模式（使用 --clean 实际执行删除）")
    else:
        click.confirm("\n⚠️ 确认执行清理？", abort=True)
        results = execute_cleanup(actions, dry_run=False)
        click.echo(f"✅ 已移动 {len(results['moved'])} 个文件到回收站")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--output", "-o", default="dedup-report.html", help="输出文件")
@click.option("--threshold", "-t", default=0.95)
def report(directory: str, output: str, threshold: float):
    """生成 HTML 去重报告"""
    scan_path = Path(directory)
    images = scan_directory(scan_path)

    hashes = {}
    for img_path in tqdm(images, desc="Hashing"):
        h = compute_phash(img_path)
        if h:
            hashes[img_path] = h

    groups = find_hash_duplicates(hashes, threshold=10)
    html = generate_report(groups, str(scan_path), threshold)
    Path(output).write_text(html)
    click.echo(f"📄 报告已保存: {output}")


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


if __name__ == "__main__":
    cli()
